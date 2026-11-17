import json
import os
import tempfile
from pathlib import Path
from typing import Any


class BusinessRulesEditor:
    def __init__(self, rules_path=None):
        project_root = Path(__file__).resolve().parents[1]
        self.rules_path = (
            Path(rules_path)
            if rules_path is not None
            else project_root / "data_manager" / "accepted_recipe.json"
        )

    def load_rules(self) -> list[dict[str, Any]]:
        try:
            with self.rules_path.open("r", encoding="utf-8") as rules_file:
                rules = json.load(rules_file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read business rules: {exc}") from exc

        self._validate_rules(rules)
        return rules

    def editbusinessrules(
        self, updated_rules: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        self._validate_rules(updated_rules)
        self._save_atomically(updated_rules)
        return updated_rules

    @staticmethod
    def _validate_rules(rules: Any) -> None:
        if not isinstance(rules, list):
            raise ValueError(
                "Business rules must be a list of recipe objects."
            )

        for index, rule in enumerate(rules, start=1):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule {index} must be an object.")

            name = rule.get("name")
            ingredients = rule.get("ingredients")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    f"Rule {index} must have a non-empty name."
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
                    f"Rule {index} must have a non-empty "
                    "list of ingredients."
                )

    def _save_atomically(self, rules: list[dict[str, Any]]) -> None:
        temp_path = None

        try:
            self.rules_path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.rules_path.parent,
                delete=False,
            ) as temp_file:
                json.dump(rules, temp_file, indent=4, ensure_ascii=False)
                temp_file.write("\n")
                temp_path = Path(temp_file.name)

            os.replace(temp_path, self.rules_path)

        except OSError as exc:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

            raise ValueError(
                f"Could not save business rules: {exc}"
            ) from exc


def show_json(title: str, values: Any) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(json.dumps(values, indent=4, ensure_ascii=False))


def run_demo() -> None:
    original_rules = [
        {
            "name": "Tomato Soup",
            "ingredients": ["tomatoes", "onion", "water"],
        },
        {
            "name": "Vegetable Rice",
            "ingredients": ["rice", "carrots", "peas"],
        },
    ]

    updated_rules = [
        {
            "name": "Tomato Soup",
            "ingredients": ["tomatoes", "red onion", "vegetable stock"],
        },
        {
            "name": "Vegetable Rice",
            "ingredients": ["rice", "carrots", "peas", "bell pepper"],
        },
        {
            "name": "Mushroom Pasta",
            "ingredients": ["pasta", "mushrooms", "cream"],
        },
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        rules_path = Path(temp_dir) / "accepted_recipe.json"

        with rules_path.open("w", encoding="utf-8") as rules_file:
            json.dump(original_rules, rules_file, indent=4)

        editor = BusinessRulesEditor(rules_path)

        print("READING ORIGINAL RULES FROM JSON")
        print(f"File: {rules_path}")
        loaded_rules = editor.load_rules()
        show_json("Original rules read", loaded_rules)

        print("\nADDING THESE CHANGES")
        original_by_name = {rule["name"]: rule for rule in loaded_rules}

        for updated_rule in updated_rules:
            name = updated_rule["name"]

            if name not in original_by_name:
                print(f"\nAdded recipe: {name}")
                for ingredient in updated_rule["ingredients"]:
                    print(f"  Added ingredient: {ingredient}")
                continue

            old_ingredients = set(original_by_name[name]["ingredients"])
            new_ingredients = set(updated_rule["ingredients"])

            for ingredient in sorted(new_ingredients - old_ingredients):
                print(f"Added ingredient to {name}: {ingredient}")

        editor.editbusinessrules(updated_rules)

        print("\nREADING SAVED RULES BACK FROM JSON")
        reloaded_rules = editor.load_rules()
        show_json("Rules read back from file", reloaded_rules)

        print("\nDemo complete. The temporary file will now be removed.")

if __name__ == "__main__":
    run_demo()