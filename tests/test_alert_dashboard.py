
import os
import sys
from copy import deepcopy
from datetime import date, datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from logic_manager.inventory_alert_service import InventoryAlertService


def display_alerts(alerts):

    for category, items in alerts.items():
        print(f"\n{category.upper()} ({len(items)} items)")
        print("-" * 50)

        if not items:
            print("No alerts found.")
            continue

        for item in items:
            record = item["record"]

            print(f"Record ID: {item['id']}")
            print(f"Product: {record.get('name', 'Unknown')}")
            print(f"Quantity: {record.get('quantity', 'Unknown')}")
            print(f"Use-by Date: {record.get('use-by', 'Unknown')}")
            print(f"Days Remaining: {item['days_remaining']}")
            print("-" * 50)


def run_test(name, test_function):

    print(f"\n{'=' * 60}")
    print(name)
    print("=" * 60)

    try:
        test_function()
        print(f"\nPASS: {name}")
        return True

    except Exception as error:
        print(f"\nFAIL: {name}")
        print(f"Error: {type(error).__name__}: {error}")
        return False


# TEST 1: Default alert categories
def test_alert_categories():
    service = InventoryAlertService()

    records = [
        {"name": "Milk", "use-by": "10/11/2026", "quantity": 5},
        {"name": "Bread", "use-by": "15/11/2026", "quantity": 10},
        {"name": "Eggs", "use-by": "20/11/2026", "quantity": 2},
        {"name": "Cheese", "use-by": None, "quantity": 1},
        {"name": "Yogurt", "use-by": "invalid", "quantity": 8},
    ]

    alerts = service.get_alerts(records, today=date(2026, 11, 13))

    display_alerts(alerts)

    assert len(alerts["expired"]) == 1
    assert len(alerts["expiring_soon"]) == 1
    assert len(alerts["low_stock"]) == 2
    assert len(alerts["unknown_expiry"]) == 2

    assert alerts["expired"][0]["record"]["name"] == "Milk"
    assert alerts["expiring_soon"][0]["record"]["name"] == "Bread"


# TEST 2: Custom thresholds
def test_custom_thresholds():
    service = InventoryAlertService()

    records = [
        {"name": "Apples", "use-by": "18/11/2026", "quantity": 4},
        {"name": "Bananas", "use-by": "20/11/2026", "quantity": 6},
        {"name": "Oranges", "use-by": "25/11/2026", "quantity": 10},
    ]

    alerts = service.get_alerts(
        records,
        today=date(2026, 11, 13),
        expiring_within_days=7,
        low_stock_threshold=5
    )

    display_alerts(alerts)

    assert len(alerts["expiring_soon"]) == 2
    assert len(alerts["low_stock"]) == 1
    assert len(alerts["expired"]) == 0


# TEST 3: Date handling and unchanged records
def test_date_handling():
    service = InventoryAlertService()

    records = [
        {"name": "Milk", "use-by": "13-11-2026", "quantity": 3},
        {"name": "Bread", "use-by": datetime(2026, 11, 14), "quantity": 4},
        {"name": "Eggs", "use-by": "17/11/2026", "quantity": 5},
    ]

    original_records = deepcopy(records)

    alerts = service.get_alerts(records, today=date(2026, 11, 13))

    display_alerts(alerts)

    assert len(alerts["expiring_soon"]) == 2
    assert len(alerts["expired"]) == 0
    assert len(alerts["unknown_expiry"]) == 0

    assert records == original_records

    empty_alerts = service.get_alerts([], today=date(2026, 11, 13))

    assert all(len(items) == 0 for items in empty_alerts.values())


# TEST 4: Invalid inputs
def test_invalid_inputs():
    service = InventoryAlertService()

    records = [
        {"name": "Milk", "use-by": "15/11/2026", "quantity": 2}
    ]

    invalid_cases = [
        {"today": "13/11/2026"},
        {"expiring_within_days": -1},
        {"low_stock_threshold": -2},
        {"expiring_within_days": 2.5},
        {"low_stock_threshold": True},
    ]

    for case in invalid_cases:
        try:
            service.get_alerts(
                records,
                today=date(2026, 11, 13) if "today" not in case else case["today"],
                expiring_within_days=case.get("expiring_within_days", 3),
                low_stock_threshold=case.get("low_stock_threshold", 2)
            )

        except (TypeError, ValueError) as error:
            print(f"PASS: Rejected {case}")
            print(f"Reason: {error}")

        else:
            raise AssertionError(f"Invalid input accepted: {case}")


# MAIN: Run all tests
def main():
    print("=" * 60)
    print("INVENTORY ALERT SERVICE - TEST RESULTS")
    print("=" * 60)

    tests = [
        ("TEST 1: Alert Categories", test_alert_categories),
        ("TEST 2: Custom Thresholds", test_custom_thresholds),
        ("TEST 3: Date Handling", test_date_handling),
        ("TEST 4: Invalid Inputs", test_invalid_inputs),
    ]

    passed = 0

    for name, test_function in tests:
        if run_test(name, test_function):
            passed += 1

    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {passed}/{len(tests)} TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
