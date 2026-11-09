import os
from typing import Optional

from inventory_table import InventoryTable
from recipe_table import RecipeTable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_PATH = os.path.join(BASE_DIR, "food_inventory.csv")
RECIPES_PATH = os.path.join(BASE_DIR, "recipe_results.csv")


# --------------------------------------------------------------------------- #
# The manager: owns both tables
# --------------------------------------------------------------------------- #
class DataManager:
    # Holds the inventory table and the recipe table, and loads both when created.

    def __init__(self, inventory_path: str = INVENTORY_PATH, recipes_path: str = RECIPES_PATH):
        self.inventory = InventoryTable(inventory_path)
        self.recipes = RecipeTable(recipes_path)
        self.load()

    def load(self, inventory_path: Optional[str] = None, recipes_path: Optional[str] = None) -> None:
        # (Re)load both CSVs from disk. Numeric columns become ints.
        #
        # Pass paths to switch to different files; they are remembered for saves.

        if inventory_path is not None:
            self.inventory.path = inventory_path
        if recipes_path is not None:
            self.recipes.path = recipes_path
        self.inventory.load()
        self.recipes.load()

    def save_all(self) -> None:
        self.inventory.save()
        self.recipes.save()
