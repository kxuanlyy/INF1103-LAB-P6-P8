import unittest
from unittest.mock import patch
from pathlib import Path
import csv
import logic_manager


# Self-contained terminal styling for the test runner
class TestColors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"


class TestLogicManagerWithScenarios(unittest.TestCase):

    def setUp(self):
        """Define hardcoded reference template data."""
        self.mock_accepted_recipes = [
            {
                "name": "Spaghetti Bolognese",
                "ingredients": ["spaghetti", "ground beef", "tomato", "onion", "garlic"]
            },
            {
                "name": "Chicken Curry",
                "ingredients": ["chicken", "onion", "garlic", "ginger", "curry powder", "coconut milk"]
            }
        ]

    def test_normalize_items(self):
        """Test item normalization (stripping spaces and lowercasing)."""
        input_list = ["  Spaghetti  ", "Ground BEEF", "tomato"]
        expected = {"spaghetti", "ground beef", "tomato"}
        self.assertEqual(logic_manager.normalize_items(input_list), expected)

    def test_ingredients_match_threshold(self):
        """Test flexible ingredient matching percentage threshold (>= 60%)."""
        expected = ["spaghetti", "ground beef", "tomato", "onion", "garlic"]
        
        # Good Case: 100% match (plus extra ingredients)
        actual_good = ["spaghetti", "ground beef", "tomato", "onion", "garlic", "salt", "pepper"]
        is_match = logic_manager.ingredients_match(expected, actual_good)
        self.assertTrue(is_match)

        # Bad Case: Low match rate (below 60%)
        actual_bad = ["spaghetti", "salt"]  # Only 1 out of 5 matched (20%)
        is_match = logic_manager.ingredients_match(expected, actual_bad)
        self.assertFalse(is_match)

    @patch("logic_manager.load_json_files")
    def test_pipeline_with_dynamic_file_reporting(self, mock_load):
        """
        Test pipeline execution using an explicit list in code, then dynamically 
        read recipe_results.csv and rejected.txt to display the results.
        """
        # Explicit test data list defined directly in the code (simulating AI output)
        recipes_test_cases = [
            {
                "name": "Spaghetti Bolognese",
                "ingredients": ["spaghetti", "ground beef", "tomato", "onion", "garlic", "olive oil"],
                "instructions": ["Cook pasta", "Simmer sauce"]
            },
            {
                "name": "Chicken Curry",
                "ingredients": ["chicken", "onion", "garlic", "ginger", "curry powder", "coconut milk", "cilantro"],
                "instructions": ["Sauté spices", "Add chicken"]
            },
            {
                "name": "Beef Tacos",
                "ingredients": ["ground beef", "taco shells", "lettuce"],
                "instructions": ["Cook beef", "Assemble"]
            },
            {
                "name": "Sushi Roll",
                "ingredients": ["rice", "fish", "seaweed"],
                "instructions": ["Roll sushi"]
            },
            {
                "name": "Spaghetti Bolognese",
                "ingredients": ["chocolate", "sugar", "butter"],
                "instructions": ["Mix strangely"]
            }
        ]

        mock_load.return_value = {
            "accepted_recipes": self.mock_accepted_recipes,
            "recipes_from_json": recipes_test_cases
        }

        # Run pipeline (logic_manager evaluates the in-code list and writes files via data_manager)
        result = logic_manager.create_recipe_results()

        # Expected outcome: 2 accepted, 3 rejected based on the list above
        self.assertEqual(result, {"accepted": 2, "rejected": 3})

        # Verify output files are physically created by data_manager
        folder = Path(__file__).resolve().parent
        results_file = folder / "recipe_results.csv"
        rejected_file = folder / "rejected.txt"

        self.assertTrue(results_file.exists(), "recipe_results.csv was not created!")
        self.assertTrue(rejected_file.exists(), "rejected.txt was not created!")

        # --- Dynamically Read Accepted Recipes from CSV ---
        accepted_entries = []
        if results_file.exists():
            with open(results_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name") or row.get("Recipe Name") or list(row.values())[0]
                    accepted_entries.append(name)

        # --- Dynamically Read Rejected Items from Text Log ---
        rejected_entries = []
        if rejected_file.exists():
            with open(rejected_file, mode="r", encoding="utf-8") as f:
                rejected_entries = [line.strip() for line in f if line.strip()]

        # --- Dynamic Test Summary Box Report ---
        print(f"\n{TestColors.CYAN}{'='*65}")
        print(f"       TEST SUITE: DYNAMIC FILE CONTENT & PATH REPORT")
        print(f"{'='*65}{TestColors.ENDC}")
        
        print(f"  {TestColors.GREEN}✔ ACCEPTED RECIPES{TestColors.ENDC}")
        if accepted_entries:
            for item in accepted_entries:
                print(f"    - {item}")
        else:
            print(f"    (None)")
        
        print(f"\n  {TestColors.FAIL}✖ REJECTED RECIPES{TestColors.ENDC}")
        if rejected_entries:
            for item in rejected_entries:
                print(f"    - {item}")
        else:
            print(f"    (None)")
        
        print(f"{TestColors.CYAN}{'-'*65}{TestColors.ENDC}")
        print(f"  Accepted Recipes saved in recipe_results.csv")
        print(f"  Rejected Recipes saved in rejected.txt")
        print(f"{TestColors.CYAN}{'='*65}\n{TestColors.ENDC}")

    @patch("logic_manager.load_json_files")
    def test_pipeline_empty_recipes_file(self, mock_load):
        """Test handling when recipes data is empty."""
        mock_load.return_value = {
            "accepted_recipes": self.mock_accepted_recipes,
            "recipes_from_json": []
        }

        result = logic_manager.create_recipe_results()
        self.assertEqual(result, {"error": "recipes.json is empty"})

    @patch("logic_manager.load_json_files")
    def test_pipeline_missing_files_error(self, mock_load):
        """Test handling when data_manager returns a file-not-found error."""
        mock_load.return_value = {"error": "Could not find file"}

        result = logic_manager.create_recipe_results()
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)