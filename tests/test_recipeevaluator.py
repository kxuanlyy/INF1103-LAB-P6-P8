from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from logic_manager.recipeevaluator import RecipeEvaluator

TEMPLATES = [
    {"name": "Tomato Soup", "ingredients": ["tomato", "onion"]},
    {"name": "Egg Toast", "ingredients": ["egg", "bread"]},
]


class TestRecipeEvaluator(unittest.TestCase):
    def test_accepted(self):
        incoming = [{
            "name": " tomato   soup ",
            "ingredients": ["tomato", "onion"],
            "instructions": ["Chop", "Cook"],
        }]
        accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, incoming)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(rejected, [])
        self.assertEqual(accepted[0]["ingredients"], "tomato, onion")
        self.assertEqual(accepted[0]["instructions"], "Chop Cook")

    def test_unknown_name(self):
        accepted, rejected = RecipeEvaluator().evaluate(
            TEMPLATES, [{"name": "Pizza", "ingredients": ["tomato"]}]
        )
        self.assertEqual(accepted, [])
        self.assertEqual(
            rejected[0]["reason"], RecipeEvaluator.NAME_NOT_FOUND_REASON
        )

    def test_ingredient_mismatch(self):
        accepted, rejected = RecipeEvaluator().evaluate(
            TEMPLATES, [{"name": "Egg Toast", "ingredients": ["egg"]}]
        )
        self.assertEqual(accepted, [])
        self.assertEqual(len(rejected), 1)
        self.assertIn("1/2 matched", rejected[0]["reason"])
        self.assertIn("bread", rejected[0]["reason"])

    def test_mixed_results(self):
        incoming = [
            {"name": "Tomato Soup", "ingredients": ["tomato", "onion"], "instructions": []},
            {"name": "Unknown Dish", "ingredients": []},
            {"name": "Egg Toast", "ingredients": ["egg"]},
        ]
        accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, incoming)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), 2)

    def test_empty_and_missing_name(self):
        self.assertEqual(RecipeEvaluator().evaluate(TEMPLATES, []), ([], []))
        accepted, rejected = RecipeEvaluator().evaluate(
            TEMPLATES, [{"ingredients": ["egg"]}]
        )
        self.assertEqual(accepted, [])
        self.assertEqual(rejected[0]["name"], "Unknown Recipe")
