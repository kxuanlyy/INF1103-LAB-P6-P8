import csv
import json
from pathlib import Path


def normalize_items(items):
    return {item.strip().lower() for item in items}


def ingredients_match(expected_ingredients, json_ingredients):
    expected = normalize_items(expected_ingredients)
    actual = normalize_items(json_ingredients)

    # Allows recipes.json to contain fewer ingredients
    # as long as all of them are valid ingredients.
    return actual.issubset(expected) and len(actual) > 0


def create_recipe_results():
    folder = Path(__file__).resolve().parent

    # File paths
    expected_file = folder / "accepted_recipe.json"
    recipes_file = folder / "recipes.json"
    results_file = folder / "recipe_results.csv"
    rejected_file = folder / "rejected.txt"

    _accept_list = []
    _reject_list = []

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

    # Loop through EACH recipe inside recipes.json
    for json_recipe in recipes_from_json:
        json_name = json_recipe.get("name", "").strip()
        json_words = set(json_name.lower().split())

        # Find matching recipe in accepted_recipe.json by checking if any word/part overlaps
        matched_expected_recipe = None
        for expected in accepted_recipes:
            expected_name = expected.get("name", "").strip()
            expected_words = set(expected_name.lower().split())
            
            # Matches if they share at least one word (e.g., "spaghetti")
            if json_words and expected_words and json_words.intersection(expected_words):
                matched_expected_recipe = expected
                break

        # Rejection Rule 1: No overlapping words found in accepted_recipe.json
        if matched_expected_recipe is None:
            _reject_list.append(
                {
                    "name": json_name or "Unknown Recipe",
                    "reason": "Recipe name not found in accepted_recipe.json",
                }
            )
            continue

        # Rejection Rule 2: Ingredients do not match accepted recipe standards
        expected_ingredients = matched_expected_recipe.get("ingredients", [])
        actual_ingredients = json_recipe.get("ingredients", [])

        if ingredients_match(expected_ingredients, actual_ingredients):
            _accept_list.append(
                {
                    "name": json_recipe.get("name", ""),
                    "ingredients": ", ".join(actual_ingredients),
                    "instructions": " ".join(
                        json_recipe.get("instructions", [])
                    ),
                }
            )
        else:
            _reject_list.append(
                {
                    "name": json_name,
                    "reason": "Ingredients do not match valid accepted criteria",
                }
            )

    # Write accepted recipes to recipe_results.csv
    with open(results_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=["name", "ingredients", "instructions"]
        )
        writer.writeheader()
        writer.writerows(_accept_list)

    # Write rejected recipes to rejected.txt
    with open(rejected_file, "w", encoding="utf-8") as file:
        for rejected in _reject_list:
            file.write(
                f"Rejected recipe: {rejected['name']} | Reason: {rejected['reason']}\n"
            )
        file.write(f"\nTotal rejected recipes: {len(_reject_list)}\n")

    print(f"Accepted recipes written to {results_file}")
    print(f"Rejected recipes written to {rejected_file}")

    return {"accepted": len(_accept_list), "rejected": len(_reject_list)}


if __name__ == "__main__":
    create_recipe_results()