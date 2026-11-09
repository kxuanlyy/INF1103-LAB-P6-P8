from typing import Any, Dict, List, Optional

from ai_module.ai_manager import RECIPES_PATH
from io_manager.input_validator import InputValidator

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
