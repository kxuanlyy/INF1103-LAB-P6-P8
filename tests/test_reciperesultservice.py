from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import json
import tempfile
from data_manager.recipe_results_store import RecipeResultsStore
from logic_manager.reciperesultservice import RecipeResultService, normalize_items, ingredients_match, evaluate_recipes

TEMPLATES = [{"name": "Tomato Soup", "ingredients": ["tomato", "onion"]}]
INCOMING = [
    {"name": "Tomato Soup", "ingredients": ["tomato", "onion"], "instructions": ["Cook"]},
    {"name": "Mystery Dish", "ingredients": ["rice"], "instructions": ["Boil"]},
]


def write_json(folder, name, data):
    (folder / name).write_text(json.dumps(data), encoding="utf-8")


class TestRecipeResultService(unittest.TestCase):
    def test_successful_workflow(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            write_json(folder, "accepted_recipe.json", TEMPLATES)
            write_json(folder, "recipes.json", INCOMING)
            result = RecipeResultService(
                results_store=RecipeResultsStore(folder)
            ).create_results()
            self.assertEqual(result, {"accepted": 1, "rejected": 1})
            csv_text = (folder / "recipe_results.csv").read_text(encoding="utf-8")
            rejected_text = (folder / "rejected.txt").read_text(encoding="utf-8")
            self.assertIn("Tomato Soup", csv_text)
            self.assertIn("Mystery Dish", rejected_text)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            result = RecipeResultService(
                results_store=RecipeResultsStore(temp)
            ).create_results()
            self.assertIn("error", result)
            self.assertIn("accepted_recipe.json", result["error"])

    def test_empty_incoming(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            write_json(folder, "accepted_recipe.json", TEMPLATES)
            write_json(folder, "recipes.json", [])
            result = RecipeResultService(
                results_store=RecipeResultsStore(folder)
            ).create_results()
            self.assertEqual(result, {"error": "recipes.json is empty"})
            self.assertFalse((folder / "recipe_results.csv").exists())

    def test_custom_templates(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            write_json(folder, "accepted_recipe.json", [])
            write_json(folder, "recipes.json", INCOMING)
            result = RecipeResultService(
                results_store=RecipeResultsStore(folder)
            ).create_results(accepted_recipes=TEMPLATES)
            self.assertEqual(result, {"accepted": 1, "rejected": 1})

    def test_compatibility_wrappers(self):
        self.assertEqual(normalize_items([" MILK "]), {"milk"})
        self.assertTrue(ingredients_match(["milk"], ["milk"]))
        accepted, rejected = evaluate_recipes(TEMPLATES, INCOMING)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), 1)
