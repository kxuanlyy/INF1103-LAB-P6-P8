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
import tempfile
from data_manager.recipe_results_store import RecipeResultsStore
from logic_manager.reciperesultservice import RecipeResultService, normalize_items, ingredients_match, evaluate_recipes

TEMPLATES = [{"name": "Tomato Soup", "ingredients": ["tomato", "onion"]}]
INCOMING = [
    {"name": "Tomato Soup", "ingredients": ["tomato", "onion"], "instructions": ["Cook"]},
    {"name": "Mystery Dish", "ingredients": ["rice"], "instructions": ["Boil"]},
]


def write_json(folder, name, data):
    (folder / name).write_text(json.dumps(data), encoding="utf-8")


def test_successful_workflow():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        write_json(folder, "accepted_recipe.json", TEMPLATES)
        write_json(folder, "recipes.json", INCOMING)
        result = RecipeResultService(results_store=RecipeResultsStore(folder)).create_results()
        print("  result:", result)
        assert result == {"accepted": 1, "rejected": 1}
        csv_text = (folder / "recipe_results.csv").read_text(encoding="utf-8")
        rejected_text = (folder / "rejected.txt").read_text(encoding="utf-8")
        assert "Tomato Soup" in csv_text and "Mystery Dish" in rejected_text


def test_missing_file():
    with tempfile.TemporaryDirectory() as temp:
        result = RecipeResultService(results_store=RecipeResultsStore(temp)).create_results()
        assert "error" in result and "accepted_recipe.json" in result["error"]


def test_empty_incoming():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        write_json(folder, "accepted_recipe.json", TEMPLATES)
        write_json(folder, "recipes.json", [])
        result = RecipeResultService(results_store=RecipeResultsStore(folder)).create_results()
        assert result == {"error": "recipes.json is empty"}
        assert not (folder / "recipe_results.csv").exists()


def test_custom_templates():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        write_json(folder, "accepted_recipe.json", [])
        write_json(folder, "recipes.json", INCOMING)
        result = RecipeResultService(results_store=RecipeResultsStore(folder)).create_results(accepted_recipes=TEMPLATES)
        assert result == {"accepted": 1, "rejected": 1}


def test_compatibility_wrappers():
    assert normalize_items([" MILK "]) == {"milk"}
    assert ingredients_match(["milk"], ["milk"]) is True
    accepted, rejected = evaluate_recipes(TEMPLATES, INCOMING)
    assert len(accepted) == 1 and len(rejected) == 1


if __name__ == "__main__":
    print("=== RECIPE RESULT SERVICE TESTS ===")
    run_tests([
        ("Evaluate and save temporary result files", test_successful_workflow),
        ("Missing input file error", test_missing_file),
        ("Empty incoming recipes error", test_empty_incoming),
        ("Custom accepted templates", test_custom_templates),
        ("Compatibility helper functions", test_compatibility_wrappers),
    ])
