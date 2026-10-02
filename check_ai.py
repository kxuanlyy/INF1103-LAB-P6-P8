from datetime import date, timedelta
import json

from ai_module.ai_manager import analyse_item

today = date.today()

# INPUT: example stock data
item = {
    "id": "tomato-001",
    "name": "Tomatoes",
    "quantity": 12,
    "unit": "kg",
    "use_by": (today + timedelta(days=2)).isoformat(),
    "demand_level": "low",
    "storage_condition": "refrigerated",
    "storage_status": "yes",
    "allergens": "none",
    "allergen_status": "yes",
}

# Add other stock records here for combined recipe suggestions.
inventory = [item]

# PROCESS: send the data through your AI manager
analysis, error = analyse_item(item, inventory, today)

# OUTPUT: display the result in the terminal
if error:
    print("Assessment failed:", error)
else:
    print(json.dumps(analysis, indent=2))