# logic_manager.py
from data_manager import load_json_files, save_results


def normalize_items(items):
    # Normalize and lowercase list of items for consistent comparison
    return {item.strip().lower() for item in items}


def ingredients_match(expected_ingredients, json_ingredients):
    # Check if actual ingredients match expected standard templates using word overlaps
    expected = normalize_items(expected_ingredients)
    actual = normalize_items(json_ingredients)

    if not actual:
        return False

    matched_count = 0
    for exp in expected:
        exp_words = set(exp.split())
        found = False
        for act in actual:
            act_words = set(act.split())
            if exp_words.intersection(act_words):
                found = True
                break
        if found:
            matched_count += 1

    # Accept if at least 60% of template ingredients match
    match_percentage = matched_count / len(expected)
    return match_percentage >= 0.6


def evaluate_recipes(accepted_recipes, recipes_from_json):
    # Process and evaluate each incoming recipe against reference templates
    accept_list = []
    reject_list = []

    for json_recipe in recipes_from_json:
        json_name = json_recipe.get("name", "").strip()
        json_words = set(json_name.lower().split())

        matched_expected_recipe = None
        for expected in accepted_recipes:
            expected_name = expected.get("name", "").strip()
            expected_words = set(expected_name.lower().split())
            
            if json_words and expected_words and json_words.intersection(expected_words):
                matched_expected_recipe = expected
                break

        # Rejection Rule 1: Recipe name not found in accepted templates
        if matched_expected_recipe is None:
            reason_text = "Recipe name not found in accepted_recipe.json"
            reject_list.append(
                {
                    "name": json_name or "Unknown Recipe",
                    "reason": reason_text,
                }
            )
            continue

        # Rejection Rule 2: Ingredients do not meet standard criteria
        expected_ingredients = matched_expected_recipe.get("ingredients", [])
        actual_ingredients = json_recipe.get("ingredients", [])

        if ingredients_match(expected_ingredients, actual_ingredients):
            accept_list.append(
                {
                    "name": json_recipe.get("name", ""),
                    "ingredients": ", ".join(actual_ingredients),
                    "instructions": " ".join(json_recipe.get("instructions", [])),
                }
            )
        else:
            reason_text = "Ingredients do not match valid accepted criteria"
            reject_list.append(
                {
                    "name": json_name,
                    "reason": reason_text,
                }
            )

    return accept_list, reject_list


def create_recipe_results():
    # Load data via data_manager
    data = load_json_files()
    if isinstance(data, dict) and "error" in data:
        return data

    accepted_recipes = data["accepted_recipes"]
    recipes_from_json = data["recipes_from_json"]

    # Check if recipes list is empty
    if not recipes_from_json:
        return {"error": "recipes.json is empty"}

    # Evaluate all recipes utilizing pure business logic
    accept_list, reject_list = evaluate_recipes(accepted_recipes, recipes_from_json)

    # Save results via data_manager
    save_results(accept_list, reject_list)

    return {"accepted": len(accept_list), "rejected": len(reject_list)}