import json
import csv
from pathlib import Path


# Keep your existing 20 combined recipes here
expected_recipes = [
    {
        "name": "Spaghetti Bolognese",
        "ingredients": [
            "spaghetti",
            "ground beef",
            "tomatoes",
            "onion",
            "garlic",
            "olive oil",
            "Italian herbs"
        ]
    },
    {
        "name": "Chicken Curry",
        "ingredients": [
            "chicken",
            "onion",
            "garlic",
            "curry powder",
            "coconut milk",
            "tomatoes",
            "oil"
        ]
    }

    # Keep the rest of your recipes here
]


def normalize_items(items):
    return {
        item.strip().lower()
        for item in items
    }


def ingredients_match(expected_ingredients, json_ingredients):
    expected = normalize_items(expected_ingredients)
    actual = normalize_items(json_ingredients)

    # Allows recipes.json to contain fewer ingredients
    # as long as all of them are valid ingredients.
    return actual.issubset(expected) and len(actual) > 0


def create_recipe_results():
    folder = Path(__file__).resolve().parent
    recipes_file = folder / "recipes.json"
    results_file = folder / "recipe_results.csv"

    _accept_list = []
    _reject_list = []

    if not recipes_file.exists():
        return {
            "error": f"Could not find {recipes_file}"
        }

    with open(recipes_file, "r", encoding="utf-8") as file:
        recipes_from_json = json.load(file)

    for expected_recipe in expected_recipes:
        expected_name = expected_recipe["name"]
        expected_ingredients = expected_recipe["ingredients"]

        json_recipe = None

        for recipe in recipes_from_json:
            if recipe.get("name", "").strip().lower() == expected_name.lower():
                json_recipe = recipe
                break

        if json_recipe is None:
            _reject_list.append({
                "name": expected_name,
                "reason": "Recipe not found in recipes.json"
            })
            continue

        if ingredients_match(
            expected_ingredients,
            json_recipe.get("ingredients", [])
        ):
            _accept_list.append({
                "name": json_recipe["name"],
                "ingredients": ", ".join(
                    json_recipe.get("ingredients", [])
                ),
                "instructions": " ".join(
                    json_recipe.get("instructions", [])
                )
            })
        else:
            _reject_list.append({
                "name": json_recipe["name"],
                "reason": "Ingredients do not match"
            })

    with open(results_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "ingredients",
                "instructions"
            ]
        )

        writer.writeheader()
        writer.writerows(_accept_list)

    return {
        "accepted": len(_accept_list),
        "rejected": len(_reject_list)
    }


if __name__ == "__main__":
    create_recipe_results()

