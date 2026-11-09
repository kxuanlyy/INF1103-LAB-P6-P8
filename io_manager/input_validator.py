from datetime import datetime
from typing import Any, Dict, List, Optional

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

