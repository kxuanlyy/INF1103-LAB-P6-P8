import csv
import os
from datetime import datetime

from ai_module.ai_manager import RECIPES_PATH, suggest_recipes

# Functions

def load_inventory_file(file_path):

    # Verify file existence
    if not os.path.exists(file_path):
        print(f"Error: Inventory file not found at path: {file_path}")
        return []

    records = []
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                use_by_str = row.get('use-by', '').strip()
                calculated_days = "0"
                if use_by_str:
                    try:
                        expiry_date = datetime.strptime(use_by_str, "%d/%m/%Y")
                        diff = (expiry_date - today).days
                        calculated_days = str(max(0, diff))
                    except ValueError:
                        calculated_days = row.get('days_to_expiry', '').strip()



                record = {
                    "item": row.get('food', '').strip(),
                    "category": row.get('food_category', '').strip(),
                    "use_by_date": use_by_str,
                    "storage_condition": row.get('storage condition', '').strip(),
                    "days_to_expiry": calculated_days,  #  Fixed to use the live variable!     
                    "waste_risk_level": row.get('waste_risk_level', '').strip(),     
                    "allergen_info": row.get('allergen info', '').strip() or "None",
                    "demand_level": row.get('demand level', '').strip().lower(),                    
                    "quantity": row.get('quantity', '').strip()                                    
                }
                records.append(record)
                
    except Exception as e:
        print(f"Error: Failed to read inventory file: {e}")
        return []

    return records

def print_current_inventory(extracted_items):
    if not extracted_items:
        print("\n[!] The inventory list is currently empty.")
        return False
    
    # Safely evaluate string column layout profiles based on data sizes
    max_name_len = max(len(record['item']) for record in extracted_items)
    name_col_width = max(max_name_len, 25)
    
    total_table_width = 4 + 3 + name_col_width + 3 + 6 + 3 + 12
    separator_line = "=" * total_table_width
    
    print("\n" + separator_line)
    print(f"{'No.':<4} | {'Ingredient Name':<{name_col_width}} | {'Qty':<6} | {'Expiry Date'}")
    print(separator_line)
    for itemid, record in enumerate(extracted_items, start=1):
        print(f"[{itemid}] {record['item']:<{name_col_width}} | {record['quantity']:<6} | {record['use_by_date']}")
    print(separator_line)
    return True

def save_inventory_file(file_path, extracted_items):
    fieldnames = [
        'food', 'food_category', 'use-by', 'storage condition', 
        'days_to_expiry', 'waste_risk_level', 'allergen info', 
        'demand level', 'quantity'
    ]
    
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()  # Write column names first
            
            for record in extracted_items:
                writer.writerow({
                    'food': record['item'],
                    'food_category': record['category'],
                    'use-by': record['use_by_date'],
                    'storage condition': record['storage_condition'],
                    'days_to_expiry': record['days_to_expiry'],
                    'waste_risk_level': record['waste_risk_level'],
                    'allergen info': record['allergen_info'],
                    'demand level': record['demand_level'],
                    'quantity': record['quantity']
                })
        # print(f"Successfully updated '{file_path}'.")
    except Exception as e:
        print(f"Error: Failed to save changes to file: {e}")

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
            return matched[0]
        print(f"Error: Invalid option. You must choose one of: {choices_str}")

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
            print("Error: Invalid date format. Please use D/M/YYYY (e.g., 26/9/2026).")

def get_validated_int(prompt_text, current_val=None):
    while True:
        suffix = f" [{current_val}]: " if current_val else ": "
        user_val = input(prompt_text + suffix).strip()
        
        if not user_val and current_val is not None:
            return str(current_val)
        if not user_val:
            print("Error: This number field cannot be left blank.")
            continue
        if user_val.isdigit():
            return user_val
        print("Error: Invalid entry. Please enter a positive whole number or 0.")

def prompt_for_ingredient_details(existing_item=None):
    print("\n--- ENTER INGREDIENT DETAILS ---")
    if existing_item:
        print("Press Enter to keep current bracketed values.")

    item = get_validated_string("Ingredient Name", allow_blank=False, current_val=existing_item.get('item') if existing_item else None)
    
    valid_categories = ["Dairy", "Meat", "Seafood", "Fresh Produce", "Bakery", "Pantry", "Other"]
    category = get_validated_choice("Category", valid_categories, current_val=existing_item.get('category') if existing_item else None)
    
    use_by = get_validated_date("Use-By Date (D/M/YYYY)", current_val=existing_item.get('use_by_date') if existing_item else None)

    valid_storage = ["Chilled", "Frozen", "Ambient"]
    storage = get_validated_choice("Storage Condition", valid_storage, current_val=existing_item.get('storage_condition') if existing_item else None)
    
    valid_risks = ["Low", "Medium", "High"]
    risk_lvl = get_validated_choice("Waste Risk Level", valid_risks, current_val=existing_item.get('waste_risk_level') if existing_item else None)
    
    allergens = get_validated_string("Allergen Info (or press Enter for None)", allow_blank=True, current_val=existing_item.get('allergen_info') if existing_item else None)
    demand = get_validated_choice("Demand Level", valid_risks, current_val=existing_item.get('demand_level', '').capitalize() if existing_item else None).lower()
    quantity = get_validated_int("Stock Quantity", current_val=existing_item.get('quantity') if existing_item else None)
    
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    expiry_date = datetime.strptime(use_by, "%d/%m/%Y")
    
    calculated_days = (expiry_date - today).days
    days_exp = str(calculated_days)
    print(f"-> Calculated Days to Expiry: {days_exp} day(s) remaining.")
   
    return {
        "item": item,
        "category": category,
        "use_by_date": use_by,
        "storage_condition": storage,
        "days_to_expiry": days_exp,                        
        "waste_risk_level": risk_lvl,                      
        "allergen_info": allergens,
        "demand_level": demand,                    
        "quantity": quantity                                    
    }

def handle_edit_menu(extracted_items, file_path):

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
            new_ingredient = prompt_for_ingredient_details()
            if new_ingredient["item"]:
                extracted_items.append(new_ingredient)
                print(f"\nSuccess: '{new_ingredient['item']}' successfully added.")
                save_inventory_file(file_path, extracted_items)

                print("\nUpdated Inventory after additions:")
                print_current_inventory(extracted_items)

            else:
                print("\nError: Action cancelled. Ingredient name cannot be blank.")

        # b. Remove Items
        elif sub_choice == 'b':
            print("\n--- REMOVE FOOD ITEM ---")
            if not print_current_inventory(extracted_items):
                continue
            
            remove_choice = input(f"Enter the item number to remove (1-{len(extracted_items)}): ").strip()
            if remove_choice.isdigit() and 1 <= int(remove_choice) <= len(extracted_items):
                removed = extracted_items.pop(int(remove_choice) - 1)
                print(f"\nSuccess: Removed '{removed['item']}' from the list.")
                save_inventory_file(file_path, extracted_items)

                print("\nUpdated Inventory after item removal:")
                print_current_inventory(extracted_items)

            else:
                print("\nError: Invalid selection. No items were removed.")

        # c. Edit Item
        elif sub_choice == 'c':
            if not print_current_inventory(extracted_items):
                continue
                
            update_choice = input(f"Enter the item number to modify (1-{len(extracted_items)}): ").strip()
            if update_choice.isdigit() and 1 <= int(update_choice) <= len(extracted_items):
                target_idx = int(update_choice) - 1
                current_data = extracted_items[target_idx]
                
                print(f"\nModifying details for: {current_data['item']}")
                print("Press Enter to keep current bracketed values.")
                
                updated_data = prompt_for_ingredient_details(current_data)
                extracted_items[target_idx] = updated_data
                print(f"\nSuccess: Updated data for '{updated_data['item']}'.")
                save_inventory_file(file_path, extracted_items)

                print("\n==================================================")
                print(f"          UPDATED DETAILS FOR: {updated_data['item'].upper()}          ")
                print("==================================================")
                print(f" Category:          {updated_data['category']}")
                print(f" Stock Quantity:    {updated_data['quantity']}")
                print(f" Use-By Date:       {updated_data['use_by_date']}")
                print(f" Days to Expiry:    {updated_data['days_to_expiry']} day(s) remaining")
                print(f" Storage Type:      {updated_data['storage_condition']}")
                print(f" Waste Risk Level:  {updated_data['waste_risk_level']}")
                print(f" Demand Level:      {updated_data['demand_level'].capitalize()}")
                print(f" Allergen Info:     {updated_data['allergen_info']}")
                print("==================================================")

            else:
                print("\nError: Invalid selection. Update aborted.")

        # d. Return to Main Menu
        elif sub_choice == 'd':
            print("\nReturning to Main Menu...")
            break
        else:
            print("\nError: Please enter a, b, c, or d.")

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
                print(f"\nSelected Item: {selected_record['item']}")
                break
                
        print(f"[INVALID INPUT] Please type a whole number between 1 and {len(extracted_items)}.")

    # Processing the Chosen Item and Staff Observations
    print("\n" + "="*55)
    print(f"PROCESSING INVENTORY ITEM: {selected_record['item']}")
    print(f"Expiry: {selected_record['use_by_date']} | Quantity: {selected_record['quantity']} | Risk Level: {selected_record['waste_risk_level']} ")
    print("="*55)

    # Staff Observations
    staff_notes = input("Enter any quality observations (or press Enter to skip): ").strip()
    if not staff_notes:
        staff_notes = "No structural physical defects observed"

    # combined payload dictionary
    ai_payload = {
        "item": selected_record["item"],
        "category": selected_record["category"],
        "use_by_date": selected_record["use_by_date"],
        "file_storage_condition": selected_record["storage_condition"],
        "days_to_expiry": selected_record["days_to_expiry"],
        "waste_risk_level": selected_record["waste_risk_level"],
        "allergen_info": selected_record["allergen_info"],
        "demand_level": selected_record["demand_level"],
        "quantity":  selected_record["quantity"],
        "staff_observations": staff_notes
    }

    return ai_payload

def search_food_item(extracted_items):
    
    print("\n--- SEARCH INVENTORY BY ITEM NUMBER ---")
    
    # 1. Print the inventory first so the user can see the ID numbers
    if not print_current_inventory(extracted_items):
        return

    # 2. Ask the user for the list index number
    user_choice = input(f"\nEnter the item number to view details (1-{len(extracted_items)}): ").strip()
    
    # 3. Validate input and display the item card with swapped labels
    if user_choice.isdigit():
        choice_num = int(user_choice)
        if 1 <= choice_num <= len(extracted_items):
            match = extracted_items[choice_num - 1]
            
            print("\n==================================================")
            print(f"          FOOD ID: [{choice_num}]          ")  # Changed header to Food ID
            print("==================================================")
            print(f" Item Name:         {match['item']}")         # Changed label to Item Name
            print(f" Category:          {match['category']}")
            print(f" Stock Quantity:    {match['quantity']}")
            print(f" Use-By Date:       {match['use_by_date']}")
            print(f" Days to Expiry:    {match['days_to_expiry']} day(s) remaining")
            print(f" Storage Type:      {match['storage_condition']}")
            print(f" Waste Risk Level:  {match['waste_risk_level']}")
            print(f" Demand Level:      {match['demand_level'].capitalize()}")
            print(f" Allergen Info:     {match['allergen_info']}")
            print("==================================================")
            return
            
    print(f"\nError: Invalid selection. Please type a valid number between 1 and {len(extracted_items)}.")


# Main Program starts here

inventory_data_path = "food_inventory.csv" 
current_inventory = load_inventory_file(inventory_data_path)

save_inventory_file(inventory_data_path, current_inventory) 


while True:
    print("\n=================================")
    print("          MAIN MENU              ")
    print("=================================")
    print(" 1. View current inventory stock")
    print(" 2. Edit items data")
    print(" 3. Search food item")  # New Option Added
    print(" 4. Ask AI")
    print(" 5. Exit")
    print("=================================")
        
    main_choice = input("Select an option (1-5): ").strip()
    if main_choice == "1":
        print_current_inventory(current_inventory)
            
    elif main_choice == "2":
        handle_edit_menu(current_inventory, inventory_data_path)
        
    elif main_choice == "3":
        search_food_item(current_inventory)
            
    elif main_choice == "4":
        print_current_inventory(current_inventory)
        process_item_for_ai(current_inventory)
            
    elif main_choice == "5":
        print("\nExiting program. Goodbye!")
        break
    else:
        print("\nError: Please select a number between 1 and 5.")

