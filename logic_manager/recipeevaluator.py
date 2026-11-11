from logic_manager.ingredientmatcher import IngredientMatcher 
from logic_manager.exact_name_template_matcher import ExactNameTemplateMatcher

class RecipeEvaluator:
    """Match incoming recipes to templates and classify their results."""

    NAME_NOT_FOUND_REASON = "Recipe name not found in accepted_recipe.json"
    INGREDIENTS_MISMATCH_REASON = (
        "Ingredients do not match valid accepted criteria"
    )

    def __init__(self, ingredient_matcher=None, template_matcher=None):
        self.ingredient_matcher = ingredient_matcher or IngredientMatcher()
        self.template_matcher = template_matcher or ExactNameTemplateMatcher()


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
            template = self.template_matcher.find_template(
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

            comparison = self.ingredient_matcher.compare(
                expected_ingredients, actual_ingredients
            )

            if comparison["matches"]:
                accept_list.append(self._accepted_result(recipe))
            else:
                matched = comparison["matched"]
                missing = comparison["unmatched"]

                reason = (
                    f"Ingredient mismatch: {len(matched)}/"
                    f"{len(matched) + len(missing)} matched "
                    f"({comparison['match_ratio']:.0%}; "
                    f"{comparison['required_ratio']:.0%} required). "
                    f"Matched: {', '.join(matched) if matched else 'none'}. "
                    f"Missing: {', '.join(missing) if missing else 'none'}."
                )

                reject_list.append(
                    self._rejected_result(recipe_name, reason)
                )

        return accept_list, reject_list
