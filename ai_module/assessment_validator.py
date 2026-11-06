import json
import math
from datetime import date

from ai_module._constants import (
    LEVELS, TEXT_FIELDS, LEVEL_FIELDS, SCORE_LIMITS, FLAG_FIELDS, MAX_RECIPES,
    ANALYSIS_PROPERTIES, RECIPE_SCHEMA,
)


class AssessmentValidator:
    # Check stock inputs and AI output before other managers use the fields.

    def validate_text(self, value, field):
        # Require actual text; never silently coerce model or input values.
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be nonempty text.")

    def validate_number(self, value, field, maximum):
        # Reject booleans, non-finite numbers, and values outside the allowed range.
        if (type(value) not in (int, float) or not 0 <= value <= maximum
                or not math.isfinite(value)):
            raise ValueError(f"{field} is outside its allowed range.")

    def validate_recipes(self, recipes, item_id, inventory_ids=None, require_steps=False):
        # Check recipes; older saved assessments may omit steps unless required.
        if not isinstance(recipes, list) or len(recipes) > MAX_RECIPES:
            raise ValueError("AI recipes must be a list of at most five suggestions.")
        for recipe in recipes:
            allowed_fields = [set(RECIPE_SCHEMA["required"])]
            if not require_steps:
                allowed_fields.append({"name", "ingredient_ids"})
            allowed_fields += [fields | {"additional_ingredients"}
                               for fields in allowed_fields]
            if not isinstance(recipe, dict) or set(recipe) not in allowed_fields:
                raise ValueError("Invalid recipe fields.")
            self.validate_text(recipe["name"], "Recipe name")
            additional = recipe.get("additional_ingredients", [])
            if not isinstance(additional, list):
                raise ValueError("Additional ingredients must be a list.")
            for ingredient in additional:
                self.validate_text(ingredient, "Additional ingredient")
            if len(additional) != len({ingredient.strip().lower() for ingredient in additional}):
                raise ValueError("Additional ingredients must be unique.")
            if "how_to_make" in recipe:
                steps = recipe["how_to_make"]
                if not isinstance(steps, list) or not steps:
                    raise ValueError("Recipe preparation steps are missing or invalid.")
                for step in steps:
                    self.validate_text(step, "Preparation step")
            ingredient_ids = recipe["ingredient_ids"]
            if not isinstance(ingredient_ids, list) or not ingredient_ids:
                raise ValueError("Recipe ingredient IDs are missing or invalid.")
            for ingredient_id in ingredient_ids:
                self.validate_text(ingredient_id, "Ingredient ID")
            if len(ingredient_ids) != len(set(ingredient_ids)) or item_id not in ingredient_ids:
                raise ValueError("Recipe must include this item and contain unique ingredient IDs.")
            if inventory_ids is not None and not set(ingredient_ids).issubset(inventory_ids):
                raise ValueError("Recipe references an ingredient outside the supplied inventory.")

    def validate_analysis(self, value, item_id, inventory_ids=None, require_steps=False):
        # Validate AI output; the optional inventory argument preserves saved-record callers.
        if not isinstance(value, dict) or set(value) != set(ANALYSIS_PROPERTIES):
            raise ValueError("AI response must be an object with exactly the required fields.")
        for field in TEXT_FIELDS:
            self.validate_text(value[field], field)
        if value["item_id"] != item_id:
            raise ValueError("AI item ID does not match the target.")
        for field in LEVEL_FIELDS:
            if value[field] not in LEVELS:
                raise ValueError(f"Invalid AI {field}.")
        for field, maximum in SCORE_LIMITS.items():
            self.validate_number(value[field], field, maximum)
        for field in FLAG_FIELDS:
            if type(value[field]) is not bool:
                raise ValueError(f"AI {field} must be a boolean.")
        self.validate_recipes(value["recipe_suggestions"], item_id, inventory_ids, require_steps)
        return value

    def validate_stock_item(self, item):
        # Check the stock record contract before passing user data to the API.
        if not isinstance(item, dict):
            raise ValueError("Stock item must be an object.")
        for field in ("id", "name", "unit", "storage_condition", "allergens", "use_by"):
            self.validate_text(item[field], field)
        quantity = item["quantity"]
        if type(quantity) not in (int, float) or quantity <= 0 or not math.isfinite(quantity):
            raise ValueError("Quantity must be a finite positive number.")
        if date.fromisoformat(item["use_by"]).isoformat() != item["use_by"]:
            raise ValueError("Use-by date must use YYYY-MM-DD.")
        if item["demand_level"] not in LEVELS:
            raise ValueError("Invalid demand level.")
        for field in ("storage_status", "allergen_status"):
            if item[field] not in ("yes", "no", "unknown"):
                raise ValueError("Invalid verification status.")

    def validate_inputs(self, item, inventory, today):
        # Validate request data and return the unique inventory IDs for response checks.
        if type(today) is not date:
            raise ValueError("Assessment date must be a date.")
        if not isinstance(inventory, list) or not inventory:
            raise ValueError("Inventory must be a nonempty list.")
        self.validate_stock_item(item)
        inventory_by_id = {}
        for stock_item in inventory:
            self.validate_stock_item(stock_item)
            if stock_item["id"] in inventory_by_id:
                raise ValueError("Inventory IDs must be unique.")
            inventory_by_id[stock_item["id"]] = stock_item
        if inventory_by_id.get(item["id"]) != item:
            raise ValueError("The target item must match its inventory entry.")
        return set(inventory_by_id)

    def extract_response(self, completion):
        # Reject truncated, refused, or missing completions before parsing their content.
        try:
            choice = completion.choices[0]
            if choice.finish_reason != "stop" or getattr(choice.message, "refusal", None):
                raise ValueError("AI response was incomplete or refused.")
            return choice.message.content
        except (AttributeError, IndexError, KeyError, TypeError):
            raise ValueError("AI completion is missing its response.") from None

    def unique_object(self, pairs):
        # Reject duplicate JSON keys instead of silently accepting the last value.
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("AI JSON contains duplicate fields.")
            result[key] = value
        return result

    def reject_constant(self, value):
        # Reject NaN and Infinity, which are not valid JSON numbers.
        raise ValueError("AI JSON contains a non-finite number.")

    def parse_response(self, content):
        # Decode one JSON object, allowing an optional enclosing Markdown code fence.
        if not isinstance(content, str) or not content.strip():
            raise ValueError("AI response must contain JSON text.")
        content = content.strip()
        lines = content.splitlines()
        if lines[0].lower() in ("```", "```json") and lines[-1] == "```":
            content = "\n".join(lines[1:-1])
        try:
            value = json.loads(content, object_pairs_hook=self.unique_object,
                               parse_constant=self.reject_constant)
        except RecursionError:
            raise ValueError("AI JSON is nested too deeply.") from None
        if not isinstance(value, dict):
            raise ValueError("AI response must be an object.")
        return value

