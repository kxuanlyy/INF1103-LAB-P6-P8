import csv
import os

# Functions

def load_inventory_file(file_path):

    # Verify file existence
    if not os.path.exists(file_path):
        print(f"Error: Inventory file not found at path: {file_path}")
        return []

    records = []
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                record = {
                    "item": row.get('food', '').strip(),
                    "category": row.get('food_category', '').strip(),
                    "use_by_date": row.get('use-by', '').strip(),
                    "storage_condition": row.get('storage condition', '').strip(),
                    "days_to_expiry": row.get('days_to_expiry', '').strip(),       
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
    """Displays your items cleanly using dynamic width spacing metrics."""
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
    for x, record in enumerate(extracted_items, start=1):
        print(f"[{x}] {record['item']:<{name_col_width}} | {record['quantity']:<6} | {record['use_by_date']}")
    print(separator_line)
    return True

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


inventory_data_path = "food_inventory.csv" 
current_inventory = load_inventory_file(inventory_data_path)

while True:
    print("\n=================================")
    print("          MAIN MENU              ")
    print("=================================")
    print(" 1. View current inventory stock")
    print(" 2. Edit items data")
    print(" 3. Ask AI")
    print(" 4. Exit")
    print("=================================")
        
    main_choice = input("Select an option (1-4): ").strip()
    if main_choice == "1":
        print_current_inventory(current_inventory)
            
    elif main_choice == "2":
        print_current_inventory(current_inventory)
        #handle_edit_menu(current_inventory, inventory_data_path)
            
    elif main_choice == "3":
        print_current_inventory(current_inventory)
        #process_item_for_ai(current_inventory)
            
    elif main_choice == "4":
        print("\nExiting program. Goodbye!")
        break
    else:
        print("\nError: Please select a number between 1 and 4.")

# if extracted_data := current_inventory:
#     final_ai_ready_dict = get_staff_input(extracted_data)
        
#     print("Final Combined Payload for AI:")
#     print(final_ai_ready_dict)
# else:
#     print(f"Error:  Ensure your inventory file exists at '{inventory_data_path}' and contains items.")
