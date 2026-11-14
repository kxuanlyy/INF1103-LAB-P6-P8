#Tests for data_manager/recipe_table.py (RecipeTable)
import csv
import os
import tempfile
import unittest
from unittest import mock

from data_manager.recipe_table import RECIPE_COLUMNS, RecipeTable

FIXTURE = (
    "name,ingredients,instructions\n"
    "Pancakes,\"Flour, Milk, Eggs\",Mix and fry\n"
    "Omelette,\"eggs, cheese, milk\",Whisk then cook gently\n"
    "Salad,\"lettuce, tomato, olive oil\",Chop and toss\n"
    "Cheese Toast,\"bread, cheddar cheese\",Grill until golden\n"
)


class RecipeTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "recipes.csv")

    def make(self, text=FIXTURE) -> RecipeTable:
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        t = RecipeTable(self.path)
        t.load()
        return t

    def disk_rows(self):
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


class TestHelpers(unittest.TestCase):
    def test_columns(self):
        self.assertEqual(RECIPE_COLUMNS, ["name", "ingredients", "instructions"])
        self.assertEqual(RecipeTable.COLUMNS, RECIPE_COLUMNS)

    def test_split_items_lowercases_and_strips(self):
        self.assertEqual(RecipeTable._split_items(" Flour , MILK,Eggs "), ["flour", "milk", "eggs"])

    def test_split_items_drops_blanks(self):
        self.assertEqual(RecipeTable._split_items("a,, ,b,"), ["a", "b"])
        self.assertEqual(RecipeTable._split_items(""), [])

    def test_join_ingredients_from_string(self):
        self.assertEqual(RecipeTable._join_ingredients("  a, b  "), "a, b")

    def test_join_ingredients_from_list(self):
        self.assertEqual(RecipeTable._join_ingredients([" a ", "b"]), "a, b")
        self.assertEqual(RecipeTable._join_ingredients(("x",)), "x")
        self.assertEqual(RecipeTable._join_ingredients([]), "")


class TestLoad(RecipeTestCase):
    def test_loads_all_recipes(self):
        t = self.make()
        self.assertEqual([r["name"] for r in t.records],
                         ["Pancakes", "Omelette", "Salad", "Cheese Toast"])
        self.assertEqual(t.records[0]["ingredients"], "Flour, Milk, Eggs")

    def test_missing_file_is_created(self):
        t = RecipeTable(self.path)
        with self.assertLogs("data_manager", "WARNING"):
            t.load()
        self.assertEqual(t.records, [])
        self.assertTrue(os.path.exists(self.path))


class TestAdd(RecipeTestCase):
    def test_add_appends_and_saves(self):
        t = self.make()
        rec = t.add("Soup", "water, salt", "Boil")
        self.assertEqual(t.records[-1], rec)
        self.assertEqual(self.disk_rows()[-1], {"name": "Soup", "ingredients": "water, salt", "instructions": "Boil"})

    def test_add_accepts_ingredient_list_and_strips(self):
        t = self.make()
        rec = t.add("  Soup ", [" water ", "salt"], "  Boil  ")
        self.assertEqual(rec, {"name": "Soup", "ingredients": "water, salt", "instructions": "Boil"})

    def test_blank_name_rejected(self):
        t = self.make()
        for bad in ("", "   "):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "name is required"):
                    t.add(bad, "a", "b")
        self.assertEqual(len(t.records), 4)

    def test_failed_save_rolls_back(self):
        t = self.make()
        with mock.patch("os.replace", side_effect=PermissionError("locked")):
            with self.assertLogs("data_manager", "ERROR"):
                with self.assertRaises(PermissionError):
                    t.add("Soup", "a", "b")
        self.assertEqual(len(t.records), 4)


class TestUpdate(RecipeTestCase):
    def test_update_one_field(self):
        t = self.make()
        rec = t.update(2, instructions="  Toss well ")
        self.assertEqual(rec["instructions"], "Toss well")
        self.assertEqual(rec["name"], "Salad")
        self.assertEqual(self.disk_rows()[2]["instructions"], "Toss well")

    def test_update_all_fields(self):
        t = self.make()
        rec = t.update(0, name=" Crepes ", ingredients=["flour", "milk"], instructions="Fry")
        self.assertEqual(rec, {"name": "Crepes", "ingredients": "flour, milk", "instructions": "Fry"})
        self.assertEqual(t.records[0], rec)

    def test_empty_string_can_clear_ingredients(self):
        t = self.make()
        self.assertEqual(t.update(0, ingredients="")["ingredients"], "")

    def test_blank_name_rejected_and_unchanged(self):
        t = self.make()
        with self.assertRaisesRegex(ValueError, "name is required"):
            t.update(0, name="  ")
        self.assertEqual(t.records[0]["name"], "Pancakes")

    def test_bad_index(self):
        t = self.make()
        for bad in (-1, 4, True, "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(IndexError):
                    t.update(bad, name="x")

    def test_failed_save_restores_record(self):
        t = self.make()
        old = t.records[0]
        with mock.patch("os.replace", side_effect=PermissionError("locked")):
            with self.assertLogs("data_manager", "ERROR"):
                with self.assertRaises(PermissionError):
                    t.update(0, name="New")
        self.assertIs(t.records[0], old)

    def test_delete(self):
        t = self.make()
        self.assertEqual(t.delete(1)["name"], "Omelette")
        self.assertEqual(len(self.disk_rows()), 3)


class TestSearch(RecipeTestCase):
    def setUp(self):
        super().setUp()
        self.t = self.make()

    def found(self, **kw):
        return [r["name"] for r in self.t.search(**kw)]

    def test_no_filters_returns_all(self):
        self.assertEqual(len(self.t.search()), 4)

    def test_returns_actual_records(self):
        self.assertIs(self.t.search(name="salad")[0], self.t.records[2])

    def test_name_substring(self):
        self.assertEqual(self.found(name="CAKE"), ["Pancakes"])
        self.assertEqual(self.found(name="x-none"), [])

    def test_instructions_substring(self):
        self.assertEqual(self.found(instructions="cook"), ["Omelette"])

    def test_ingredient_single_string(self):
        self.assertEqual(self.found(ingredient="eggs"), ["Pancakes", "Omelette"])

    def test_ingredient_matches_inside_an_item(self):
        self.assertEqual(self.found(ingredient="oil"), ["Salad"])           # "olive oil"
        self.assertEqual(self.found(ingredient="cheese"), ["Omelette", "Cheese Toast"])

    def test_ingredient_matching_is_per_item_not_whole_text(self):
        # "milk, cheese" would match as text, but no single item contains it
        self.assertEqual(self.found(ingredient="milk, cheese"), [])

    def test_ingredient_list_requires_all(self):
        self.assertEqual(self.found(ingredient=["eggs", "milk"]), ["Pancakes", "Omelette"])
        self.assertEqual(self.found(ingredient=["eggs", "flour"]), ["Pancakes"])
        self.assertEqual(self.found(ingredient=["eggs", "lettuce"]), [])

    def test_ingredient_case_insensitive(self):
        self.assertEqual(self.found(ingredient="FLOUR"), ["Pancakes"])

    def test_any_ingredient(self):
        self.assertEqual(self.found(any_ingredient=["lettuce", "bread"]), ["Salad", "Cheese Toast"])
        self.assertEqual(self.found(any_ingredient="tomato"), ["Salad"])

    def test_exclude_ingredient(self):
        self.assertEqual(self.found(exclude_ingredient="milk"), ["Salad", "Cheese Toast"])
        self.assertEqual(self.found(exclude_ingredient=["milk", "bread"]), ["Salad"])

    def test_combined_filters(self):
        self.assertEqual(self.found(ingredient="eggs", exclude_ingredient="flour"), ["Omelette"])
        self.assertEqual(self.found(name="o", any_ingredient=["milk"], instructions="whisk"), ["Omelette"])

    def test_empty_lists_are_ignored(self):
        self.assertEqual(len(self.t.search(ingredient=[], any_ingredient=[], exclude_ingredient=[])), 4)

    def test_item_id(self):
        self.assertEqual(self.found(item_id=1), ["Pancakes"])
        self.assertEqual(self.found(item_id=4), ["Cheese Toast"])
        for bad in (0, 5, -1):
            with self.subTest(bad=bad):
                self.assertEqual(self.found(item_id=bad), [])

    def test_recipe_with_blank_ingredients(self):
        t = self.make("name,ingredients,instructions\nAir,,Breathe\n")
        self.assertEqual(t.search(ingredient="x"), [])
        self.assertEqual(len(t.search(exclude_ingredient="x")), 1)


if __name__ == "__main__":
    unittest.main()
