import textwrap

from io_manager.user_interface import UserInterface
from io_manager.colors import Colors


class ConsoleView(UserInterface):
    #Handles only displaying text to the screen (Output)

    def display_main_menu(self) -> None:
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

    def display_edit_menu(self) -> None:
        print("\n------------------------------")
        print("    2. EDIT INVENTORY LIST       ")
        print("------------------------------")
        print("  a. Add Food")
        print("  b. Remove Food")
        print("  c. Edit Food")
        print("  d. Back to Main Menu")
        print("------------------------------")

    def display_inventory_search_menu(self) -> None:
        print("\n------------------------------")
        print("   INVENTORY SEARCH ACTIONS   ")
        print("------------------------------")
        print("  1. Search again")
        print("  2. View specific food item card")
        print("  3. Back to Main Menu")
        print("------------------------------")

    def display_recipe_search_menu(self) -> None:
        print("\n------------------------------")
        print("     RECIPE SEARCH ACTIONS    ")
        print("------------------------------")
        print("  1. Search again")
        print("  2. View specific recipe card")
        print("  3. Back to Main Menu")
        print("------------------------------")

    def print_current_inventory(self, extracted_items, ids=None) -> bool:
        if not extracted_items:
            print("\n[!] The inventory list is currently empty.")
            return False

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

    def print_recipes(self, recipe_list, ids=None) -> bool:
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

    def print_item_card(self, choice_num, match) -> None:
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

    def print_recipe_card(self, choice_num, match) -> None:
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

    def print_ai_result(self, result, recipes_path) -> None:
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
        print(f"\nRecipes saved to: {recipes_path}")

    def print_recipe_processor_header(self) -> None:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}")
        print(f"       🍳 RECIPE VALIDATION PROCESSOR 🍳")
        print(f"{'='*50}{Colors.ENDC}\n")
        print(f"{Colors.BOLD}Processing recipes...{Colors.ENDC}\n")

    def print_recipe_processor_step(self, accept_flag, name, reason=None) -> None:
        if accept_flag:
            print(f"  {Colors.GREEN}✔ ACCEPTED:{Colors.ENDC} {name} (Matched template)")
        else:
            print(f"  {Colors.FAIL}✖ REJECTED:{Colors.ENDC} {name} -> {Colors.WARNING}{reason}{Colors.ENDC}")

    def print_recipe_processor_summary(self, accept_len, reject_len, r_file, rej_file) -> None:
        print(f"\n{Colors.CYAN}{'='*50}")
        print(f"                SUMMARY REPORT")
        print(f"{'='*50}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✔ Accepted Recipes :{Colors.ENDC} {accept_len}")
        print(f"  {Colors.FAIL}✖ Rejected Recipes :{Colors.ENDC} {reject_len}")
        print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")
        print(f"  📁 Accepted Recipes saved to : {Colors.BOLD}{r_file}{Colors.ENDC}")
        print(f"  📁 Rejected Recipes saved to : {Colors.BOLD}{rej_file}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}\n{Colors.ENDC}")
