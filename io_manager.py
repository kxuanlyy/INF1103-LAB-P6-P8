from data_manager import load_json_files, save_results
from logic_manager import evaluate_recipes
from datetime import datetime
import textwrap
import data_manager as dm
from ai_module.ai_manager import RECIPES_PATH, suggest_recipes

# Functions

def print_current_inventory(extracted_items, ids=None):
    # ids: optional numbers to show instead of 1, 2, 3... (search results use this
    # so each item keeps its number from the full list)
    if not extracted_items:
        print("\n[!] The inventory list is currently empty.")
        return False

    # Safely evaluate string column layout profiles based on data sizes
    max_name_len = max(len(record['food']) for record in extracted_items)
    name_col_width = max(max_name_len, 25)

    total_table_width = 4 + 3 + name_col_width + 3 + 6 + 3 + 12
    separator_line = "=" * total_table_width

    print("\n" + separator_line)
    print(f"{'No.':<4} | {'Ingredient Name':<{name_col_width}} | {'Qty':<6} | {'Expiry Date'}")
    print(separator_line)
    for x, record in zip(ids or range(1, len(extracted_items) + 1), extracted_items):
        qty = "" if record['quantity'] is None else record['quantity']
        print(f"[{x}] {record['food']:<{name_col_width}} | {str(qty):<6} | {record['use-by']}")
    print(separator_line)
    return True

def print_recipes(recipe_list, ids=None):
#    Print every recipe (dm.recipes) with its ingredients as a list and
#    its instructions word-wrapped. Returns False if there is nothing to show.

#    ids: optional numbers to show instead of 1, 2, 3... (search results use this
#    so each recipe keeps its number from the full list).
    if not recipe_list:
        print("\n[!] There are no recipes saved yet.")
        return False
 
    separator_line = "=" * 60
 
    for x, recipe in zip(ids or range(1, len(recipe_list) + 1), recipe_list):
        print("\n" + separator_line)
        print(f"[{x}] {recipe['name']}")
        print(separator_line)
 
        ingredients = [i.strip() for i in recipe['ingredients'].split(",") if i.strip()]
        print("Ingredients:")
        if ingredients:
            for ingredient in ingredients:
                print(f"  - {ingredient}")
        else:
            print("  (none listed)")
 
        print("Instructions:")
        if recipe['instructions']:
            print(textwrap.fill(recipe['instructions'], width=60,
                                initial_indent="  ", subsequent_indent="  "))
        else:
            print("  (none listed)")
    print("\n" + separator_line)
    return True


def get_validated_string(prompt_text, allow_blank=False, current_val=None):
    while True:
        suffix = f" [{current_val}]: " if current_val else ": "
        user_val = input(prompt_text + suffix).strip()

        if not user_val and current_val:
            return current_val
        if not user_val and not allow_blank:
            print("Error: This field cannot be left blank. Please enter a value.")
            continue
        return user_val if user_val else "None"

def get_validated_choice(prompt_text, valid_choices, current_val=None):
    choices_str = "/".join(valid_choices)
    while True:
        suffix = f" ({choices_str}) [{current_val}]: " if current_val else f" ({choices_str}): "
        user_val = input(prompt_text + suffix).strip()

        if not user_val and current_val:
            return current_val
        if not user_val:
            print("Error: Selection cannot be blank. Please pick one of the options.")
            continue

        matched = [c for c in valid_choices if c.lower() == user_val.lower()]
        if matched:
            return matched[0]  # Return standard capitalized version
        print(f"Error: Invalid option. You must choose one of: {choices_str}")

def get_validated_int(prompt_text, current_val=None):
    while True:
        suffix = f" [{current_val}]: " if current_val is not None else ": "
        user_val = input(prompt_text + suffix).strip()

        if not user_val and current_val is not None:
            return str(current_val)
        if not user_val:
            print("Error: This number field cannot be left blank.")
            continue
        if user_val.isascii() and user_val.isdigit():
            return user_val
        print("Error: Invalid entry. Please enter a positive whole number or 0.")

def get_validated_date(prompt_text, current_val=None):
    while True:
        suffix = f" [{current_val}]: " if current_val else ": "
        user_val = input(prompt_text + suffix).strip()
        
        if not user_val and current_val:
            return current_val
        if not user_val:
            print("Error: Date cannot be blank. Please enter a valid date.")
            continue
            
        try:
            parsed_date = datetime.strptime(user_val, "%d/%m/%Y")
            
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if parsed_date < today:
                print("Error: The expiration date cannot be in the past. Please enter a current or future date.")
                continue
                
            return f"{parsed_date.day}/{parsed_date.month}/{parsed_date.year}"

        except ValueError:
            print("Error: Invalid date format. Please use DD/MM/YYYY (e.g., 9/26/2026).")

def prompt_for_ingredient_details(existing_item=None):
#    Ask for every field and return them as keyword arguments for
#    dm.add_inventory_item() / dm.update_inventory_item().

#    existing_item is a record from dm.inventory (CSV column names as keys).
    print("\n--- ENTER INGREDIENT DETAILS ---")
    if existing_item:
        print("Press Enter to keep current bracketed values.")

    # Validated Inputs (Cannot be blank)
    item = get_validated_string("Ingredient Name", allow_blank=False, current_val=existing_item.get('food') if existing_item else None)

    valid_categories = ["Dairy", "Meat & Seafood", "Fresh Produce", "Bakery", "Pantry", "Other"]
    category = get_validated_choice("Category", valid_categories, current_val=existing_item.get('food_category') if existing_item else None)

    use_by = get_validated_date("Use-By Date (DD/MM/YYYY)", current_val=existing_item.get('use-by') if existing_item else None)

    valid_storage = ["Chilled", "Frozen", "Ambient"]
    storage = get_validated_choice("Storage Condition", valid_storage, current_val=existing_item.get('storage condition') if existing_item else None)

    valid_risks = ["Low", "Medium", "High"]
    risk_lvl = get_validated_choice("Waste Risk Level", valid_risks, current_val=existing_item.get('waste_risk_level') if existing_item else None)


    allergens = get_validated_string("Allergen Info (or press Enter for None)", allow_blank=True, current_val=existing_item.get('allergen info') if existing_item else None)
    if allergens.lower() == "none":
        allergens = "None"  # data_manager stores "no allergens" as an empty cell

    demand = get_validated_choice("Demand Level", valid_risks, current_val=existing_item.get('demand level').capitalize() if existing_item else None)
    quantity = get_validated_int("Stock Quantity", current_val=existing_item.get('quantity') if existing_item else None)

    # auto calculate date to expiry
    today = datetime.today()
    expiry_date = datetime.strptime(use_by, "%d/%m/%Y")

    calculated_days = (expiry_date - today).days + 1

    if calculated_days < 0:
        calculated_days = 0

    print(f"-> Calculated Days to Expiry: {calculated_days} day(s) remaining.")

    return {
        "food": item,
        "food_category": category,
        "use_by": use_by,
        "storage_condition": storage,
        "days_to_expiry": calculated_days,
        "waste_risk_level": risk_lvl,
        "allergen_info": allergens,
        "demand_level": demand,
        "quantity": int(quantity),
    }

def handle_edit_menu():

    while True:
        print("\n------------------------------")
        print("    2. EDIT INVENTORY LIST       ")
        print("------------------------------")
        print("  a. Add Food")
        print("  b. Remove Food")
        print("  c. Edit Food")
        print("  d. Back to Main Menu")
        print("------------------------------")

        sub_choice = input("Select an option (a-d): ").strip().lower()

        # a. Add Items
        if sub_choice == 'a':
            print("\nCurrent Inventory before adding:")
            print_current_inventory(dm.inventory)

            details = prompt_for_ingredient_details()
            try:
                dm.add_inventory_item(**details)
            except (OSError, ValueError) as e:
                print(f"\nError: Failed to add '{details['food']}': {e}")
            else:
                print(f"\nSuccess: '{details['food']}' successfully added.")

                print("\nUpdated Inventory after additions:")
                print_current_inventory(dm.inventory)

        # b. Remove Items
        elif sub_choice == 'b':
            print("\n--- REMOVE FOOD ITEM ---")
            if not print_current_inventory(dm.inventory):
                continue

            remove_choice = input(f"Enter the item number to remove (1-{len(dm.inventory)}): ").strip()
            if remove_choice.isdigit() and 1 <= int(remove_choice) <= len(dm.inventory):
                try:
                    removed = dm.delete_inventory_item(int(remove_choice) - 1)
                except OSError as e:
                    print(f"\nError: Failed to remove the item: {e}")
                else:
                    print(f"\n[SUCCESS] Removed '{removed['food']}' from the list.")

                    print("\nUpdated Inventory after item removal:")
                    print_current_inventory(dm.inventory)

            else:
                print("\nError: Invalid selection. No items were removed.")

        # c. Edit Item
        elif sub_choice == 'c':
            if not print_current_inventory(dm.inventory):
                continue

            update_choice = input(f"Enter the item number to modify (1-{len(dm.inventory)}): ").strip()
            if update_choice.isdigit() and 1 <= int(update_choice) <= len(dm.inventory):
                target_idx = int(update_choice) - 1
                current_data = dm.inventory[target_idx]

                print(f"\nModifying details for: {current_data['food']}")
                print("Press Enter to keep current bracketed values.")

                details = prompt_for_ingredient_details(current_data)
                try:
                    dm.update_inventory_item(target_idx, **details)
                except (OSError, ValueError) as e:
                    print(f"\nError: Failed to update '{current_data['food']}': {e}")
                else:
                    print(f"\nSuccess: Updated data for '{details['food']}'.")
            else:
                print("\nError: Invalid selection. Update aborted.")

        # d. Return to Main Menu
        elif sub_choice == 'd':
            print("\nReturning to Main Menu...")
            break
        else:
            print("\nError: Please enter a, b, c, or d.")

def get_optional_text(prompt_text):
#   Ask for text; pressing Enter skips the filter (returns None).
    return input(prompt_text + " (Enter to skip): ").strip() or None

def get_optional_int(prompt_text):
#   Ask for a whole number >= 0; pressing Enter skips the filter (returns None).
    while True:
        user_val = input(prompt_text + " (Enter to skip): ").strip()
        if not user_val:
            return None
        if user_val.isascii() and user_val.isdigit():
            return int(user_val)
        print("Error: Please enter a whole number (0 or more), or press Enter to skip.")

def get_optional_list(prompt_text):
#   Ask for a comma-separated list; pressing Enter skips the filter (returns None).
    raw = input(prompt_text + " (comma-separated, Enter to skip): ").strip()
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or None

def ids_of(table, records):
#   The numbers (as shown in the full list) of the records a search returned.
    position = {id(record): n for n, record in enumerate(table, start=1)}
    return [position[id(record)] for record in records]

def prompt_for_inventory_filters():
#    Ask for the inventory search fields (Enter skips one) and return keyword
#    arguments for dm.search_inventory().
    print("\n--- SEARCH INVENTORY ---")
    print("Leave a field blank to skip it. If you fill in both, both must match.")

    return {
        "food": get_optional_text("Food name contains"),
        "item_id": get_optional_int("ID (the number shown in the inventory list)"),
    }

def prompt_for_recipe_filters():
#Ask for the recipe search fields (Enter skips one) and return keyword
#arguments for dm.search_recipes().
    print("\n--- SEARCH RECIPES ---")
    print("Leave a field blank to skip it. If you fill in both, both must match.")

    return {
        "ingredient": get_optional_list("Ingredient (a recipe must have all you list)"),
        "item_id": get_optional_int("ID (the number shown in the recipe list)"),
    }

def print_item_card(user_choice):
#   Show one inventory item as a card. user_choice is the ID the user typed
#   (the item's number in the full inventory list). Returns True if a card was shown.
    extracted_items = dm.inventory

    if not extracted_items:
        print("\n[!] The inventory list is currently empty.")
        return False

    # Validate input and display the item card
    if user_choice.isascii() and user_choice.isdigit():
        choice_num = int(user_choice)
        if 1 <= choice_num <= len(extracted_items):
            match = extracted_items[choice_num - 1]
            quantity = "Unknown" if match['quantity'] is None else match['quantity']
            days_left = "Unknown" if match['days_to_expiry'] is None else f"{match['days_to_expiry']} day(s) remaining"

            print("\n==================================================")
            print(f"          FOOD ID: [{choice_num}]          ")
            print("==================================================")
            print(f" Item Name:         {match['food']}")
            print(f" Category:          {match['food_category']}")
            print(f" Stock Quantity:    {quantity}")
            print(f" Use-By Date:       {match['use-by']}")
            print(f" Days to Expiry:    {days_left}")
            print(f" Storage Type:      {match['storage condition']}")
            print(f" Waste Risk Level:  {match['waste_risk_level']}")
            print(f" Demand Level:      {match['demand level'].capitalize()}")
            print(f" Allergen Info:     {match['allergen info'] or 'None'}")
            print("==================================================")
            return True

    print(f"\nError: Invalid selection. Please type a valid number between 1 and {len(extracted_items)}.")
    return False

def print_recipe_card(user_choice):
#   Show one recipe as a card. user_choice is the ID the user typed
#   (the recipe's number in the full recipe list). Returns True if a card was shown.
    recipe_list = dm.recipes

    if not recipe_list:
        print("\n[!] There are no recipes saved yet.")
        return False

    # Validate input and display the recipe card
    if user_choice.isascii() and user_choice.isdigit():
        choice_num = int(user_choice)
        if 1 <= choice_num <= len(recipe_list):
            match = recipe_list[choice_num - 1]
            ingredients = [i.strip() for i in match['ingredients'].split(",") if i.strip()]

            print("\n==================================================")
            print(f"         RECIPE ID: [{choice_num}]          ")
            print("==================================================")
            print(f" Recipe Name:       {match['name']}")
            print(" Ingredients:")
            if ingredients:
                for ingredient in ingredients:
                    print(f"   - {ingredient}")
            else:
                print("   (none listed)")
            print(" Instructions:")
            if match['instructions']:
                print(textwrap.fill(match['instructions'], width=50,
                                    initial_indent="   ", subsequent_indent="   "))
            else:
                print("   (none listed)")
            print("==================================================")
            return True

    print(f"\nError: Invalid selection. Please type a valid number between 1 and {len(recipe_list)}.")
    return False

def run_inventory_search():
#   Ask for name/ID, search dm.inventory and print the matches.
    filters = prompt_for_inventory_filters()
    results = dm.search_inventory(**filters)

    if results:
        print(f"\nFound {len(results)} matching item(s):")
        print_current_inventory(results, ids_of(dm.inventory, results))
    else:
        print("\nNo inventory items matched that name/ID.")

def handle_inventory_search():
#   Main menu option 2: search the inventory, then offer a small menu to
#   re-search, show an item card by ID, or go back to the main menu.
    run_inventory_search()

    while True:
        print("\n------------------------------")
        print("    INVENTORY SEARCH MENU       ")
        print("------------------------------")
        print("  1. Re-search the inventory list")
        print("  2. Type an ID to show the item card")
        print("  3. Back to Main Menu")
        print("------------------------------")

        search_choice = input("Select an option (1-3): ").strip()

        if search_choice == "1":
            run_inventory_search()

        elif search_choice == "2":
            user_choice = input(f"Enter the item ID to show (1-{len(dm.inventory)}): ").strip()
            print_item_card(user_choice)

        elif search_choice == "3":
            print("\nReturning to Main Menu...")
            break
        else:
            print("\nError: Please enter 1, 2, or 3.")

def run_recipe_search():
#   Ask for ingredient/ID, search dm.recipes and print the matches.
    filters = prompt_for_recipe_filters()
    results = dm.search_recipes(**filters)

    if results:
        print(f"\nFound {len(results)} matching recipe(s):")
        print_recipes(results, ids_of(dm.recipes, results))
    else:
        print("\nNo recipes matched that ingredient/ID.")

def handle_recipe_search():
#   Main menu option 7: search the recipes, then offer a small menu to
#   re-search, show a recipe card by ID, or go back to the main menu.
    run_recipe_search()

    while True:
        print("\n------------------------------")
        print("    RECIPE SEARCH MENU          ")
        print("------------------------------")
        print("  1. Re-search the recipe list")
        print("  2. Type an ID to show the recipe card")
        print("  3. Back to Main Menu")
        print("------------------------------")

        search_choice = input("Select an option (1-3): ").strip()

        if search_choice == "1":
            run_recipe_search()

        elif search_choice == "2":
            user_choice = input(f"Enter the recipe ID to show (1-{len(dm.recipes)}): ").strip()
            print_recipe_card(user_choice)

        elif search_choice == "3":
            print("\nReturning to Main Menu...")
            break
        else:
            print("\nError: Please enter 1, 2, or 3.")

def process_item_for_ai(extracted_items):

    if not extracted_items:
        print("Error: No inventory data available to process.")
        return None

    # User Choice Selection Loop
    selected_record = None
    while True:
        user_choice = input(f"Enter the item number you want to check (1 to {len(extracted_items)}): ").strip()

        if user_choice.isdigit():
            choice_num = int(user_choice)
            if 1 <= choice_num <= len(extracted_items):
                selected_record = extracted_items[choice_num - 1]
                print(f"\nSelected Item: {selected_record['food']}")
                break

        print(f"[INVALID INPUT] Please type a whole number between 1 and {len(extracted_items)}.")

    # Processing the Chosen Item and Staff Observations
    print("\n" + "="*55)
    print(f"PROCESSING INVENTORY ITEM: {selected_record['food']}")
    print(f"Expiry: {selected_record['use-by']} | Quantity: {selected_record['quantity']} | Risk Level: {selected_record['waste_risk_level']} ")
    print("="*55)

    # Staff Observations
    staff_notes = input("Enter any quality observations (or press Enter to skip): ").strip()
    if not staff_notes:
        staff_notes = "No structural physical defects observed"

    # combined payload dictionary
    ai_payload = {
        "item": selected_record["food"],
        "category": selected_record["food_category"],
        "use_by_date": selected_record["use-by"],
        "file_storage_condition": selected_record["storage condition"],
        "days_to_expiry": selected_record["days_to_expiry"],
        "waste_risk_level": selected_record["waste_risk_level"],
        "allergen_info": selected_record["allergen info"] or "None",
        "demand_level": selected_record["demand level"].lower(),
        "quantity":  selected_record["quantity"],
        "staff_observations": staff_notes
    }

    return ai_payload

def print_ai_result(result):
    # Display the validated assessment and recipe preparation steps.
    print("\n==================================================")
    print(f"          AI ASSESSMENT FOR: {result['stock_item']['name'].upper()}          ")
    print("==================================================")
    print(f" Item Name:         {result['stock_item']['name']}")
    print(f" Category:          {result['category']}")
    print(f" Demand Level:      {result['demand_level'].capitalize()}")
    print(f" Expiry Urgency:    {result['expiry_urgency'].capitalize()}")
    print(f" Spoilage Risk:     {result['spoilage_risk'].capitalize()}")
    print(f" Suitability Score: {result['suitability_score']}/100")
    print(f" Confidence:        {result['confidence']:.0%}")
    print(f" Allergen Uncertain: {result['allergen_uncertain']}")
    print(f" Storage Uncertain:  {result['storage_uncertain']}")
    print(f" Reason:            {result['reason']}")
    print("==================================================")
    if not result['recipes']:
        print("No recipes suggested for this item. See the assessment reason above.")
    for number, recipe in enumerate(result['recipes'], start=1):
        print("\n==================================================")
        print(f"          RECIPE {number}: {recipe['name'].upper()}          ")
        print("==================================================")
        print(" Ingredients:       " + ", ".join(recipe['ingredients']))
        print(" Preparation Steps:")
        for step_number, instruction in enumerate(recipe['instructions'], start=1):
            print(f"  {step_number}. {instruction}")
        print("==================================================")
    print(f"\nRecipes saved to: {RECIPES_PATH}")


# Main Program starts here
# (data_manager loads food_inventory.csv and recipe_results.csv when it is imported;
#  the live data is dm.inventory and dm.recipes)


def main(today=None, client=None):
    while True:
        print("\n=================================")
        print("          MAIN MENU              ")
        print("=================================")
        print(" 1. View current inventory stock")
        print(" 2. Search in inventory")
        print(" 3. Edit items data")
        print(" 4. Ask AI")
        print(" 5. Process valid recipes")
        print(" 6. View recipes")
        print(" 7. Search recipes")
        print(" 8. Exit")
        print("=================================")

        main_choice = input("Select an option (1-8): ").strip()
        if main_choice == "1":
            print_current_inventory(dm.inventory)

        elif main_choice == "2":
            handle_inventory_search()

        elif main_choice == "3":
            print_current_inventory(dm.inventory)
            handle_edit_menu()

        elif main_choice == "4":
            if not print_current_inventory(dm.inventory):
                continue
            payload = process_item_for_ai(dm.inventory)
            print("\nAsking AI... please wait.")
            last_result, last_error = suggest_recipes(payload, today=today, client=client)
            if last_error:
                print("Assessment failed:", last_error)
            else:
                print_ai_result(last_result)
                
        elif main_choice == "5":
            print("\nProcessing recipes based on accepted_recipe.json...")
            run_recipe_processor()  # Calls the IO manager processor directly
            dm.load()

        elif main_choice == "6":
            dm.load()
            print_recipes(dm.recipes)

        elif main_choice == "7":
            dm.load()
            handle_recipe_search()

        elif main_choice == "8":
            print("\nExiting program. Goodbye!")
            break
        else:
            print("\nError: Please select a number between 1 and 8.")



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


def run_recipe_processor():
    # Print welcome header banner
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

    print(f"{Colors.BOLD}Processing recipes...{Colors.ENDC}\n")

    # Evaluate recipes using logic_manager
    _accept_list = []
    _reject_list = []

    # Custom real-time print feedback loop leveraging logic evaluations
    for json_recipe in recipes_from_json:
        json_name = json_recipe.get("name", "").strip()
        
        # Run evaluation for individual item to display step-by-step terminal UI feedback
        single_accept, single_reject = evaluate_recipes(accepted_recipes, [json_recipe])
        
        if single_accept:
            _accept_list.append(single_accept[0])
            matched_name = single_accept[0]["name"]
            print(f"  {Colors.GREEN}✔ ACCEPTED:{Colors.ENDC} {json_name} (Matched template)")
        else:
            rejected_item = single_reject[0]
            _reject_list.append(rejected_item)
            print(f"  {Colors.FAIL}✖ REJECTED:{Colors.ENDC} {rejected_item['name']} -> {Colors.WARNING}{rejected_item['reason']}{Colors.ENDC}")

    # Save results via data_manager
    results_filename, rejected_filename = save_results(_accept_list, _reject_list)

    # Render summary report block
    print(f"\n{Colors.CYAN}{'='*50}")
    print(f"                SUMMARY REPORT")
    print(f"{'='*50}{Colors.ENDC}")
    print(f"  {Colors.GREEN}✔ Accepted Recipes :{Colors.ENDC} {len(_accept_list)}")
    print(f"  {Colors.FAIL}✖ Rejected Recipes :{Colors.ENDC} {len(_reject_list)}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")
    print(f"  📁 Accepted Recipes saved to : {Colors.BOLD}{results_filename}{Colors.ENDC}")
    print(f"  📁 Rejected Recipes saved to : {Colors.BOLD}{rejected_filename}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*50}\n{Colors.ENDC}")

    return {"accepted": len(_accept_list), "rejected": len(_reject_list)}