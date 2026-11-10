from logic_manager.recipeevaluator import RecipeEvaluator
from logic_manager.ingredientmatcher import IngredientMatcher
from data_manager.recipe_results_store import RecipeResultsStore

class RecipeResultService:
    """Load, evaluate, and save recipe results."""

    def __init__(self, evaluator=None, results_store=None):
        # Allow a custom evaluator or results store to be supplied when needed.
        self.evaluator = evaluator or RecipeEvaluator()
        self.results_store = results_store or RecipeResultsStore()

    def create_results(self, accepted_recipes=None):
        # Load the reference templates and incoming recipes.
        data = self.results_store.load_json_files()

        # Pass through any error returned by the data manager.
        if isinstance(data, dict) and "error" in data:
            return data
        if accepted_recipes is None:
            accepted_recipes = data["accepted_recipes"]


        recipes_from_json = data["recipes_from_json"]

        # Return an error when there are no incoming recipes to evaluate.
        if not recipes_from_json:
            return {"error": "recipes.json is empty"}

        # Evaluate the recipes and save both result lists.
        accept_list, reject_list = self.evaluator.evaluate(
            accepted_recipes, recipes_from_json
        )
        self.results_store.save_results(accept_list, reject_list)

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