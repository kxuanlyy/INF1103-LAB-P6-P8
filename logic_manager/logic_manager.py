"""Object-oriented recipe validation and result creation.

This module keeps recipe matching separate from data loading and saving.
"""

from data_manager.data_manager import load_json_files, save_results


class IngredientMatcher:
    """Compare recipe ingredients with a standard ingredient template."""

    def __init__(self, minimum_match_ratio=0.6):
        # Minimum fraction of template ingredients that must match.
        self.minimum_match_ratio = minimum_match_ratio

    @staticmethod
    def normalize_items(items):
        # Trim whitespace and lowercase items for consistent comparison.
        return {item.strip().lower() for item in items}

    def matches(self, expected_ingredients, actual_ingredients):
        # Normalize both lists before comparing them.
        expected = self.normalize_items(expected_ingredients)
        actual = self.normalize_items(actual_ingredients)

        # Empty ingredient lists cannot meet the matching requirement.
        if not expected or not actual:
            return False

        matched_count = 0
        for expected_item in expected:
            expected_words = set(expected_item.split())

            # One shared word is enough to count this ingredient as a match.
            if any(
                expected_words.intersection(actual_item.split())
                for actual_item in actual
            ):
                matched_count += 1

        # Compare the matching fraction with the configured threshold.
        return matched_count / len(expected) >= self.minimum_match_ratio


class RecipeEvaluator:
    """Match incoming recipes to templates and classify their results."""

    NAME_NOT_FOUND_REASON = "Recipe name not found in accepted_recipe.json"
    INGREDIENTS_MISMATCH_REASON = (
        "Ingredients do not match valid accepted criteria"
    )

    def __init__(self, ingredient_matcher=None):
        # Allow a custom matcher to be supplied when needed.
        self.ingredient_matcher = ingredient_matcher or IngredientMatcher()

    @staticmethod
    def _find_matching_template(recipe_name, accepted_recipes):
        # Match a recipe to the first template with any name word in common.
        recipe_words = set(recipe_name.strip().lower().split())
        if not recipe_words:
            return None

        for template in accepted_recipes:
            template_name = template.get("name", "").strip()
            template_words = set(template_name.lower().split())

            if recipe_words.intersection(template_words):
                return template

        return None

    @staticmethod
    def _accepted_result(recipe):
        # Keep the accepted result in the original output format.
        return {
            "name": recipe.get("name", ""),
            "ingredients": ", ".join(recipe.get("ingredients", [])),
            "instructions": " ".join(recipe.get("instructions", [])),
        }

    @staticmethod
    def _rejected_result(name, reason):
        # Keep the rejected result in the original output format.
        return {"name": name, "reason": reason}

    def evaluate(self, accepted_recipes, recipes_from_json):
        # Collect accepted and rejected recipes separately.
        accept_list = []
        reject_list = []

        for recipe in recipes_from_json:
            recipe_name = recipe.get("name", "").strip()
            template = self._find_matching_template(
                recipe_name, accepted_recipes
            )

            # Reject recipes that do not match an accepted template name.
            if template is None:
                reject_list.append(
                    self._rejected_result(
                        recipe_name or "Unknown Recipe",
                        self.NAME_NOT_FOUND_REASON,
                    )
                )
                continue

            # Compare actual ingredients against the matched template.
            expected_ingredients = template.get("ingredients", [])
            actual_ingredients = recipe.get("ingredients", [])

            if self.ingredient_matcher.matches(
                expected_ingredients, actual_ingredients
            ):
                accept_list.append(self._accepted_result(recipe))
            else:
                reject_list.append(
                    self._rejected_result(
                        recipe_name, self.INGREDIENTS_MISMATCH_REASON
                    )
                )

        return accept_list, reject_list


class RecipeResultService:
    """Load, evaluate, and save recipe results."""

    def __init__(self, evaluator=None):
        # Allow a custom evaluator to be supplied when needed.
        self.evaluator = evaluator or RecipeEvaluator()

    def create_results(self):
        # Load the reference templates and incoming recipes.
        data = load_json_files()

        # Pass through any error returned by the data manager.
        if isinstance(data, dict) and "error" in data:
            return data

        accepted_recipes = data["accepted_recipes"]
        recipes_from_json = data["recipes_from_json"]

        # Return an error when there are no incoming recipes to evaluate.
        if not recipes_from_json:
            return {"error": "recipes.json is empty"}

        # Evaluate the recipes and save both result lists.
        accept_list, reject_list = self.evaluator.evaluate(
            accepted_recipes, recipes_from_json
        )
        save_results(accept_list, reject_list)

        # Report the number of recipes in each result list.
        return {
            "accepted": len(accept_list),
            "rejected": len(reject_list),
        }


# These wrappers preserve the original functions for existing callers.
def normalize_items(items):
    return IngredientMatcher.normalize_items(items)


def ingredients_match(expected_ingredients, json_ingredients):
    return IngredientMatcher().matches(expected_ingredients, json_ingredients)


def evaluate_recipes(accepted_recipes, recipes_from_json):
    return RecipeEvaluator().evaluate(accepted_recipes, recipes_from_json)


def create_recipe_results():
    return RecipeResultService().create_results()