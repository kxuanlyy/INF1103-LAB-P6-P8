from datetime import date, datetime
from typing import Optional, Union

from data_manager.csv_table import CsvTable, log

INVENTORY_COLUMNS = [
    "food", "food_category", "use-by", "storage condition", "days_to_expiry",
    "waste_risk_level", "allergen info", "demand level", "quantity",
]

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

# food_inventory.csv
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
        # Append an inventory record and write it to food_inventory.csv

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
        # Change fields of the inventory record at `index` and save
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
