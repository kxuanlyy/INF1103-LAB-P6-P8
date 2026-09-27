import csv
import os

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

