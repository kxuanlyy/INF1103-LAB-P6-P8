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

from logic_manager.recipeevaluator import RecipeEvaluator

TEMPLATES = [
    {"name": "Tomato Soup", "ingredients": ["tomato", "onion"]},
    {"name": "Egg Toast", "ingredients": ["egg", "bread"]},
]


def test_accepted():
    incoming = [{"name": " tomato   soup ", "ingredients": ["tomato", "onion"], "instructions": ["Chop", "Cook"]}]
    accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, incoming)
    print("  accepted:", accepted)
    assert len(accepted) == 1 and rejected == []
    assert accepted[0]["ingredients"] == "tomato, onion"
    assert accepted[0]["instructions"] == "Chop Cook"


def test_unknown_name():
    accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, [{"name": "Pizza", "ingredients": ["tomato"]}])
    assert not accepted and rejected[0]["reason"] == RecipeEvaluator.NAME_NOT_FOUND_REASON


def test_ingredient_mismatch():
    accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, [{"name": "Egg Toast", "ingredients": ["egg"]}])
    assert not accepted and len(rejected) == 1
    assert "1/2 matched" in rejected[0]["reason"] and "bread" in rejected[0]["reason"]


def test_mixed_results():
    incoming = [
        {"name": "Tomato Soup", "ingredients": ["tomato", "onion"], "instructions": []},
        {"name": "Unknown Dish", "ingredients": []},
        {"name": "Egg Toast", "ingredients": ["egg"]},
    ]
    accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, incoming)
    assert len(accepted) == 1 and len(rejected) == 2


def test_empty_and_missing_name():
    assert RecipeEvaluator().evaluate(TEMPLATES, []) == ([], [])
    accepted, rejected = RecipeEvaluator().evaluate(TEMPLATES, [{"ingredients": ["egg"]}])
    assert not accepted and rejected[0]["name"] == "Unknown Recipe"


if __name__ == "__main__":
    print("=== RECIPE EVALUATOR TESTS ===")
    run_tests([
        ("Accepted recipe and formatting", test_accepted),
        ("Unknown recipe name rejected", test_unknown_name),
        ("Ingredient mismatch rejected", test_ingredient_mismatch),
        ("Mixed accepted and rejected recipes", test_mixed_results),
        ("Empty input and missing recipe name", test_empty_and_missing_name),
    ])
