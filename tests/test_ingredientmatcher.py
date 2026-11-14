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

from logic_manager.ingredientmatcher import IngredientMatcher


def test_capitalisation():
    assert IngredientMatcher.test_capitalisation([" Milk ", "MILK", "  Eggs  "]) == {"milk", "egg"}


def test_full_match():
    result = IngredientMatcher().compare(
        ["2 cups chopped tomatoes", "1 red onion"],
        ["tomato", "red onion"],
    )
    print("  matched:", result["matched"], "ratio:", result["match_ratio"])
    assert result["matches"] is True and result["match_ratio"] == 1.0


def test_threshold_boundary():
    matcher = IngredientMatcher(minimum_match_ratio=0.5)
    result = matcher.compare(["milk", "egg"], ["milk"])
    assert result["matches"] is True and result["match_ratio"] == 0.5
    assert result["unmatched"] == ["egg"]


def test_below_threshold():
    result = IngredientMatcher().compare(["milk", "egg", "flour"], ["milk"])
    assert result["matches"] is False and len(result["matched"]) == 1


def test_empty_and_duplicates():
    matcher = IngredientMatcher()
    assert matcher.matches([], ["milk"]) is False
    assert matcher.matches(["milk"], []) is False
    result = matcher.compare(["milk", "MILK"], ["milk"])
    assert result["matches"] is False
    assert result["matched"] == ["milk"]
    assert result["unmatched"] == ["MILK"]
    assert result["match_ratio"] == 0.5


def test_word_overlap_behaviour():
    result = IngredientMatcher().compare(["red pepper"], ["red apple"])
    assert result["matches"] is False
    assert result["matched"] == []
    assert result["unmatched"] == ["red pepper"]
    assert result["match_ratio"] == 0.0


if __name__ == "__main__":
    print("=== INGREDIENT MATCHER TESTS ===")
    run_tests([
        (""
        "Whitespace and case normalisation", test_capitalisation),
        ("Full ingredient match", test_full_match),
        ("Threshold boundary", test_threshold_boundary),
        ("Below threshold", test_below_threshold),
        ("Empty inputs and duplicates", test_empty_and_duplicates),
        ("Non-matching ingredient word overlap", test_word_overlap_behaviour),
    ])
