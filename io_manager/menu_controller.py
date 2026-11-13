import sys
from typing import Any, Dict, List, Optional

from ai_module.ai_manager import RECIPES_PATH
from data_manager import data_manager
from io_manager.input_validator import InputValidator
from io_manager.key_reader import KeyReader
from logic_manager.edit_business_rules import BusinessRulesEditor
from logic_manager.inventory_alert_service import (
    DEFAULT_EXPIRING_WITHIN_DAYS,
    InventoryAlertService,
)


#

class MenuController:
    # Coordinates application lifecycle states, routes user selections, n bridges interaction across IO, Data n AI

    def __init__(self, view, data_manager, results_store, ai_manager, logic_evaluator) -> None:
        self.view = view
        self.data_manager = data_manager
        self.results_store = results_store
        self.ai_manager = ai_manager
        self.logic_evaluator = logic_evaluator
        self.validator = InputValidator()
        self.business_rules_editor = BusinessRulesEditor()
        self.inventory_alert_service = InventoryAlertService()
                
    def load_business_rules(self) -> List[Dict[str, Any]]:
        # Supply validated recipe rules to the GUI through the existing service.
        return self.business_rules_editor.load_rules()

    def editbusinessrules(self, updated_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Keep validation and file saving in BusinessRulesEditor.
        return self.business_rules_editor.editbusinessrules(updated_rules)

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
                print("\nError: Please select a number between 1 and 9.")

    def handle_inventory_alerts(self, today: Optional[Any] = None) -> None:
        self.data_manager.load()
        alerts = self.inventory_alert_service.get_alerts(
            self.data_manager.inventory.records,
            today=today,
        )

        print("\n============= INVENTORY ALERTS =============")
        print(f"Expired: {len(alerts['expired'])} | "
              f"Expiring within {DEFAULT_EXPIRING_WITHIN_DAYS} days: "
              f"{len(alerts['expiring_soon'])} | "
              f"Low stock: "
              f"{len(alerts['low_stock'])} | "
              f"Check expiry date: {len(alerts['unknown_expiry'])}")

        by_id = {}
        for alert_name, entries in alerts.items():
            for entry in entries:
                item_id = entry["id"]
                item = by_id.setdefault(item_id, {
                    **entry,
                    "statuses": [],
                })
                item["statuses"].append(alert_name)

        if not by_id:
            print("No inventory alerts. All recorded items are within the configured thresholds.")
            return

        print(f"\n{'ID':<5} {'Item':<25} {'Qty':<6} {'Use-by':<13} "
              f"{'Days left':<11} Alerts")
        print("-" * 85)
        for item_id, item in by_id.items():
            record = item["record"]
            days_remaining = item["days_remaining"]
            days_text = str(days_remaining) if days_remaining is not None else "Unknown"
            quantity = record.get("quantity")
            quantity_text = str(quantity) if quantity is not None else "Unknown"
            status_labels = {
                "expired": "EXPIRED",
                "expiring_soon": "EXPIRING SOON",
                "low_stock": "LOW STOCK",
                "unknown_expiry": "CHECK EXPIRY DATE",
            }
            status = ", ".join(status_labels[name] for name in item["statuses"])
            print(f"{item_id:<5} {record.get('food', '')[:24]:<25} "
                  f"{quantity_text:<6} {record.get('use-by', ''):<13} "
                  f"{days_text:<11} {status}")

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

    def _inventory_matches(self, query: str) -> List[Dict[str, Any]]:
        # Items whose name contains the text. If the text is a whole number, the
        # item with that ID (its number in the full list) is included too.
        table = self.data_manager.inventory
        query = query.strip()
        found = table.search(food=query or None)
        if query.isascii() and query.isdigit():
            found = found + table.search(item_id=int(query))
        wanted = {id(record) for record in found}
        return [record for record in table.records if id(record) in wanted]   # keep list order

    def _live_inventory_search(self) -> Optional[str]:
        # Shows the inventory and narrows it after every key press.
        # Returns the final text on Enter, or None if the user pressed Esc.
        records = self.data_manager.inventory.records
        query = ""
        with KeyReader() as keys:
            while True:
                items = self._inventory_matches(query)
                self.view.display_inventory_live_search(
                    query, items, self._get_record_ids(records, items), len(records))

                key = keys.read_key()
                while True:                       # take everything already typed (e.g. a paste) before redrawing
                    if key == "ENTER":
                        return query
                    if key == "ESC":
                        sys.stdout.write("\033[H\033[J")     # clear the live screen before leaving
                        return None
                    if key == "BACKSPACE":
                        query = query[:-1]
                    elif key == "CTRL_U":
                        query = ""
                    elif len(key) == 1:
                        query += key
                    if not keys.pending():
                        break
                    key = keys.read_key()

    def _ask_inventory_search(self) -> Optional[str]:
        # Live search in a real terminal; a plain one-line prompt when input is piped.
        if KeyReader.is_interactive():
            return self._live_inventory_search()
        print("\n--- SEARCH INVENTORY ---")
        return input("Food name or ID (Enter to skip): ").strip()

    def _show_inventory_results(self, query: str) -> None:
        if KeyReader.is_interactive():
            sys.stdout.write("\033[H\033[J")      # drop the live screen so the final list stands alone
        results = self._inventory_matches(query)
        if results:
            print(f"\nFound {len(results)} matching item(s):")
            self.view.print_current_inventory(results, self._get_record_ids(self.data_manager.inventory.records, results))
        else:
            print("\nNo inventory items matched that name/ID.")

    def handle_inventory_search(self) -> None:
        query = self._ask_inventory_search()
        if query is None:                          # Esc on the first search: straight back
            print("\nReturning to Main Menu...")
            return
        self._show_inventory_results(query)

        while True:
            self.view.display_inventory_search_menu()
            search_choice = input("Select an option (1-3): ").strip()

            if search_choice == "1":
                query = self._ask_inventory_search()
                if query is not None:              # Esc here just returns to this menu
                    self._show_inventory_results(query)
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
