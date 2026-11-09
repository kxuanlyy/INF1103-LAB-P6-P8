from typing import Iterable, Optional, Union

from csv_table import CsvTable

RECIPE_COLUMNS = ["name", "ingredients", "instructions"]


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
