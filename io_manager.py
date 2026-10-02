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
                # Extract fields using column headers
                food_name = row.get('food', '').strip()
                category = row.get('food_category', '').strip()
                use_by = row.get('use-by', '').strip()
                storage = row.get('storage condition', '').strip()
                days_exp = row.get('days_to_expiry', '').strip()       
                risk_lvl = row.get('waste_risk_level', '').strip()     
                allergens = row.get('allergen info', '').strip() or "None"
                demand = row.get('demand level', '').strip()
                quantity = row.get('quantity', '').strip()                  


                # Construct the clean dictionary payload
                record = {
                    "item": food_name,
                    "category": category,
                    "use_by_date": use_by,
                    "storage_condition": storage,
                    "days_to_expiry": days_exp,                        
                    "waste_risk_level": risk_lvl,                      
                    "allergen_info": allergens,
                    "demand_level": demand.lower(),                    
                    "quantity": quantity                                    
                }
                    
                records.append(record)
                
    except Exception as e:
        print(f"Error: Failed to read inventory file: {e}")
        return []

    return records

def get_staff_input(file_record):

    if not extracted_items:
        print("Error: No inventory data available to process.")
        return None

    # Display Interactive Choice Selection Menu
    print("\n--- SUPERMARKET STOCK LIST ---")
    for id, record in enumerate(extracted_items, start=1):
        print(f"[{id}] {record['item']:<32} (Stock Quantity: {record['quantity']})")
    print("-" * 50)

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

# Main Program starts here

inventory_data_path = "food_inventory.csv" 
extracted_items = load_inventory_file(inventory_data_path)

if extracted_data := extracted_items:
    final_ai_ready_dict = get_staff_input(extracted_data)
        
    print("Final Combined Payload for AI:")
    print(final_ai_ready_dict)
else:
    print(f"Error:  Ensure your inventory file exists at '{inventory_data_path}' and contains items.")