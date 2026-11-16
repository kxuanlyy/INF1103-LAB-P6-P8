
import os
import sys
import unittest
from copy import deepcopy
from datetime import date, datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from logic_manager.inventory_alert_service import InventoryAlertService


class TestInventoryAlertService(unittest.TestCase):
    def test_alert_categories(self):
        service = InventoryAlertService()
        records = [
            {"name": "Milk", "use-by": "10/11/2026", "quantity": 5},
            {"name": "Bread", "use-by": "15/11/2026", "quantity": 10},
            {"name": "Eggs", "use-by": "20/11/2026", "quantity": 2},
            {"name": "Cheese", "use-by": None, "quantity": 1},
            {"name": "Yogurt", "use-by": "invalid", "quantity": 8},
        ]

        alerts = service.get_alerts(records, today=date(2026, 11, 13))

        self.assertEqual(len(alerts["expired"]), 1)
        self.assertEqual(len(alerts["expiring_soon"]), 1)
        self.assertEqual(len(alerts["low_stock"]), 2)
        self.assertEqual(len(alerts["unknown_expiry"]), 2)
        self.assertEqual(alerts["expired"][0]["record"]["name"], "Milk")
        self.assertEqual(alerts["expiring_soon"][0]["record"]["name"], "Bread")

    def test_custom_thresholds(self):
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
            low_stock_threshold=5,
        )

        self.assertEqual(len(alerts["expiring_soon"]), 2)
        self.assertEqual(len(alerts["low_stock"]), 1)
        self.assertEqual(len(alerts["expired"]), 0)

    def test_date_handling(self):
        service = InventoryAlertService()
        records = [
            {"name": "Milk", "use-by": "13-11-2026", "quantity": 3},
            {"name": "Bread", "use-by": datetime(2026, 11, 14), "quantity": 4},
            {"name": "Eggs", "use-by": "17/11/2026", "quantity": 5},
        ]
        original_records = deepcopy(records)

        alerts = service.get_alerts(records, today=date(2026, 11, 13))

        self.assertEqual(len(alerts["expiring_soon"]), 2)
        self.assertEqual(len(alerts["expired"]), 0)
        self.assertEqual(len(alerts["unknown_expiry"]), 0)
        self.assertEqual(records, original_records)

        empty_alerts = service.get_alerts([], today=date(2026, 11, 13))
        self.assertTrue(all(len(items) == 0 for items in empty_alerts.values()))

    def test_invalid_inputs(self):
        service = InventoryAlertService()
        records = [{"name": "Milk", "use-by": "15/11/2026", "quantity": 2}]
        invalid_cases = [
            {"today": "13/11/2026"},
            {"expiring_within_days": -1},
            {"low_stock_threshold": -2},
            {"expiring_within_days": 2.5},
            {"low_stock_threshold": True},
        ]

        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaises((TypeError, ValueError)):
                    service.get_alerts(
                        records,
                        today=(
                            date(2026, 11, 13)
                            if "today" not in case
                            else case["today"]
                        ),
                        expiring_within_days=case.get("expiring_within_days", 3),
                        low_stock_threshold=case.get("low_stock_threshold", 2),
                    )
