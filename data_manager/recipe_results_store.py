import csv
import json
from pathlib import Path
from typing import Optional, Union

# Created and writing files for accepted and rejected recipes
class RecipeResultsStore:
    # Reads accepted_recipe.json / recipes.json and writes recipe_results.csv and
    # rejected.txt. By default everything lives next to this file

    def __init__(self, folder: Optional[Union[str, Path]] = None):
        self.folder = Path(folder) if folder is not None else Path(__file__).resolve().parent

    def get_folder_path(self):
        return self.folder

    def load_json_files(self):
        folder = self.get_folder_path()
        expected_file = folder / "accepted_recipe.json"
        recipes_file = folder / "recipes.json"

        # Check for input files
        if not expected_file.exists():
            return {"error": f"Could not find {expected_file}"}

        if not recipes_file.exists():
            return {"error": f"Could not find {recipes_file}"}

        # Load JSON files
        with open(expected_file, "r", encoding="utf-8") as file:
            accepted_recipes = json.load(file)

        with open(recipes_file, "r", encoding="utf-8") as file:
            recipes_from_json = json.load(file)

        return {
            "accepted_recipes": accepted_recipes,
            "recipes_from_json": recipes_from_json,
        }

    def save_results(self, accept_list, reject_list):
        folder = self.get_folder_path()
        results_file = folder / "recipe_results.csv"
        rejected_file = folder / "rejected.txt"

        # Write accepted recipes to recipe_results.csv
        with open(results_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=["name", "ingredients", "instructions"]
            )
            writer.writeheader()
            writer.writerows(accept_list)

        # Write rejected recipes to rejected.txt
        with open(rejected_file, "w", encoding="utf-8") as file:
            for rejected in reject_list:
                file.write(
                    f"Rejected recipe: {rejected['name']} | Reason: {rejected['reason']}\n"
                )
            file.write(f"\nTotal rejected recipes: {len(reject_list)}\n")

        return results_file.name, rejected_file.name
