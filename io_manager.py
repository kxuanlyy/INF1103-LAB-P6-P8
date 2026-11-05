# standard library
from abc import ABC, abstractmethod
from datetime import datetime

import textwrap

# typing n ds imports
from typing import Any, Dict, List, Optional

# local project imports
from ai_module.ai_manager import RECIPES_PATH, suggest_recipes
from logic_manager import evaluate_recipes


class UserInterface(ABC):
    @abstractmethod
    def display_main_menu(self) -> None: pass

    @abstractmethod
    def display_edit_menu(self) -> None: pass

    @abstractmethod
    def display_inventory_search_menu(self) -> None: pass

    @abstractmethod
    def display_recipe_search_menu(self) -> None: pass

    @abstractmethod
    def print_current_inventory(self, extracted_items: list, ids: list = None) -> bool: pass

    @abstractmethod
    def print_recipes(self, recipe_list: list, ids: list = None) -> bool: pass

class StockItem:
    #Domain object representing food asset in inventory, groups item data together instead of using raw loose variables

    def __init__(self, name: str, quantity: float, unit: str = "pcs"):
        self._name: str = name
        self._quantity: float = quantity
        self._unit: str = unit

    @property
    def name(self) -> str:
        return self._name

    @property
    def quantity(self) -> float:
        return self._quantity


    def to_dict(self) -> Dict[str, Any]:
        #Converts object data back into dictionary for storage
        return {"name": self._name, "quantity": self._quantity, "unit": self._unit}


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockItem':
        #Creates a fresh StockItem object using dictionary data from storage
        return cls(
            name=data.get("name", "Unknown"),
            quantity=float(data.get("quantity", 0.0)),
            unit=data.get("unit", "pcs")
        )

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

class InputValidator:
    #Handles capturing input arguments and apply validations

    def get_validated_string(self, prompt_text: str, allow_blank: bool = False, current_val: Optional[str] = None) -> str:
        while True:
            suffix = f" [{current_val}]: " if current_val else ": "
            user_val = input(prompt_text + suffix).strip()

            if not user_val and current_val:
                return current_val
            if not user_val and not allow_blank:
                print("Error: This field cannot be left blank. Please enter a value.")
                continue
            return user_val if user_val else "None"

    def get_validated_choice(self, prompt_text: str, valid_choices: List[str], current_val: Optional[str] = None) -> str:
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
                return matched[0]
            print(f"Error: Invalid option. You must choose one of: {choices_str}")

    def get_validated_int(self, prompt_text: str, current_val: Optional[Any] = None) -> str:
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

    def get_validated_date(self, prompt_text: str, current_val: Optional[str] = None) -> str:
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
                print("Error: Invalid date format. Please use DD/MM/YYYY (e.g., 26/09/2026).")

    def get_optional_text(self, prompt_text: str) -> Optional[str]:
        return input(prompt_text + " (Enter to skip): ").strip() or None

    def get_optional_int(self, prompt_text: str) -> Optional[int]:
        while True:
            user_val = input(prompt_text + " (Enter to skip): ").strip()
            if not user_val:
                return None
            if user_val.isascii() and user_val.isdigit():
                return int(user_val)
            print("Error: Please enter a whole number (0 or more), or press Enter to skip.")

    def get_optional_list(self, prompt_text: str) -> Optional[List[str]]:
        raw = input(prompt_text + " (comma-separated, Enter to skip): ").strip()
        items = [item.strip() for item in raw.split(",") if item.strip()]
        return items or None

    def prompt_for_ingredient_details(self, existing_item: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        print("\n--- ENTER INGREDIENT DETAILS ---")
        if existing_item:
            print("Press Enter to keep current bracketed values.")

        item = self.get_validated_string("Ingredient Name", allow_blank=False, current_val=existing_item.get('food') if existing_item else None)
        valid_categories = ["Dairy", "Meat & Seafood", "Fresh Produce", "Bakery", "Pantry", "Other"]
        category = self.get_validated_choice("Category", valid_categories, current_val=existing_item.get('food_category') if existing_item else None)
        use_by = self.get_validated_date("Use-By Date (DD/MM/YYYY)", current_val=existing_item.get('use-by') if existing_item else None)
        valid_storage = ["Chilled", "Frozen", "Ambient"]
        storage = self.get_validated_choice("Storage Condition", valid_storage, current_val=existing_item.get('storage condition') if existing_item else None)
        valid_risks = ["Low", "Medium", "High"]
        risk_lvl = self.get_validated_choice("Waste Risk Level", valid_risks, current_val=existing_item.get('waste_risk_level') if existing_item else None)
        allergens = self.get_validated_string("Allergen Info (or press Enter for None)", allow_blank=True, current_val=existing_item.get('allergen info') if existing_item else None)
        
        if allergens.lower() == "none":
            allergens = "None"

        demand = self.get_validated_choice("Demand Level", valid_risks, current_val=existing_item.get('demand level').capitalize() if existing_item else None)
        quantity = self.get_validated_int("Stock Quantity", current_val=existing_item.get('quantity') if existing_item else None)

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

class MenuController:
    # Coordinates application lifecycle states, routes user selections, n bridges interaction across IO, Data n AI

    def __init__(self, view, data_manager, results_store, ai_manager, logic_evaluator) -> None:
        self.view = view
        self.data_manager = data_manager
        self.results_store = results_store
        self.ai_manager = ai_manager
        self.logic_evaluator = logic_evaluator
        self.validator = InputValidator()
                
    def _get_record_ids(self, table: List[Any], records: List[Any]) -> List[int]:
        position = {id(record): n for n, record in enumerate(table, start=1)}
        return [position[id(record)] for record in records]

    def run(self, today: Optional[Any] = None, client: Optional[Any] = None) -> None:
        while True:
            self.view.display_main_menu()
            main_choice = input("Select an option (1-8): ").strip()

            if main_choice == "1":
                self.view.print_current_inventory(self.data_manager.inventory.records)

            elif main_choice == "2":
                self.handle_inventory_search()

            elif main_choice == "3":
                self.view.print_current_inventory(self.data_manager.inventory.records)
                self.handle_edit_menu()

            elif main_choice == "4":
                if not self.view.print_current_inventory(self.data_manager.inventory.records):
                    continue
                payload = self.process_item_for_ai(self.data_manager.inventory.records)
                if payload:
                    print("\nAsking AI... please wait.")
                    last_result, last_error = self.ai_manager.suggest_recipes(payload, today=today)
                    if last_error:
                        print("Assessment failed:", last_error)
                    else:
                        self.view.print_ai_result(last_result, RECIPES_PATH)

            elif main_choice == "5":
                self.handle_recipe_processor()

            elif main_choice == "6":
                self.data_manager.load()
                self.view.print_recipes(self.data_manager.recipes.records)

            elif main_choice == "7":
                self.data_manager.load()
                self.handle_recipe_search()


            elif main_choice == "8":
                print("\nExiting program. Goodbye!")
                break
            else:
                print("\nError: Please select a number between 1 and 8.")

    def handle_edit_menu(self) -> None:
        while True:
            self.view.display_edit_menu()
            sub_choice = input("Select an option (a-d): ").strip().lower()

            if sub_choice == 'a':
                print("\nCurrent Inventory before adding:")
                self.view.print_current_inventory(self.data_manager.inventory.records)

                details = self.validator.prompt_for_ingredient_details()
                try:
                    self.data_manager.inventory.add(**details)
                except (OSError, ValueError) as e:
                    print(f"\nError: Failed to add '{details['food']}': {e}")
                else:
                    print(f"\nSuccess: '{details['food']}' successfully added.")
                    print("\nUpdated Inventory after additions:")
                    self.view.print_current_inventory(self.data_manager.inventory.records)

            elif sub_choice == 'b':
                print("\n--- REMOVE FOOD ITEM ---")
                if not self.view.print_current_inventory(self.data_manager.inventory.records):
                    continue

                remove_choice = input(f"Enter the item number to remove (1-{len(self.data_manager.inventory.records)}): ").strip()
                if remove_choice.isdigit() and 1 <= int(remove_choice) <= len(self.data_manager.inventory.records):
                    try:
                        removed = self.data_manager.inventory.delete(int(remove_choice) - 1)
                    except OSError as e:
                        print(f"\nError: Failed to remove the item: {e}")
                    else:
                        print(f"\n[SUCCESS] Removed '{removed['food']}' from the list.")
                        print("\nUpdated Inventory after item removal:")
                        self.view.print_current_inventory(self.data_manager.inventory.records)
                else:
                    print("\nError: Invalid selection. No items were removed.")

            elif sub_choice == 'c':
                if not self.view.print_current_inventory(self.data_manager.inventory.records):
                    continue

                update_choice = input(f"Enter the item number to modify (1-{len(self.data_manager.inventory.records)}): ").strip()
                if update_choice.isdigit() and 1 <= int(update_choice) <= len(self.data_manager.inventory.records):
                    target_idx = int(update_choice) - 1
                    current_data = self.data_manager.inventory.records[target_idx]

                    print(f"\nModifying details for: {current_data['food']}")
                    print("Press Enter to keep current bracketed values.")

                    details = self.validator.prompt_for_ingredient_details(current_data)
                    try:
                        self.data_manager.inventory.update(target_idx, **details)
                    except (OSError, ValueError) as e:
                        print(f"\nError: Failed to update '{current_data['food']}': {e}")
                    else:
                        print(f"\nSuccess: Updated data for '{details['food']}'.")
                else:
                    print("\nError: Invalid selection. Update aborted.")

            elif sub_choice == 'd':
                print("\nReturning to Main Menu...")
                break
            else:
                print("\nError: Please enter a, b, c, or d.")

    def handle_inventory_search(self) -> None:
        print("\n--- SEARCH INVENTORY ---")
        print("Leave a field blank to skip it. If you fill in both, both must match.")
        
        filters = {
            "food": self.validator.get_optional_text("Food name contains"),
            "item_id": self.validator.get_optional_int("ID (the number shown in the inventory list)"),
        }
        results = self.data_manager.inventory.search(**filters)
        
        if results:
            print(f"\nFound {len(results)} matching item(s):")
            self.view.print_current_inventory(results, self._get_record_ids(self.data_manager.inventory.records, results))
        else:
            print("\nNo inventory items matched that name/ID.")

        while True:
            self.view.display_inventory_search_menu()
            search_choice = input("Select an option (1-3): ").strip()

            if search_choice == "1":
                self.handle_inventory_search()
                break
            elif search_choice == "2":
                user_choice = input(f"Enter the item ID to show (1-{len(self.data_manager.inventory.records)}): ").strip()
                if user_choice.isdigit() and 1 <= int(user_choice) <= len(self.data_manager.inventory.records):
                    idx = int(user_choice)
                    self.view.print_item_card(idx, self.data_manager.inventory.records[idx - 1])
                else:
                    print(f"\nError: Invalid selection. Use range 1-{len(self.data_manager.inventory.records)}.")
            elif search_choice == "3":
                print("\nReturning to Main Menu...")
                break
            else:
                print("\nError: Please enter 1, 2, or 3.")

    def handle_recipe_search(self) -> None:
        print("\n--- SEARCH RECIPES ---")
        print("Leave a field blank to skip it. If you fill in both, both must match.")

        filters = {
            "ingredient": self.validator.get_optional_list("Ingredient (a recipe must have all you list)"),
            "item_id": self.validator.get_optional_int("ID (the number shown in the recipe list)"),
        }
        results = self.data_manager.recipes.search(**filters)

        if search_results := results:
            print(f"\nFound {len(search_results)} matching recipe(s):")
            self.view.print_recipes(search_results, self._get_record_ids(self.data_manager.recipes.records, search_results))
        else:
            print("\nNo recipes matched that ingredient/ID.")

        while True:
            self.view.display_recipe_search_menu()
            search_choice = input("Select an option (1-3): ").strip()

            if search_choice == "1":
                self.handle_recipe_search()
                break
            elif search_choice == "2":
                user_choice = input(f"Enter the recipe ID to show (1-{len(self.data_manager.recipes.records)}): ").strip()
                if user_choice.isdigit() and 1 <= int(user_choice) <= len(self.data_manager.recipes.records):
                    idx = int(user_choice)
                    self.view.print_recipe_card(idx, self.data_manager.recipes.records[idx - 1])
                else:
                    print(f"\nError: Invalid selection. Use range 1-{len(self.data_manager.recipes.records)}.")
            elif search_choice == "3":
                print("\nReturning to Main Menu...")
                break
            else:
                print("\nError: Please enter 1, 2, or 3.")

    def process_item_for_ai(self, extracted_items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not extracted_items:
            print("Error: No inventory data available to process.")
            return None

        selected_record = None
        while True:
            user_choice = input(f"Enter the item number you want to check (1 to {len(extracted_items)}): ").strip()
            if user_choice.isdigit() and 1 <= int(user_choice) <= len(extracted_items):
                selected_record = extracted_items[int(user_choice) - 1]
                print(f"\nSelected Item: {selected_record['food']}")
                break
            print(f"[INVALID INPUT] Please type a whole number between 1 and {len(extracted_items)}.")

        print("\n" + "="*55)
        print(f"PROCESSING INVENTORY ITEM: {selected_record['food']}")
        print(f"Expiry: {selected_record['use-by']} | Quantity: {selected_record['quantity']} | Risk Level: {selected_record['waste_risk_level']} ")
        print("="*55)

        staff_notes = input("Enter any quality observations (or press Enter to skip): ").strip()
        if not staff_notes:
            staff_notes = "No structural physical defects observed"
        return {
        "item": selected_record["food"],
        "category": selected_record["food_category"],
        "use_by_date": selected_record["use-by"],
        "file_storage_condition": selected_record["storage condition"],
        "days_to_expiry": selected_record["days_to_expiry"],
        "waste_risk_level": selected_record["waste_risk_level"],
        "allergen_info": selected_record["allergen info"] or "None",
        "demand_level": selected_record["demand level"].lower(),
        "quantity": selected_record["quantity"],
        "staff_observations": staff_notes
        }
    
    def handle_recipe_processor(self) -> None:
        self.view.print_recipe_processor_header()
        data = self.results_store.load_json_files()
        
        if isinstance(data, dict) and "error" in data:
            print(f"\033[91m[ERROR] {data['error']}\033[0m")
            return

        accepted_recipes = data["accepted_recipes"]
        recipes_from_json = data["recipes_from_json"]

        _accept_list = []
        _reject_list = []

        for json_recipe in recipes_from_json:
            json_name = json_recipe.get("name", "").strip()
            single_accept, single_reject = self.logic_evaluator.evaluate(accepted_recipes, [json_recipe])
            
            if single_accept:
                _accept_list.append(single_accept[0])
                self.view.print_recipe_processor_step(True, json_name)
            else:
                rejected_item = single_reject[0]
                _reject_list.append(rejected_item)
                self.view.print_recipe_processor_step(False, rejected_item['name'], rejected_item['reason'])

        results_filename, rejected_filename = self.results_store.save_results(_accept_list, _reject_list)
        self.view.print_recipe_processor_summary(len(_accept_list), len(_reject_list), results_filename, rejected_filename)
        self.data_manager.load()

def main(today=None, client=None):
    import data_manager as dm 
    from logic_manager import RecipeEvaluator 
    from ai_module.ai_manager import AIManager, GroqProvider
    
    active_view = ConsoleView()
    active_data_mgr = dm.DataManager()         
    active_results_store = dm.RecipeResultsStore()
    provider = GroqProvider(client) if client is not None else None
    ai_manager = AIManager(provider=provider)
    logic_evaluator = RecipeEvaluator()
    
    controller = MenuController(
        view=active_view, 
        data_manager=active_data_mgr, 
        results_store=active_results_store,
        ai_manager=ai_manager,
        logic_evaluator=logic_evaluator
    )
    controller.run(today=today, client=client)

    
if __name__ == "__main__":
    main()