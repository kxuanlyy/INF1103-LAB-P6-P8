from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run_tests(tests):
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS: {name}")
            passed += 1
        except Exception as exc:
            print(f"FAIL: {name} - {type(exc).__name__}: {exc}")
    print(f"\nFINAL RESULTS: {passed}/{len(tests)} TESTS PASSED")
    if passed != len(tests):
        raise SystemExit(1)


def expect_error(fn, error_type=ValueError):
    try:
        fn()
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}")

import json
from copy import deepcopy
from datetime import date, datetime
from types import SimpleNamespace
from ai_module.assessment_validator import AssessmentValidator

validator = AssessmentValidator()


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


def test_valid_stock_and_inventory():
    item = stock()
    validator.validate_stock_item(item)
    assert validator.validate_inputs(item, [item], date(2026, 11, 13)) == {"I001"}


def test_invalid_stock():
    for bad_quantity in [0, -1, True, float("nan")]:
        item = stock(); item["quantity"] = bad_quantity
        expect_error(lambda item=item: validator.validate_stock_item(item))
    item = stock(); item["use_by"] = "15/11/2026"
    expect_error(lambda: validator.validate_stock_item(item))


def test_invalid_inventory():
    item = stock()
    expect_error(lambda: validator.validate_inputs(item, [item, deepcopy(item)], date(2026, 11, 13)))
    expect_error(lambda: validator.validate_inputs(item, [item], datetime(2026, 11, 13)))
    expect_error(lambda: validator.validate_inputs(item, [], date(2026, 11, 13)))


def test_valid_analysis():
    value = analysis()
    assert validator.validate_analysis(value, "I001", {"I001"}, require_steps=True) is value


def test_invalid_analysis():
    value = analysis(); value["item_id"] = "WRONG"
    expect_error(lambda: validator.validate_analysis(value, "I001"))
    value = analysis(); value["confidence"] = 1.5
    expect_error(lambda: validator.validate_analysis(value, "I001"))
    value = analysis(); value["allergen_uncertain"] = "false"
    expect_error(lambda: validator.validate_analysis(value, "I001"))


def test_invalid_recipes():
    value = analysis(); value["recipe_suggestions"][0]["ingredient_ids"] = ["I002"]
    expect_error(lambda: validator.validate_analysis(value, "I001", {"I001"}))
    value = analysis(); value["recipe_suggestions"][0]["how_to_make"] = []
    expect_error(lambda: validator.validate_analysis(value, "I001", {"I001"}, require_steps=True))
    value = analysis(); value["recipe_suggestions"][0]["additional_ingredients"] = ["Salt", " salt "]
    expect_error(lambda: validator.validate_analysis(value, "I001"))


def test_json_parsing():
    assert validator.parse_response('```json\n{"ok": true}\n```') == {"ok": True}
    expect_error(lambda: validator.parse_response('{"a":1,"a":2}'))
    expect_error(lambda: validator.parse_response('{"score":NaN}'))
    expect_error(lambda: validator.parse_response('[1,2]'))


def test_completion_handling():
    completion = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content='{"ok":true}', refusal=None))])
    assert validator.extract_response(completion) == '{"ok":true}'
    refused = SimpleNamespace(choices=[SimpleNamespace(finish_reason="length", message=SimpleNamespace(content="partial", refusal=None))])
    expect_error(lambda: validator.extract_response(refused))
    expect_error(lambda: validator.extract_response(SimpleNamespace(choices=[])))


if __name__ == "__main__":
    print("=== ASSESSMENT VALIDATOR TESTS ===")
    run_tests([
        ("Valid stock and inventory", test_valid_stock_and_inventory),
        ("Invalid stock values", test_invalid_stock),
        ("Invalid inventory and dates", test_invalid_inventory),
        ("Valid AI assessment", test_valid_analysis),
        ("Invalid AI assessment fields", test_invalid_analysis),
        ("Invalid recipe suggestions", test_invalid_recipes),
        ("JSON parsing and malformed JSON", test_json_parsing),
        ("AI completion handling", test_completion_handling),
    ])
