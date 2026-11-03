import csv
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

log = logging.getLogger("data_manager")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_PATH = os.path.join(BASE_DIR, "food_inventory.csv")
RECIPES_PATH = os.path.join(BASE_DIR, "recipe_results.csv")

INVENTORY_COLUMNS = [
    "food", "food_category", "use-by", "storage condition", "days_to_expiry",
    "waste_risk_level", "allergen info", "demand level", "quantity",
]
RECIPE_COLUMNS = ["name", "ingredients", "instructions"]

INVENTORY_INT_FIELDS = ("days_to_expiry", "quantity")
DATE_FORMAT = "%d/%m/%Y"

# Keyword names used by InventoryTable.add / update -> CSV column.
INVENTORY_ARGS = {
    "food": "food",
    "food_category": "food_category",
    "use_by": "use-by",
    "storage_condition": "storage condition",
    "days_to_expiry": "days_to_expiry",
    "waste_risk_level": "waste_risk_level",
    "allergen_info": "allergen info",
    "demand_level": "demand level",
    "quantity": "quantity",
}


# --------------------------------------------------------------------------- #
# Base class: one CSV file held in memory
# --------------------------------------------------------------------------- #
class CsvTable:
    # A CSV file loaded into memory as a list of dict records (self.records).
    #
    # This base class handles what every table needs: reading the file (and
    # repairing it if it is missing or corrupt), saving it atomically, and the
    # add / replace / delete bookkeeping. Every change is saved straight away and
    # is undone in memory if the save fails, so memory and disk never disagree.
    # Subclasses set COLUMNS and add their own fields and searches.

    COLUMNS: list = []

    def __init__(self, path: str):
        self.path = path
        self.records: list = []

    # ---- file helpers ----------------------------------------------------- #
    def _write(self, rows: list) -> None:
        # Write atomically so a crash mid-save can't corrupt the file.
        folder = os.path.dirname(self.path) or "."
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            os.replace(tmp, self.path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def _create_empty(self) -> None:
        # Create a header-only CSV. If that isn't possible, carry on in memory.
        try:
            self._write([])
        except OSError as exc:
            log.error("Could not create %s (%s). Continuing with in-memory data only.", self.path, exc)

    def _quarantine(self) -> Optional[str]:
        # Move a corrupt file aside (never delete it). Returns the new path, or None.
        backup = f"{self.path}.corrupt-{datetime.now().strftime('%d%m%Y-%H%M%S')}"
        n = 1
        while os.path.exists(backup):
            n += 1
            backup = f"{self.path}.corrupt-{datetime.now().strftime('%d%m%Y-%H%M%S')}-{n}"
        try:
            os.replace(self.path, backup)
            return backup
        except OSError as exc:
            log.error("Could not move corrupt file %s aside (%s).", self.path, exc)
            return None

    def _read(self) -> list:
        # Read the CSV into a list of dicts, repairing missing/corrupt files.
        #
        # Always returns a list (possibly empty); only raises for problems that
        # aren't about the file's contents, such as a permissions error on read.

        # Missing or zero-byte file -> create a header-only CSV.
        if not os.path.exists(self.path) or os.path.getsize(self.path) == 0:
            log.warning("%s is missing or empty; creating a new one.", self.path)
            self._create_empty()
            return []

        try:
            with open(self.path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, strict=True)
                header = reader.fieldnames or []
                absent = [c for c in self.COLUMNS if c not in header]
                if absent:
                    raise ValueError(f"required column(s) missing: {', '.join(absent)}")
                rows = []
                for row in reader:
                    clean = {c: (row.get(c) or "").strip() for c in self.COLUMNS}
                    if any(clean.values()):  # skip blank rows
                        rows.append(clean)
                return rows
        except (UnicodeDecodeError, csv.Error, ValueError) as exc:
            # UnicodeDecodeError is a ValueError subclass; listed for clarity.
            backup = self._quarantine()
            log.error("%s is corrupt (%s). %s Starting with an empty file.",
                      self.path, exc, f"Original saved as {backup}." if backup else "Original left in place.")
            self._create_empty()
            return []

    # ---- load / save ------------------------------------------------------ #
    def _clean(self, rows: list) -> list:
        # Hook: subclasses tidy freshly read rows here (default: leave as is).
        return rows

    def _rows_for_saving(self) -> list:
        # Hook: subclasses adjust records just before writing (default: as is).
        return self.records

    def load(self) -> None:
        # (Re)load the file from disk. self.records is replaced in place, so any
        # outside reference to the list stays valid.
        self.records[:] = self._clean(self._read())

    def save(self) -> None:
        self._write(self._rows_for_saving())

    # ---- change bookkeeping (saved immediately, undone if saving fails) ---- #
    def _check_index(self, index: int) -> None:
        # Raise IndexError unless `index` is a valid position in the table.
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(self.records):
            raise IndexError(f"No record at index {index!r}; there are {len(self.records)} record(s).")

    def _append_and_save(self, record: dict) -> dict:
        # Add a record and save. If saving fails (e.g. file locked or disk
        # full) the record is removed again so memory and disk stay in sync.
        self.records.append(record)
        try:
            self.save()
        except Exception as exc:
            self.records.pop()
            log.error("Could not save record, nothing was added: %s", exc)
            raise
        return record

    def _replace_and_save(self, index: int, record: dict) -> dict:
        # Swap in an updated record and save; restore the old one if saving fails.
        old = self.records[index]
        self.records[index] = record
        try:
            self.save()
        except Exception as exc:
            self.records[index] = old
            log.error("Could not save changes, record left unchanged: %s", exc)
            raise
        return record

    def _delete_and_save(self, index: int) -> dict:
        # Remove a record and save; put it back if saving fails.
        old = self.records.pop(index)
        try:
            self.save()
        except Exception as exc:
            self.records.insert(index, old)
            log.error("Could not save, nothing was deleted: %s", exc)
            raise
        return old

    def delete(self, index: int) -> dict:
        # Remove the record at `index`, save, and return the removed record.
        self._check_index(index)
        return self._delete_and_save(index)

    # ---- matching helpers shared by the searches -------------------------- #
    @staticmethod
    def _contains(haystack: str, needle: Optional[str]) -> bool:
        # Case-insensitive substring match. needle=None means 'no filter'.
        return needle is None or needle.lower() in haystack.lower()

    @staticmethod
    def _equals(value: str, wanted: Optional[str]) -> bool:
        # Case-insensitive exact match. wanted=None means 'no filter'.
        return wanted is None or value.lower() == wanted.lower()

    @staticmethod
    def _as_list(value: Union[str, Iterable[str], None]) -> list:
        if value is None:
            return []
        return [value] if isinstance(value, str) else list(value)


# --------------------------------------------------------------------------- #
# food_inventory.csv
# --------------------------------------------------------------------------- #
class InventoryTable(CsvTable):
    COLUMNS = INVENTORY_COLUMNS
    INT_FIELDS = INVENTORY_INT_FIELDS
    ARGS = INVENTORY_ARGS

    @staticmethod
    def _parse_date(value: str) -> Optional[datetime]:
        try:
            return datetime.strptime(value, DATE_FORMAT)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _to_date(value: Union[str, datetime, None]) -> Optional[datetime]:
        if value is None or isinstance(value, datetime):
            return value
        for fmt in (DATE_FORMAT, "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unrecognised date '{value}'. Use DD-MM-YYYY.")

    def _clean(self, rows: list) -> list:
        # Numeric columns become ints; anything that isn't a whole number becomes None.
        for row in rows:
            for field in self.INT_FIELDS:
                try:
                    row[field] = int(row[field])
                except (ValueError, TypeError):
                    log.warning("%s: %r is not a whole number for %r; treating as missing.",
                                self.path, row[field], row["food"] or "(unnamed row)")
                    row[field] = None
        return rows

    def _rows_for_saving(self) -> list:
        return [{c: ("" if r[c] is None else r[c]) for c in self.COLUMNS} for r in self.records]

    def add(
        self,
        food: str,
        food_category: str,
        use_by: str,
        storage_condition: str,
        days_to_expiry: int,
        waste_risk_level: str,
        allergen_info: str = "",
        demand_level: str = "",
        quantity: int = 0,
    ) -> dict:
        # Append an inventory record and write it to food_inventory.csv.
        #
        # `use_by` should be D/M/YYYY to stay consistent with existing rows.

        if not food.strip():
            raise ValueError("food is required")
        record = {
            "food": food.strip(),
            "food_category": food_category.strip(),
            "use-by": use_by.strip(),
            "storage condition": storage_condition.strip(),
            "days_to_expiry": int(days_to_expiry),
            "waste_risk_level": waste_risk_level.strip(),
            "allergen info": allergen_info.strip(),
            "demand level": demand_level.strip(),
            "quantity": int(quantity),
        }
        return self._append_and_save(record)

    def update(self, index: int, **changes) -> dict:
        # Change fields of the inventory record at `index` and save.
        #
        # Only the fields you pass are changed. Use the same names as add():
        # food, food_category, use_by, storage_condition, days_to_expiry,
        # waste_risk_level, allergen_info, demand_level, quantity.
        # Returns the updated record.

        self._check_index(index)
        unknown = [k for k in changes if k not in self.ARGS]
        if unknown:
            raise ValueError(f"Unknown inventory field(s): {', '.join(unknown)}")
        record = dict(self.records[index])
        for key, value in changes.items():
            column = self.ARGS[key]
            if column in self.INT_FIELDS:
                record[column] = int(value)
            else:
                record[column] = "" if value is None else str(value).strip()
        if not record["food"]:
            raise ValueError("food is required")
        return self._replace_and_save(index, record)

    def search(
        self,
        food: Optional[str] = None,                 # substring
        food_category: Optional[str] = None,        # exact (case-insensitive)
        use_by_before: Union[str, datetime, None] = None,  # inclusive
        use_by_after: Union[str, datetime, None] = None,   # inclusive
        storage_condition: Optional[str] = None,    # substring, e.g. "chilled"
        min_days_to_expiry: Optional[int] = None,
        max_days_to_expiry: Optional[int] = None,
        waste_risk_level: Optional[str] = None,     # exact, e.g. "High"
        allergen: Optional[str] = None,             # substring, e.g. "eggs"
        exclude_allergen: Optional[str] = None,     # drop rows containing this allergen
        allergen_free: bool = False,                # only rows with no allergen listed
        demand_level: Optional[str] = None,         # exact
        min_quantity: Optional[int] = None,
        max_quantity: Optional[int] = None,
        item_id: Optional[int] = None,              # the item's number in the list (position + 1)
    ) -> list:
        # Return inventory rows matching ALL supplied filters (unset = ignored).
        #
        # `item_id` is the number shown next to the item in the full inventory list
        # (1 = first row), so it changes if rows above it are added or removed.

        before, after = self._to_date(use_by_before), self._to_date(use_by_after)
        results = []
        for n, r in enumerate(self.records, start=1):
            if item_id is not None and n != item_id:
                continue
            if not self._contains(r["food"], food):
                continue
            if not self._equals(r["food_category"], food_category):
                continue
            if before or after:
                d = self._parse_date(r["use-by"])
                if d is None or (before and d > before) or (after and d < after):
                    continue
            if not self._contains(r["storage condition"], storage_condition):
                continue
            days, qty = r["days_to_expiry"], r["quantity"]
            if min_days_to_expiry is not None and (days is None or days < min_days_to_expiry):
                continue
            if max_days_to_expiry is not None and (days is None or days > max_days_to_expiry):
                continue
            if not self._equals(r["waste_risk_level"], waste_risk_level):
                continue
            if allergen is not None and not self._contains(r["allergen info"], allergen):
                continue
            if exclude_allergen is not None and self._contains(r["allergen info"], exclude_allergen):
                continue
            if allergen_free and r["allergen info"]:
                continue
            if not self._equals(r["demand level"], demand_level):
                continue
            if min_quantity is not None and (qty is None or qty < min_quantity):
                continue
            if max_quantity is not None and (qty is None or qty > max_quantity):
                continue
            results.append(r)
        return results


# --------------------------------------------------------------------------- #
# recipe_results.csv
# --------------------------------------------------------------------------- #
class RecipeTable(CsvTable):
    COLUMNS = RECIPE_COLUMNS

    @staticmethod
    def _split_items(text: str) -> list:
        return [p.strip().lower() for p in text.split(",") if p.strip()]

    @staticmethod
    def _join_ingredients(ingredients: Union[str, Iterable[str]]) -> str:
        if not isinstance(ingredients, str):
            ingredients = ", ".join(i.strip() for i in ingredients)
        return ingredients.strip()

    def add(self, name: str, ingredients: Union[str, Iterable[str]], instructions: str) -> dict:
        # Append a recipe and write it to recipe_results.csv.
        #
        # `ingredients` can be a comma-separated string or a list of strings.

        if not name.strip():
            raise ValueError("name is required")
        record = {"name": name.strip(), "ingredients": self._join_ingredients(ingredients), "instructions": instructions.strip()}
        return self._append_and_save(record)

    def update(
        self,
        index: int,
        name: Optional[str] = None,
        ingredients: Union[str, Iterable[str], None] = None,
        instructions: Optional[str] = None,
    ) -> dict:
        # Change fields of the recipe at `index` and save (omitted fields are kept).
        #
        # Returns the updated record.

        self._check_index(index)
        record = dict(self.records[index])
        if name is not None:
            record["name"] = name.strip()
        if ingredients is not None:
            record["ingredients"] = self._join_ingredients(ingredients)
        if instructions is not None:
            record["instructions"] = instructions.strip()
        if not record["name"]:
            raise ValueError("name is required")
        return self._replace_and_save(index, record)

    def search(
        self,
        name: Optional[str] = None,                              # substring
        ingredient: Union[str, Iterable[str], None] = None,      # recipe must contain ALL of these
        any_ingredient: Union[str, Iterable[str], None] = None,  # recipe must contain AT LEAST ONE
        exclude_ingredient: Union[str, Iterable[str], None] = None,
        instructions: Optional[str] = None,                      # substring
        item_id: Optional[int] = None,                           # the recipe's number in the list (position + 1)
    ) -> list:
        # Return recipes matching ALL supplied filters (unset = ignored).
        #
        # Ingredient terms match as substrings, so "tomato" finds "tomatoes".
        # `item_id` is the number shown next to the recipe in the full recipe list
        # (1 = first recipe), so it changes if recipes above it are added or removed.

        need_all = [i.lower() for i in self._as_list(ingredient)]
        need_any = [i.lower() for i in self._as_list(any_ingredient)]
        banned = [i.lower() for i in self._as_list(exclude_ingredient)]
        results = []
        for n, r in enumerate(self.records, start=1):
            if item_id is not None and n != item_id:
                continue
            if not self._contains(r["name"], name):
                continue
            if not self._contains(r["instructions"], instructions):
                continue
            items = self._split_items(r["ingredients"])
            has = lambda term: any(term in item for item in items)
            if need_all and not all(has(t) for t in need_all):
                continue
            if need_any and not any(has(t) for t in need_any):
                continue
            if banned and any(has(t) for t in banned):
                continue
            results.append(r)
        return results


# --------------------------------------------------------------------------- #
# The manager: owns both tables
# --------------------------------------------------------------------------- #
class DataManager:
    # Holds the inventory table and the recipe table, and loads both when created.
    #
    #     manager = DataManager()
    #     manager.inventory.search(waste_risk_level="High")
    #     manager.recipes.add("Fried Rice", "rice, egg", "Fry everything.")
    #     manager.inventory.records        # the list of inventory dicts

    def __init__(self, inventory_path: str = INVENTORY_PATH, recipes_path: str = RECIPES_PATH):
        self.inventory = InventoryTable(inventory_path)
        self.recipes = RecipeTable(recipes_path)
        self.load()

    def load(self, inventory_path: Optional[str] = None, recipes_path: Optional[str] = None) -> None:
        # (Re)load both CSVs from disk. Numeric columns become ints.
        #
        # Pass paths to switch to different files; they are remembered for saves.

        if inventory_path is not None:
            self.inventory.path = inventory_path
        if recipes_path is not None:
            self.recipes.path = recipes_path
        self.inventory.load()
        self.recipes.load()

    def save_all(self) -> None:
        self.inventory.save()
        self.recipes.save()


# --------------------------------------------------------------------------- #
# Created and writing files for accepted and rejected recipes
# --------------------------------------------------------------------------- #
class RecipeResultsStore:
    # Reads accepted_recipe.json / recipes.json and writes recipe_results.csv and
    # rejected.txt. By default everything lives next to this file.

    def __init__(self, folder: Optional[Union[str, Path]] = None):
        self.folder = Path(folder) if folder is not None else Path(__file__).resolve().parent

    def get_folder_path(self):
        return self.folder

    def load_json_files(self):
        folder = self.get_folder_path()
        expected_file = folder / "accepted_recipe.json"
        recipes_file = folder / "recipes.json"

        # Check for input files
        if not expected_file.exists():
            return {"error": f"Could not find {expected_file}"}

        if not recipes_file.exists():
            return {"error": f"Could not find {recipes_file}"}

        # Load JSON files
        with open(expected_file, "r", encoding="utf-8") as file:
            accepted_recipes = json.load(file)

        with open(recipes_file, "r", encoding="utf-8") as file:
            recipes_from_json = json.load(file)

        return {
            "accepted_recipes": accepted_recipes,
            "recipes_from_json": recipes_from_json,
        }

    def save_results(self, accept_list, reject_list):
        folder = self.get_folder_path()
        results_file = folder / "recipe_results.csv"
        rejected_file = folder / "rejected.txt"

        # Write accepted recipes to recipe_results.csv
        with open(results_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=["name", "ingredients", "instructions"]
            )
            writer.writeheader()
            writer.writerows(accept_list)

        # Write rejected recipes to rejected.txt
        with open(rejected_file, "w", encoding="utf-8") as file:
            for rejected in reject_list:
                file.write(
                    f"Rejected recipe: {rejected['name']} | Reason: {rejected['reason']}\n"
                )
            file.write(f"\nTotal rejected recipes: {len(reject_list)}\n")

        return results_file.name, rejected_file.name


# --------------------------------------------------------------------------- #
# Ready-made objects, plus module-level shortcuts
# --------------------------------------------------------------------------- #
# One DataManager is created (and the CSVs loaded) when this module is imported,
# i.e. at startup. The names below simply point at its methods, so code written
# for the old function-style module (io_manager.py: dm.inventory,
# dm.search_inventory(...), dm.add_inventory_item(...)) keeps working unchanged.
# New code can use the classes directly, and this block can be deleted once
# nothing calls the old names any more.
manager = DataManager()
results_store = RecipeResultsStore()

inventory = manager.inventory.records       # same list object, updated in place on reload
recipes = manager.recipes.records

load = manager.load
save_inventory = manager.inventory.save
save_recipes = manager.recipes.save
save_all = manager.save_all

add_inventory_item = manager.inventory.add
update_inventory_item = manager.inventory.update
delete_inventory_item = manager.inventory.delete
search_inventory = manager.inventory.search

add_recipe = manager.recipes.add
update_recipe = manager.recipes.update
delete_recipe = manager.recipes.delete
search_recipes = manager.recipes.search

get_folder_path = results_store.get_folder_path
load_json_files = results_store.load_json_files
save_results = results_store.save_results
