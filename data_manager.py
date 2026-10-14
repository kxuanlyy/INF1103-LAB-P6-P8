import csv
import logging
import os
import tempfile
import csv
import json
from pathlib import Path
from datetime import datetime
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

# Keyword names used by add_inventory_item / update_inventory_item -> CSV column.
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

# In-memory tables (filled by load()).
inventory: list = []
recipes: list = []


# --------------------------------------------------------------------------- #
# File helpers
# --------------------------------------------------------------------------- #
def _write_csv(path: str, columns: list, rows: list) -> None:
#    Write atomically so a crash mid-save can't corrupt the file.
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _create_empty(path: str, columns: list) -> None:
#    Create a header-only CSV. If that isn't possible, carry on in memory.
    try:
        _write_csv(path, columns, [])
    except OSError as exc:
        log.error("Could not create %s (%s). Continuing with in-memory data only.", path, exc)


def _quarantine(path: str) -> Optional[str]:
#    Move a corrupt file aside (never delete it). Returns the new path, or None.
    backup = f"{path}.corrupt-{datetime.now().strftime('%d%m%Y-%H%M%S')}"
    n = 1
    while os.path.exists(backup):
        n += 1
        backup = f"{path}.corrupt-{datetime.now().strftime('%d%m%Y-%H%M%S')}-{n}"
    try:
        os.replace(path, backup)
        return backup
    except OSError as exc:
        log.error("Could not move corrupt file %s aside (%s).", path, exc)
        return None


def _read_csv(path: str, columns: list) -> list:
#    Read a CSV into a list of dicts, repairing missing/corrupt files.

#    Always returns a list (possibly empty); only raises for problems that
#    aren't about the file's contents, such as a permissions error on read.

    # Missing or zero-byte file -> create a header-only CSV.
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        log.warning("%s is missing or empty; creating a new one.", path)
        _create_empty(path, columns)
        return []

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, strict=True)
            header = reader.fieldnames or []
            absent = [c for c in columns if c not in header]
            if absent:
                raise ValueError(f"required column(s) missing: {', '.join(absent)}")
            rows = []
            for row in reader:
                clean = {c: (row.get(c) or "").strip() for c in columns}
                if any(clean.values()):  # skip blank rows
                    rows.append(clean)
            return rows
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        # UnicodeDecodeError is a ValueError subclass; listed for clarity.
        backup = _quarantine(path)
        log.error("%s is corrupt (%s). %s Starting with an empty file.",
                  path, exc, f"Original saved as {backup}." if backup else "Original left in place.")
        _create_empty(path, columns)
        return []


# --------------------------------------------------------------------------- #
# Search helpers
# --------------------------------------------------------------------------- #
def _contains(haystack: str, needle: Optional[str]) -> bool:
#    Case-insensitive substring match. needle=None means 'no filter'.
    return needle is None or needle.lower() in haystack.lower()


def _equals(value: str, wanted: Optional[str]) -> bool:
#    Case-insensitive exact match. wanted=None means 'no filter'.
    return wanted is None or value.lower() == wanted.lower()


def _parse_date(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (ValueError, TypeError):
        return None


def _to_date(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None or isinstance(value, datetime):
        return value
    for fmt in (DATE_FORMAT, "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date '{value}'. Use DD-MM-YYYY.")


def _as_list(value: Union[str, Iterable[str], None]) -> list:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def _split_items(text: str) -> list:
    return [p.strip().lower() for p in text.split(",") if p.strip()]


# --------------------------------------------------------------------------- #
# Load / save
# --------------------------------------------------------------------------- #
def load(inventory_path: Optional[str] = None, recipes_path: Optional[str] = None) -> None:
#    (Re)load both CSVs from disk. Numeric columns become ints.

#   Pass paths to switch to different files; they are remembered for saves.

    global INVENTORY_PATH, RECIPES_PATH
    if inventory_path is not None:
        INVENTORY_PATH = inventory_path
    if recipes_path is not None:
        RECIPES_PATH = recipes_path

    new_inventory = _read_csv(INVENTORY_PATH, INVENTORY_COLUMNS)
    for row in new_inventory:
        for field in INVENTORY_INT_FIELDS:
            try:
                row[field] = int(row[field])
            except (ValueError, TypeError):
                log.warning("%s: %r is not a whole number for %r; treating as missing.",
                            INVENTORY_PATH, row[field], row["food"] or "(unnamed row)")
                row[field] = None
    inventory[:] = new_inventory  # in place, so outside references stay valid
    recipes[:] = _read_csv(RECIPES_PATH, RECIPE_COLUMNS)


def save_inventory() -> None:
    rows = [{c: ("" if r[c] is None else r[c]) for c in INVENTORY_COLUMNS} for r in inventory]
    _write_csv(INVENTORY_PATH, INVENTORY_COLUMNS, rows)


def save_recipes() -> None:
    _write_csv(RECIPES_PATH, RECIPE_COLUMNS, recipes)


def save_all() -> None:
    save_inventory()
    save_recipes()


def _append_and_save(table: list, record: dict, save) -> dict:
#    Add a record and save. If saving fails (e.g. file locked or disk
#    full) the record is removed again so memory and disk stay in sync.
    table.append(record)
    try:
        save()
    except Exception as exc:
        table.pop()
        log.error("Could not save record, nothing was added: %s", exc)
        raise
    return record


def _check_index(table: list, index: int) -> None:
#    Raise IndexError unless `index` is a valid position in `table`.
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(table):
        raise IndexError(f"No record at index {index!r}; there are {len(table)} record(s).")


def _replace_and_save(table: list, index: int, record: dict, save) -> dict:
#    Swap in an updated record and save; restore the old one if saving fails.
    old = table[index]
    table[index] = record
    try:
        save()
    except Exception as exc:
        table[index] = old
        log.error("Could not save changes, record left unchanged: %s", exc)
        raise
    return record


def _delete_and_save(table: list, index: int, save) -> dict:
#    Remove a record and save; put it back if saving fails.
    old = table.pop(index)
    try:
        save()
    except Exception as exc:
        table.insert(index, old)
        log.error("Could not save, nothing was deleted: %s", exc)
        raise
    return old


def _join_ingredients(ingredients: Union[str, Iterable[str]]) -> str:
    if not isinstance(ingredients, str):
        ingredients = ", ".join(i.strip() for i in ingredients)
    return ingredients.strip()


# --------------------------------------------------------------------------- #
# Add records (saved immediately)
# --------------------------------------------------------------------------- #
def add_inventory_item(
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
#    Append an inventory record and write it to food_inventory.csv.

#    `use_by` should be D/M/YYYY to stay consistent with existing rows.

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
    return _append_and_save(inventory, record, save_inventory)


def add_recipe(name: str, ingredients: Union[str, Iterable[str]], instructions: str) -> dict:
#    Append a recipe and write it to recipe_results.csv.

#    `ingredients` can be a comma-separated string or a list of strings.

    if not name.strip():
        raise ValueError("name is required")
    record = {"name": name.strip(), "ingredients": _join_ingredients(ingredients), "instructions": instructions.strip()}
    return _append_and_save(recipes, record, save_recipes)


# --------------------------------------------------------------------------- #
# Update / delete records (saved immediately)
# --------------------------------------------------------------------------- #
def update_inventory_item(index: int, **changes) -> dict:
#    Change fields of the inventory record at `index` and save.

#    Only the fields you pass are changed. Use the same names as
#    add_inventory_item: food, food_category, use_by, storage_condition,
#    days_to_expiry, waste_risk_level, allergen_info, demand_level, quantity.
#    Returns the updated record.

    _check_index(inventory, index)
    unknown = [k for k in changes if k not in INVENTORY_ARGS]
    if unknown:
        raise ValueError(f"Unknown inventory field(s): {', '.join(unknown)}")
    record = dict(inventory[index])
    for key, value in changes.items():
        column = INVENTORY_ARGS[key]
        if column in INVENTORY_INT_FIELDS:
            record[column] = int(value)
        else:
            record[column] = "" if value is None else str(value).strip()
    if not record["food"]:
        raise ValueError("food is required")
    return _replace_and_save(inventory, index, record, save_inventory)


def delete_inventory_item(index: int) -> dict:
#    Remove the inventory record at `index`, save, and return the removed record.
    _check_index(inventory, index)
    return _delete_and_save(inventory, index, save_inventory)


def update_recipe(
    index: int,
    name: Optional[str] = None,
    ingredients: Union[str, Iterable[str], None] = None,
    instructions: Optional[str] = None,
) -> dict:
#    Change fields of the recipe at `index` and save (omitted fields are kept).

#    Returns the updated record.

    _check_index(recipes, index)
    record = dict(recipes[index])
    if name is not None:
        record["name"] = name.strip()
    if ingredients is not None:
        record["ingredients"] = _join_ingredients(ingredients)
    if instructions is not None:
        record["instructions"] = instructions.strip()
    if not record["name"]:
        raise ValueError("name is required")
    return _replace_and_save(recipes, index, record, save_recipes)


def delete_recipe(index: int) -> dict:
#    Remove the recipe at `index`, save, and return the removed record.
    _check_index(recipes, index)
    return _delete_and_save(recipes, index, save_recipes)


# --------------------------------------------------------------------------- #
# Search / filter: food_inventory.csv
# --------------------------------------------------------------------------- #
def search_inventory(
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
#    Return inventory rows matching ALL supplied filters (unset = ignored).

#    `item_id` is the number shown next to the item in the full inventory list
#    (1 = first row), so it changes if rows above it are added or removed.

    before, after = _to_date(use_by_before), _to_date(use_by_after)
    results = []
    for n, r in enumerate(inventory, start=1):
        if item_id is not None and n != item_id:
            continue
        if not _contains(r["food"], food):
            continue
        if not _equals(r["food_category"], food_category):
            continue
        if before or after:
            d = _parse_date(r["use-by"])
            if d is None or (before and d > before) or (after and d < after):
                continue
        if not _contains(r["storage condition"], storage_condition):
            continue
        days, qty = r["days_to_expiry"], r["quantity"]
        if min_days_to_expiry is not None and (days is None or days < min_days_to_expiry):
            continue
        if max_days_to_expiry is not None and (days is None or days > max_days_to_expiry):
            continue
        if not _equals(r["waste_risk_level"], waste_risk_level):
            continue
        if allergen is not None and not _contains(r["allergen info"], allergen):
            continue
        if exclude_allergen is not None and _contains(r["allergen info"], exclude_allergen):
            continue
        if allergen_free and r["allergen info"]:
            continue
        if not _equals(r["demand level"], demand_level):
            continue
        if min_quantity is not None and (qty is None or qty < min_quantity):
            continue
        if max_quantity is not None and (qty is None or qty > max_quantity):
            continue
        results.append(r)
    return results


# --------------------------------------------------------------------------- #
# Search / filter: recipe_results.csv
# --------------------------------------------------------------------------- #
def search_recipes(
    name: Optional[str] = None,                              # substring
    ingredient: Union[str, Iterable[str], None] = None,      # recipe must contain ALL of these
    any_ingredient: Union[str, Iterable[str], None] = None,  # recipe must contain AT LEAST ONE
    exclude_ingredient: Union[str, Iterable[str], None] = None,
    instructions: Optional[str] = None,                      # substring
    item_id: Optional[int] = None,                           # the recipe's number in the list (position + 1)
) -> list:
#    Return recipes matching ALL supplied filters (unset = ignored).

#    Ingredient terms match as substrings, so "tomato" finds "tomatoes".
#    `item_id` is the number shown next to the recipe in the full recipe list
#    (1 = first recipe), so it changes if recipes above it are added or removed.

    need_all = [i.lower() for i in _as_list(ingredient)]
    need_any = [i.lower() for i in _as_list(any_ingredient)]
    banned = [i.lower() for i in _as_list(exclude_ingredient)]
    results = []
    for n, r in enumerate(recipes, start=1):
        if item_id is not None and n != item_id:
            continue
        if not _contains(r["name"], name):
            continue
        if not _contains(r["instructions"], instructions):
            continue
        items = _split_items(r["ingredients"])
        has = lambda term: any(term in item for item in items)
        if need_all and not all(has(t) for t in need_all):
            continue
        if need_any and not any(has(t) for t in need_any):
            continue
        if banned and any(has(t) for t in banned):
            continue
        results.append(r)
    return results


# Loaded once, on import (i.e. at startup).
load()


#--------------------------------------------------------------------------- #
# Created and writing files for accepted and rejected recipes
# --------------------------------------------------------------------------- #
def get_folder_path():
    return Path(__file__).resolve().parent


def load_json_files():
    folder = get_folder_path()
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


def save_results(accept_list, reject_list):
    folder = get_folder_path()
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