import json
import os
import tempfile
from pathlib import Path
from typing import Any


class TestRecipeEditor:
    def __init__(self, recipes_path=None):
        project_root = Path(__file__).resolve().parents[1]
        self.recipes_path = (
            Path(recipes_path)
            if recipes_path is not None
            else project_root / "tests" / "test_recipe.json"
        )

    def load_recipes(self) -> list[dict[str, Any]]:
        if not self.recipes_path.exists():
            return []

        try:
            with self.recipes_path.open("r", encoding="utf-8") as file:
                contents = file.read()
        except OSError as exc:
            raise ValueError(f"Could not read recipes: {exc}") from exc

        if not contents.strip():
            return []

        try:
            recipes = json.loads(contents)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"The recipe file contains invalid JSON: {exc}"
            ) from exc

        self._validate_recipes(recipes)
        return recipes

    def edit_recipes(self, updated_recipes: list[dict[str, Any]]) -> None:
        self._validate_recipes(updated_recipes)
        self._save_atomically(updated_recipes)

    def edit_from_terminal(self) -> None:
        try:
            recipes = self.load_recipes()
        except ValueError as exc:
            print(f"\nCould not load existing recipes: {exc}")
            choice = input(
                "Start with an empty recipe list? "
                "The file changes only if you later choose Save. (y/N): "
            ).strip().lower()

            if choice != "y":
                print("Editing cancelled.")
                return

            recipes = []

        while True:
            print("\n" + "=" * 50)
            print("              TEST RECIPE EDITOR")
            print("=" * 50)

            if recipes:
                print("\nSaved recipes:")
                for index, recipe in enumerate(recipes, start=1):
                    print(f"  {index:>2}. {recipe['name']}")
            else:
                print("\nNo recipes are currently saved.")

            print("\nTo edit a recipe or its ingredients, type its recipe number.")
            print("  V        View all recipes and ingredients")
            print("  A        Add a recipe")
            print("  D<number> Delete a recipe, e.g. D2")
            print("  S        Save changes")
            print("  Q        Quit without saving")

            choice = input("\nYour choice: ").strip().lower()

            if choice == "v":
                self._view_recipes(recipes)

            elif choice == "s":
                try:
                    self.edit_recipes(recipes)
                except (OSError, ValueError) as exc:
                    print(f"\nCould not save recipes: {exc}")
                else:
                    print(f"\nChanges saved to:\n{self.recipes_path}")
                    return

            elif choice == "q":
                print("\nChanges discarded.")
                return

            elif choice == "a":
                self._add_recipe(recipes)

            elif choice.startswith("d") and choice[1:].isdigit():
                recipe_index = int(choice[1:]) - 1

                if 0 <= recipe_index < len(recipes):
                    removed = recipes.pop(recipe_index)
                    print(f"\nDeleted recipe: {removed['name']}")
                else:
                    print("\nThat recipe number is not in the list.")

            elif choice.isdigit():
                recipe_index = int(choice) - 1

                if 0 <= recipe_index < len(recipes):
                    self._edit_recipe(recipes[recipe_index])
                else:
                    print("\nThat recipe number is not in the list.")

            else:
                print("\nPlease enter a recipe number or one of the listed options.")


    def _view_recipes(self, recipes: list[dict[str, Any]]) -> None:
                print("\n" + "-" * 50)
                print("                 ALL RECIPES")
                print("-" * 50)

                if not recipes:
                    print("No recipes to display.")
                    return

                for index, recipe in enumerate(recipes, start=1):
                    print(f"\n{index}. {recipe['name']}")
                    print("   Ingredients:")
                    for ingredient in recipe["ingredients"]:
                        print(f"     • {ingredient}")

                print("\n" + "-" * 50)

    def _add_recipe(self, recipes: list[dict[str, Any]]) -> None:
        name = input("Recipe name: ").strip()
        ingredients = self._read_ingredients()

        recipe = {"name": name, "ingredients": ingredients}

        try:
            self._validate_recipes([recipe])
        except ValueError as exc:
            print(f"Recipe not added: {exc}")
            return

        recipes.append(recipe)
        print(f"Added: {name}")

    def _edit_recipe(self, recipe: dict[str, Any]) -> None:
        print(f"\nEditing: {recipe['name']}")
        new_name = input(
            f"New recipe name [press Enter to keep '{recipe['name']}']: "
        ).strip()

        if new_name:
            recipe["name"] = new_name

        while True:
            print(f"\nIngredients for {recipe['name']}:")
            for index, ingredient in enumerate(recipe["ingredients"], start=1):
                print(f"{index}. {ingredient}")

            print("\nA = Add ingredient")
            print("D<number> = Delete an ingredient, e.g. D2")
            print("E<number> = Edit an ingredient, e.g. E2")
            print("S = Finish editing this recipe")

            choice = input("Choice: ").strip().lower()

            if choice == "s":
                return

            elif choice == "a":
                ingredient = input("New ingredient: ").strip()
                if ingredient:
                    recipe["ingredients"].append(ingredient)
                else:
                    print("Ingredient cannot be empty.")

            elif choice.startswith("d") and choice[1:].isdigit():
                ingredient_index = int(choice[1:]) - 1
                if 0 <= ingredient_index < len(recipe["ingredients"]):
                    removed = recipe["ingredients"].pop(ingredient_index)
                    print(f"Removed ingredient: {removed}")
                else:
                    print("That ingredient number is not in the list.")

            elif choice.startswith("e") and choice[1:].isdigit():
                ingredient_index = int(choice[1:]) - 1
                if 0 <= ingredient_index < len(recipe["ingredients"]):
                    replacement = input("Replacement ingredient: ").strip()
                    if replacement:
                        recipe["ingredients"][ingredient_index] = replacement
                    else:
                        print("Ingredient cannot be empty.")
                else:
                    print("That ingredient number is not in the list.")
            elif choice.startswith("d") and choice[1:].isdigit():
                ingredient_index = int(choice[1:]) - 1

                if 0 <= ingredient_index < len(recipe["ingredients"]):
                    removed = recipe["ingredients"].pop(ingredient_index)
                    print(f"Removed ingredient: {removed}")
                else:
                    print("That ingredient number is not in the list.")
            else:
                print("Invalid choice.")


    @staticmethod
    def _read_ingredients() -> list[str]:
        ingredient_text = input(
            "Ingredients, separated by commas: "
        ).strip()

        return [
            item.strip()
            for item in ingredient_text.split(",")
            if item.strip()
        ]

    @staticmethod
    def _validate_recipes(recipes: Any) -> None:
        if not isinstance(recipes, list):
            raise ValueError("Recipes must be a list.")

        for index, recipe in enumerate(recipes, start=1):
            if not isinstance(recipe, dict):
                raise ValueError(f"Recipe {index} must be an object.")

            name = recipe.get("name")
            ingredients = recipe.get("ingredients")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    f"Recipe {index} must have a non-empty name."
                )

            if (
                not isinstance(ingredients, list)
                or not ingredients
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in ingredients
                )
            ):
                raise ValueError(
                    f"Recipe {index} must have a non-empty list "
                    "of ingredients."
                )

    def _save_atomically(self, recipes: list[dict[str, Any]]) -> None:
        temp_path = None

        try:
            self.recipes_path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.recipes_path.parent,
                delete=False,
            ) as temp_file:
                json.dump(recipes, temp_file, indent=4, ensure_ascii=False)
                temp_file.write("\n")
                temp_path = Path(temp_file.name)

            os.replace(temp_path, self.recipes_path)

        except OSError as exc:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise ValueError(f"Could not save recipes: {exc}") from exc


if __name__ == "__main__":
    editor = TestRecipeEditor()
    editor.edit_from_terminal()