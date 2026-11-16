from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from copy import deepcopy
from datetime import date, datetime
from types import SimpleNamespace
from ai_module.assessment_validator import AssessmentValidator


def stock():
    return {"id": "I001", "name": "Tomato", "unit": "kg", "storage_condition": "chilled",
            "allergens": "none", "use_by": "2026-11-15", "quantity": 3,
            "demand_level": "medium", "storage_status": "yes", "allergen_status": "no"}


def analysis():
    return {"item_id": "I001", "category": "produce", "reason": "Use soon",
            "demand_level": "medium", "expiry_urgency": "high", "spoilage_risk": "medium",
            "suitability_score": 80, "confidence": 0.9, "allergen_uncertain": False,
            "storage_uncertain": False, "recipe_suggestions": [
                {"name": "Tomato Soup", "ingredient_ids": ["I001"], "how_to_make": ["Cook tomatoes"]}
            ]}


class TestAssessmentValidator(unittest.TestCase):
    def setUp(self):
        self.validator = AssessmentValidator()

    def test_valid_stock_and_inventory(self):
        item = stock()
        self.validator.validate_stock_item(item)
        self.assertEqual(
            self.validator.validate_inputs(item, [item], date(2026, 11, 13)),
            {"I001"},
        )

    def test_invalid_stock(self):
        for bad_quantity in [0, -1, True, float("nan")]:
            with self.subTest(quantity=bad_quantity):
                item = stock()
                item["quantity"] = bad_quantity
                with self.assertRaises(ValueError):
                    self.validator.validate_stock_item(item)

        item = stock()
        item["use_by"] = "15/11/2026"
        with self.assertRaises(ValueError):
            self.validator.validate_stock_item(item)

    def test_invalid_inventory(self):
        item = stock()
        with self.assertRaises(ValueError):
            self.validator.validate_inputs(
                item, [item, deepcopy(item)], date(2026, 11, 13)
            )
        with self.assertRaises(ValueError):
            self.validator.validate_inputs(item, [item], datetime(2026, 11, 13))
        with self.assertRaises(ValueError):
            self.validator.validate_inputs(item, [], date(2026, 11, 13))

    def test_valid_analysis(self):
        value = analysis()
        self.assertIs(
            self.validator.validate_analysis(
                value, "I001", {"I001"}, require_steps=True
            ),
            value,
        )

    def test_invalid_analysis(self):
        value = analysis()
        value["item_id"] = "WRONG"
        with self.assertRaises(ValueError):
            self.validator.validate_analysis(value, "I001")

        value = analysis()
        value["confidence"] = 1.5
        with self.assertRaises(ValueError):
            self.validator.validate_analysis(value, "I001")

        value = analysis()
        value["allergen_uncertain"] = "false"
        with self.assertRaises(ValueError):
            self.validator.validate_analysis(value, "I001")

    def test_invalid_recipes(self):
        value = analysis()
        value["recipe_suggestions"][0]["ingredient_ids"] = ["I002"]
        with self.assertRaises(ValueError):
            self.validator.validate_analysis(value, "I001", {"I001"})

        value = analysis()
        value["recipe_suggestions"][0]["how_to_make"] = []
        with self.assertRaises(ValueError):
            self.validator.validate_analysis(
                value, "I001", {"I001"}, require_steps=True
            )

        value = analysis()
        value["recipe_suggestions"][0]["additional_ingredients"] = ["Salt", " salt "]
        with self.assertRaises(ValueError):
            self.validator.validate_analysis(value, "I001")

    def test_json_parsing(self):
        self.assertEqual(
            self.validator.parse_response('```json\n{"ok": true}\n```'),
            {"ok": True},
        )
        for response in ['{"a":1,"a":2}', '{"score":NaN}', '[1,2]']:
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    self.validator.parse_response(response)

    def test_completion_handling(self):
        completion = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(content='{"ok":true}', refusal=None),
                )
            ]
        )
        self.assertEqual(
            self.validator.extract_response(completion), '{"ok":true}'
        )

        refused = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="length",
                    message=SimpleNamespace(content="partial", refusal=None),
                )
            ]
        )
        with self.assertRaises(ValueError):
            self.validator.extract_response(refused)
        with self.assertRaises(ValueError):
            self.validator.extract_response(SimpleNamespace(choices=[]))
