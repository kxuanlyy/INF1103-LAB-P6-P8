#Tests for data_manager/data_manager.py (DataManager)
import os
import tempfile
import unittest

from data_manager import data_manager as dm_module
from data_manager.data_manager import DataManager
from data_manager.inventory_table import INVENTORY_COLUMNS, InventoryTable
from data_manager.recipe_table import RecipeTable

INV_HEADER = ",".join(INVENTORY_COLUMNS) + "\n"
RECIPE_HEADER = "name,ingredients,instructions\n"


class DataManagerTestCase(unittest.TestCase):
    # Always pass explicit temp paths: the defaults point into the package folder.

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = tmp.name
        self.inv = os.path.join(self.folder, "inv.csv")
        self.rec = os.path.join(self.folder, "rec.csv")

    def write(self, path, text):
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def populate(self):
        self.write(self.inv, INV_HEADER + "milk,Dairy,10/11/2026,Chilled,3,High,Milk,High,10\n")
        self.write(self.rec, RECIPE_HEADER + "Soup,\"water, salt\",Boil\n")


class TestConstants(unittest.TestCase):
    def test_default_paths_are_next_to_the_module(self):
        self.assertEqual(dm_module.BASE_DIR, os.path.dirname(os.path.abspath(dm_module.__file__)))
        self.assertEqual(dm_module.INVENTORY_PATH, os.path.join(dm_module.BASE_DIR, "food_inventory.csv"))
        self.assertEqual(dm_module.RECIPES_PATH, os.path.join(dm_module.BASE_DIR, "recipe_results.csv"))


class TestConstruction(DataManagerTestCase):
    def test_creates_both_tables_and_loads_them(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        self.assertIsInstance(d.inventory, InventoryTable)
        self.assertIsInstance(d.recipes, RecipeTable)
        self.assertEqual(d.inventory.records[0]["food"], "milk")
        self.assertEqual(d.inventory.records[0]["quantity"], 10)
        self.assertEqual(d.recipes.records[0]["name"], "Soup")

    def test_tables_use_the_given_paths(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        self.assertEqual(d.inventory.path, self.inv)
        self.assertEqual(d.recipes.path, self.rec)

    def test_missing_files_are_created_empty(self):
        with self.assertLogs("data_manager", "WARNING"):
            d = DataManager(self.inv, self.rec)
        self.assertEqual(d.inventory.records, [])
        self.assertEqual(d.recipes.records, [])
        self.assertTrue(os.path.exists(self.inv))
        self.assertTrue(os.path.exists(self.rec))

    def test_corrupt_file_does_not_stop_the_other_loading(self):
        self.write(self.inv, "wrong,header\n1,2\n")
        self.write(self.rec, RECIPE_HEADER + "Soup,water,Boil\n")
        with self.assertLogs("data_manager", "ERROR"):
            d = DataManager(self.inv, self.rec)
        self.assertEqual(d.inventory.records, [])
        self.assertEqual(len(d.recipes.records), 1)
        self.assertTrue(any(".corrupt-" in f for f in os.listdir(self.folder)))


class TestLoad(DataManagerTestCase):
    def test_reload_picks_up_changes_on_disk(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        self.write(self.rec, RECIPE_HEADER + "A,x,y\nB,x,y\n")
        d.load()
        self.assertEqual([r["name"] for r in d.recipes.records], ["A", "B"])

    def test_reload_is_in_place(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        ref = d.inventory.records
        d.load()
        self.assertIs(d.inventory.records, ref)

    def test_load_with_new_paths_switches_and_remembers(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        inv2 = os.path.join(self.folder, "inv2.csv")
        rec2 = os.path.join(self.folder, "rec2.csv")
        self.write(inv2, INV_HEADER + "rice,Grains,01/01/2027,Ambient,50,Low,,Low,20\n")
        self.write(rec2, RECIPE_HEADER + "Rice bowl,rice,Cook\n")
        d.load(inventory_path=inv2, recipes_path=rec2)
        self.assertEqual(d.inventory.path, inv2)
        self.assertEqual(d.recipes.path, rec2)
        self.assertEqual(d.inventory.records[0]["food"], "rice")
        self.assertEqual(d.recipes.records[0]["name"], "Rice bowl")
        d.save_all()                                              # saves go to the new files
        with open(inv2, encoding="utf-8") as f:
            self.assertIn("rice", f.read())

    def test_load_with_one_new_path_keeps_the_other(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        rec2 = os.path.join(self.folder, "rec2.csv")
        self.write(rec2, RECIPE_HEADER + "Z,x,y\n")
        d.load(recipes_path=rec2)
        self.assertEqual(d.inventory.path, self.inv)
        self.assertEqual(d.recipes.path, rec2)
        self.assertEqual(d.recipes.records[0]["name"], "Z")


class TestSaveAll(DataManagerTestCase):
    def test_writes_both_files(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        d.inventory.records[0]["quantity"] = 77
        d.recipes.records[0]["name"] = "Stew"
        d.save_all()
        again = DataManager(self.inv, self.rec)
        self.assertEqual(again.inventory.records[0]["quantity"], 77)
        self.assertEqual(again.recipes.records[0]["name"], "Stew")

    def test_save_all_recreates_deleted_files(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        os.remove(self.inv)
        os.remove(self.rec)
        d.save_all()
        self.assertTrue(os.path.exists(self.inv))
        self.assertTrue(os.path.exists(self.rec))

    def test_changes_made_through_the_tables_are_saved(self):
        self.populate()
        d = DataManager(self.inv, self.rec)
        d.inventory.add("Tea", "Drinks", "01/01/2030", "Ambient", 300, "Low")
        d.recipes.add("Toast", "bread", "Toast it")
        again = DataManager(self.inv, self.rec)
        self.assertEqual(len(again.inventory.records), 2)
        self.assertEqual(len(again.recipes.records), 2)


if __name__ == "__main__":
    unittest.main()
