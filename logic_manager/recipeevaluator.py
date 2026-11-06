from logic_manager.ingredientmatcher import IngredientMatcher 

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
