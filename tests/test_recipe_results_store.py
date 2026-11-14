#Tests for data_manager/recipe_results_store.py (RecipeResultsStore)
import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

from data_manager import recipe_results_store
from data_manager.recipe_results_store import RecipeResultsStore


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.store = RecipeResultsStore(self.folder)

    def put_json(self, name, data):
        (self.folder / name).write_text(json.dumps(data), encoding="utf-8")


class TestFolder(StoreTestCase):
    def test_given_folder_is_used(self):
        self.assertEqual(self.store.get_folder_path(), self.folder)

    def test_string_folder_becomes_a_path(self):
        s = RecipeResultsStore(str(self.folder))
        self.assertIsInstance(s.get_folder_path(), Path)
        self.assertEqual(s.get_folder_path(), self.folder)

    def test_default_folder_is_the_module_folder(self):
        expected = Path(recipe_results_store.__file__).resolve().parent
        self.assertEqual(RecipeResultsStore().get_folder_path(), expected)


class TestLoadJsonFiles(StoreTestCase):
    def test_both_files_missing(self):
        result = self.store.load_json_files()
        self.assertEqual(list(result), ["error"])
        self.assertIn("accepted_recipe.json", result["error"])

    def test_only_accepted_missing(self):
        self.put_json("recipes.json", [])
        result = self.store.load_json_files()
        self.assertIn("accepted_recipe.json", result["error"])

    def test_only_recipes_missing(self):
        self.put_json("accepted_recipe.json", [])
        result = self.store.load_json_files()
        self.assertIn("recipes.json", result["error"])
        self.assertNotIn("accepted_recipe.json", result["error"])

    def test_loads_both(self):
        accepted = [{"name": "Soup"}]
        recipes = [{"name": "Soup", "ingredients": "water"}, {"name": "Stew"}]
        self.put_json("accepted_recipe.json", accepted)
        self.put_json("recipes.json", recipes)
        result = self.store.load_json_files()
        self.assertEqual(result, {"accepted_recipes": accepted, "recipes_from_json": recipes})

    def test_non_ascii_content(self):
        self.put_json("accepted_recipe.json", ["crème brûlée"])
        self.put_json("recipes.json", [])
        (self.folder / "accepted_recipe.json").write_text('["crème brûlée"]', encoding="utf-8")
        self.assertEqual(self.store.load_json_files()["accepted_recipes"], ["crème brûlée"])

    def test_invalid_json_raises(self):
        (self.folder / "accepted_recipe.json").write_text("{not json", encoding="utf-8")
        self.put_json("recipes.json", [])
        with self.assertRaises(json.JSONDecodeError):
            self.store.load_json_files()


class TestSaveResults(StoreTestCase):
    ACCEPTED = [
        {"name": "Soup", "ingredients": "water, salt", "instructions": "Boil"},
        {"name": "Stew, hearty", "ingredients": "beef", "instructions": "Line 1\nLine 2"},
    ]
    REJECTED = [
        {"name": "Mud pie", "reason": "not food"},
        {"name": "Glue", "reason": "toxic"},
    ]

    def read_csv(self):
        with open(self.folder / "recipe_results.csv", newline="", encoding="utf-8") as f:
            return list(csv.reader(f))

    def read_rejected(self):
        return (self.folder / "rejected.txt").read_text(encoding="utf-8")

    def test_returns_the_two_file_names(self):
        self.assertEqual(self.store.save_results([], []), ("recipe_results.csv", "rejected.txt"))

    def test_csv_has_header_and_rows(self):
        self.store.save_results(self.ACCEPTED, [])
        rows = self.read_csv()
        self.assertEqual(rows[0], ["name", "ingredients", "instructions"])
        self.assertEqual(rows[1], ["Soup", "water, salt", "Boil"])
        self.assertEqual(rows[2], ["Stew, hearty", "beef", "Line 1\nLine 2"])
        self.assertEqual(len(rows), 3)

    def test_empty_accepted_list_gives_header_only(self):
        self.store.save_results([], [])
        self.assertEqual(self.read_csv(), [["name", "ingredients", "instructions"]])

    def test_rejected_file_format(self):
        self.store.save_results([], self.REJECTED)
        self.assertEqual(
            self.read_rejected(),
            "Rejected recipe: Mud pie | Reason: not food\n"
            "Rejected recipe: Glue | Reason: toxic\n"
            "\nTotal rejected recipes: 2\n",
        )

    def test_no_rejections(self):
        self.store.save_results([], [])
        self.assertEqual(self.read_rejected(), "\nTotal rejected recipes: 0\n")

    def test_files_are_overwritten_not_appended(self):
        self.store.save_results(self.ACCEPTED, self.REJECTED)
        self.store.save_results(self.ACCEPTED[:1], self.REJECTED[:1])
        self.assertEqual(len(self.read_csv()), 2)
        self.assertIn("Total rejected recipes: 1", self.read_rejected())
        self.assertNotIn("Glue", self.read_rejected())

    def test_saved_csv_loads_back_as_a_recipe_table(self):
        from data_manager.recipe_table import RecipeTable
        self.store.save_results(self.ACCEPTED, [])
        t = RecipeTable(str(self.folder / "recipe_results.csv"))
        t.load()
        self.assertEqual(t.records, self.ACCEPTED)

    def test_extra_keys_in_accepted_recipes_raise(self):
        with self.assertRaises(ValueError):
            self.store.save_results([{"name": "A", "ingredients": "b", "instructions": "c", "extra": 1}], [])

    def test_rejected_entry_without_reason_raises(self):
        with self.assertRaises(KeyError):
            self.store.save_results([], [{"name": "A"}])

    def test_non_ascii_round_trip(self):
        rec = [{"name": "Crème brûlée 🍮", "ingredients": "œuf", "instructions": "Cuire"}]
        self.store.save_results(rec, [{"name": "Café", "reason": "trop sucré"}])
        self.assertEqual(self.read_csv()[1][0], "Crème brûlée 🍮")
        self.assertIn("Café", self.read_rejected())

    def test_missing_folder_raises(self):
        s = RecipeResultsStore(self.folder / "nope")
        with self.assertRaises(FileNotFoundError):
            s.save_results([], [])

    def test_only_the_two_output_files_are_created(self):
        self.store.save_results(self.ACCEPTED, self.REJECTED)
        self.assertEqual(sorted(os.listdir(self.folder)), ["recipe_results.csv", "rejected.txt"])


if __name__ == "__main__":
    unittest.main()
