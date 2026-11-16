from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic_manager.ingredientmatcher import IngredientMatcher


class TestIngredientMatcher(unittest.TestCase):
    def test_capitalisation(self):
        self.assertEqual(
            IngredientMatcher.normalize_items([" Milk ", "MILK", "  Eggs  "]),
            {"milk", "egg"},
        )

    def test_full_match(self):
        result = IngredientMatcher().compare(
            ["2 cups chopped tomatoes", "1 red onion"],
            ["tomato", "red onion"],
        )
        self.assertTrue(result["matches"])
        self.assertEqual(result["match_ratio"], 1.0)

    def test_threshold_boundary(self):
        matcher = IngredientMatcher(minimum_match_ratio=0.5)
        result = matcher.compare(["milk", "egg"], ["milk"])
        self.assertTrue(result["matches"])
        self.assertEqual(result["match_ratio"], 0.5)
        self.assertEqual(result["unmatched"], ["egg"])

    def test_below_threshold(self):
        result = IngredientMatcher().compare(["milk", "egg", "flour"], ["milk"])
        self.assertFalse(result["matches"])
        self.assertEqual(len(result["matched"]), 1)

    def test_empty_and_duplicates(self):
        matcher = IngredientMatcher()
        self.assertFalse(matcher.matches([], ["milk"]))
        self.assertFalse(matcher.matches(["milk"], []))
        result = matcher.compare(["milk", "MILK"], ["milk"])
        self.assertFalse(result["matches"])
        self.assertEqual(result["matched"], ["milk"])
        self.assertEqual(result["unmatched"], ["MILK"])
        self.assertEqual(result["match_ratio"], 0.5)

    def test_word_overlap_behaviour(self):
        result = IngredientMatcher().compare(["red pepper"], ["red apple"])
        self.assertFalse(result["matches"])
        self.assertEqual(result["matched"], [])
        self.assertEqual(result["unmatched"], ["red pepper"])
        self.assertEqual(result["match_ratio"], 0.0)
