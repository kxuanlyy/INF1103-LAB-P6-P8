from data_manager import load_json_files, save_results


# ANSI Color Codes for terminal styling
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def normalize_items(items):
    return {item.strip().lower() for item in items}


def ingredients_match(expected_ingredients, json_ingredients):
    expected = normalize_items(expected_ingredients)
    actual = normalize_items(json_ingredients)

    if not actual:
        return False

    # Flexible matching: Check if each expected ingredient finds a match 
    # based on overlapping words (handles plurals, minor phrasing differences)
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

    # Accepts the recipe if at least 60% of the template ingredients match (adjustable)
    match_percentage = matched_count / len(expected)
    return match_percentage >= 0.6


def create_recipe_results():
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}")
    print(f"       🍳 RECIPE VALIDATION PROCESSOR 🍳")
    print(f"{'='*50}{Colors.ENDC}\n")

    # Load data via data_manager
    data = load_json_files()
    if isinstance(data, dict) and "error" in data:
        print(f"{Colors.FAIL}[ERROR] {data['error']}{Colors.ENDC}")
        return data

    accepted_recipes = data["accepted_recipes"]
    recipes_from_json = data["recipes_from_json"]

    # Check if recipes.json is empty
    if not recipes_from_json:
        print(f"{Colors.FAIL}[ERROR] recipes.json is empty or contains no recipes!{Colors.ENDC}\n")
        return {"error": "recipes.json is empty"}

    print(f"{Colors.BOLD}Processing recipes...{Colors.ENDC}\n")

    _accept_list = []
    _reject_list = []

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
            reason_text = "Recipe name not found in accepted_recipe.json"
            _reject_list.append(
                {
                    "name": json_name or "Unknown Recipe",
                    "reason": reason_text,
                }
            )
            print(f"  {Colors.FAIL}✖ REJECTED:{Colors.ENDC} {json_name or 'Unknown Recipe'} -> {Colors.WARNING}{reason_text}{Colors.ENDC}")
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
            print(f"  {Colors.GREEN}✔ ACCEPTED:{Colors.ENDC} {json_name} (Matched with template: '{matched_expected_recipe.get('name')}')")
        else:
            reason_text = "Ingredients do not match valid accepted criteria"
            _reject_list.append(
                {
                    "name": json_name,
                    "reason": reason_text,
                }
            )
            print(f"  {Colors.FAIL}✖ REJECTED:{Colors.ENDC} {json_name} -> {Colors.WARNING}{reason_text}{Colors.ENDC}")

    # Save results via data_manager
    results_filename, rejected_filename = save_results(_accept_list, _reject_list)

    # Beautiful Summary Box
    print(f"\n{Colors.CYAN}{'='*50}")
    print(f"                 SUMMARY REPORT")
    print(f"{'='*50}{Colors.ENDC}")
    print(f"  {Colors.GREEN}✔ Accepted Recipes :{Colors.ENDC} {len(_accept_list)}")
    print(f"  {Colors.FAIL}✖ Rejected Recipes :{Colors.ENDC} {len(_reject_list)}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")
    print(f"  📁 Accepted Recipes saved to : {Colors.BOLD}{results_filename}{Colors.ENDC}")
    print(f"  📁 Rejected Recipes saved to : {Colors.BOLD}{rejected_filename}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*50}\n{Colors.ENDC}")

    return {"accepted": len(_accept_list), "rejected": len(_reject_list)}


if __name__ == "__main__":
    create_recipe_results()