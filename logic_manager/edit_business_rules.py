import json
import os
import tempfile
from pathlib import Path
from typing import Any


class BusinessRulesEditor:
    """Loads, validates, and saves the recipe templates used as business rules."""

    def __init__(self, rules_path=None):
        project_root = Path(__file__).resolve().parents[1]
        self.rules_path = (
            Path(rules_path)
            if rules_path is not None
            else project_root / "data_manager" / "accepted_recipe.json"
        )
    def load_rules(self) -> list[dict[str, Any]]:
        """Return the current rules, or raise a clear error if the file is invalid."""
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
        """Validate and save rules supplied by the GUI; return the saved rules."""
        self._validate_rules(updated_rules)
        self._save_atomically(updated_rules)
        return updated_rules

    @staticmethod
    def _validate_rules(rules: Any) -> None:
        if not isinstance(rules, list):
            raise ValueError("Business rules must be a list of recipe objects.")

        for index, rule in enumerate(rules, start=1):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule {index} must be an object.")

            name = rule.get("name")
            ingredients = rule.get("ingredients")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"Rule {index} must have a non-empty name.")

            if (
                not isinstance(ingredients, list)
                or not ingredients
                or any(not isinstance(item, str) or not item.strip()
                       for item in ingredients)
            ):
                raise ValueError(
                    f"Rule {index} must have a non-empty list of ingredients."
                )

    def _save_atomically(self, rules: list[dict[str, Any]]) -> None:
        """Write to a temporary file first so a failed save won't corrupt the rules."""
        temp_path: Path | None = None

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
            raise ValueError(f"Could not save business rules: {exc}") from exc