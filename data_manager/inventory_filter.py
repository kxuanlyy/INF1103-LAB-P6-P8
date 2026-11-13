from typing import Iterable, Optional, Union

Values = Union[str, Iterable[str], None]


class InventoryFilter:
    # Decides which inventory rows pass a set of dropdown-style filters

    NO_ALLERGENS = "none"

    def __init__(
        self,
        food_category: Values = None,
        storage_condition: Values = None,
        waste_risk_level: Values = None,
        allergen: Values = None,
        demand_level: Values = None,
        exclude_allergen: Values = None,
    ) -> None:
        self.food_category = self._wanted(food_category)
        self.storage_condition = self._wanted(storage_condition)
        self.waste_risk_level = self._wanted(waste_risk_level)
        self.allergen = self._wanted(allergen)
        self.demand_level = self._wanted(demand_level)
        self.exclude_allergen = self._wanted(exclude_allergen)

    #filter
    def is_active(self) -> bool:
        # False when no filter was supplied (every row would pass)
        return any((self.food_category, self.storage_condition, self.waste_risk_level,
                    self.allergen, self.demand_level, self.exclude_allergen))

    def matches(self, record: dict) -> bool:
        if self.food_category and not any(self._equals(record["food_category"], c) for c in self.food_category):
            return False
        if self.storage_condition and not any(self._contains(record["storage condition"], s) for s in self.storage_condition):
            return False
        if self.waste_risk_level and not any(self._equals(record["waste_risk_level"], r) for r in self.waste_risk_level):
            return False
        if self.demand_level and not any(self._equals(record["demand level"], d) for d in self.demand_level):
            return False
        if self.allergen and not any(self._has_allergen(record["allergen info"], a) for a in self.allergen):
            return False
        if self.exclude_allergen and any(self._has_allergen(record["allergen info"], a) for a in self.exclude_allergen):
            return False
        return True

    def apply(self, records: Iterable[dict]) -> list:
        # The rows that pass, in their original order (the same row objects, not copies)
        return [record for record in records if self.matches(record)]

    def __repr__(self) -> str:
        used = {name: values for name, values in vars(self).items() if values}
        return f"InventoryFilter({', '.join(f'{k}={v}' for k, v in used.items())})"

    #helpers
    @staticmethod
    def _wanted(value: Values) -> list:
        # One value or many -> a clean list with blanks and None removed
        if value is None:
            return []
        items = [value] if isinstance(value, str) else list(value)
        return [item.strip() for item in items if item and item.strip()]

    @staticmethod
    def _equals(value: str, wanted: str) -> bool:
        return value.lower() == wanted.lower()

    @staticmethod
    def _contains(value: str, wanted: str) -> bool:
        return wanted.lower() in value.lower()

    @classmethod
    def _has_allergen(cls, info: str, name: str) -> bool:
        if name.lower() == cls.NO_ALLERGENS:
            return info.strip().lower() in ("", cls.NO_ALLERGENS)
        return cls._contains(info, name)
