#Tests for data_manager/inventory_filter.py (InventoryFilter)
import unittest

from data_manager.inventory_filter import InventoryFilter


def row(food="x", category="Dairy", storage="Chilled", risk="High", allergen="", demand="High"):
    return {
        "food": food, "food_category": category, "use-by": "01/01/2030",
        "storage condition": storage, "days_to_expiry": 5, "waste_risk_level": risk,
        "allergen info": allergen, "demand level": demand, "quantity": 1,
    }


ROWS = [
    row("milk", "Dairy", "Chilled", "High", "Milk", "High"),
    row("bread", "Bakery", "Ambient", "Medium", "Wheat, Gluten", "Medium"),
    row("rice", "Grains", "Ambient dry", "Low", "", "Low"),
    row("apple", "Fruit", "Chilled", "Low", "None", "High"),
    row("cake", "Bakery", "Ambient", "High", "Eggs, Wheat", "Low"),
]


def foods(records):
    return [r["food"] for r in records]


class TestWanted(unittest.TestCase):
    def test_none_gives_empty_list(self):
        self.assertEqual(InventoryFilter._wanted(None), [])

    def test_string_becomes_one_item(self):
        self.assertEqual(InventoryFilter._wanted("Dairy"), ["Dairy"])

    def test_iterables_are_cleaned(self):
        self.assertEqual(InventoryFilter._wanted([" a ", "", None, "  ", "b"]), ["a", "b"])
        self.assertEqual(InventoryFilter._wanted(("a",)), ["a"])
        self.assertEqual(InventoryFilter._wanted({"a"}), ["a"])

    def test_blank_string_gives_empty_list(self):
        self.assertEqual(InventoryFilter._wanted("   "), [])
        self.assertEqual(InventoryFilter._wanted(""), [])


class TestHelpers(unittest.TestCase):
    def test_equals_is_case_insensitive_and_exact(self):
        self.assertTrue(InventoryFilter._equals("High", "high"))
        self.assertFalse(InventoryFilter._equals("High", "hig"))

    def test_contains_is_case_insensitive_substring(self):
        self.assertTrue(InventoryFilter._contains("Ambient dry", "DRY"))
        self.assertFalse(InventoryFilter._contains("Ambient", "dry"))

    def test_has_allergen_substring(self):
        self.assertTrue(InventoryFilter._has_allergen("Eggs, Wheat", "wheat"))
        self.assertFalse(InventoryFilter._has_allergen("Eggs", "wheat"))

    def test_has_allergen_none_keyword(self):
        for info in ("", "  ", "None", "none", " NONE "):
            with self.subTest(info=info):
                self.assertTrue(InventoryFilter._has_allergen(info, "none"))
                self.assertTrue(InventoryFilter._has_allergen(info, "None"))
        self.assertFalse(InventoryFilter._has_allergen("Milk", "none"))

    def test_none_keyword_is_not_a_substring_match(self):
        self.assertFalse(InventoryFilter._has_allergen("Nonexistent nut", "none"))


class TestConstructorAndIsActive(unittest.TestCase):
    def test_no_arguments_is_inactive(self):
        f = InventoryFilter()
        self.assertFalse(f.is_active())

    def test_blank_values_are_inactive(self):
        self.assertFalse(InventoryFilter(food_category="", allergen=[None, " "]).is_active())

    def test_each_filter_activates(self):
        for name in ("food_category", "storage_condition", "waste_risk_level",
                     "allergen", "demand_level", "exclude_allergen"):
            with self.subTest(name=name):
                self.assertTrue(InventoryFilter(**{name: "x"}).is_active())

    def test_values_stored_as_lists(self):
        f = InventoryFilter(food_category="Dairy", allergen=["a", "b"])
        self.assertEqual(f.food_category, ["Dairy"])
        self.assertEqual(f.allergen, ["a", "b"])
        self.assertEqual(f.demand_level, [])


class TestMatches(unittest.TestCase):
    def test_inactive_filter_matches_everything(self):
        f = InventoryFilter()
        self.assertTrue(all(f.matches(r) for r in ROWS))

    def test_category_is_exact(self):
        self.assertEqual(foods(InventoryFilter(food_category="bakery").apply(ROWS)), ["bread", "cake"])
        self.assertEqual(InventoryFilter(food_category="Bake").apply(ROWS), [])

    def test_multiple_categories_are_or(self):
        f = InventoryFilter(food_category=["Dairy", "Fruit"])
        self.assertEqual(foods(f.apply(ROWS)), ["milk", "apple"])

    def test_storage_is_substring(self):
        self.assertEqual(foods(InventoryFilter(storage_condition="ambient").apply(ROWS)),
                         ["bread", "rice", "cake"])
        self.assertEqual(foods(InventoryFilter(storage_condition="dry").apply(ROWS)), ["rice"])

    def test_risk_is_exact(self):
        self.assertEqual(foods(InventoryFilter(waste_risk_level="high").apply(ROWS)), ["milk", "cake"])

    def test_demand_is_exact(self):
        self.assertEqual(foods(InventoryFilter(demand_level="LOW").apply(ROWS)), ["rice", "cake"])

    def test_allergen_substring(self):
        self.assertEqual(foods(InventoryFilter(allergen="wheat").apply(ROWS)), ["bread", "cake"])

    def test_allergen_none_means_blank_or_none(self):
        self.assertEqual(foods(InventoryFilter(allergen="none").apply(ROWS)), ["rice", "apple"])

    def test_multiple_allergens_are_or(self):
        self.assertEqual(foods(InventoryFilter(allergen=["milk", "eggs"]).apply(ROWS)), ["milk", "cake"])

    def test_exclude_allergen(self):
        self.assertEqual(foods(InventoryFilter(exclude_allergen="wheat").apply(ROWS)),
                         ["milk", "rice", "apple"])

    def test_exclude_multiple_allergens_drops_any(self):
        self.assertEqual(foods(InventoryFilter(exclude_allergen=["wheat", "milk"]).apply(ROWS)),
                         ["rice", "apple"])

    def test_exclude_none_keeps_only_rows_with_allergens(self):
        self.assertEqual(foods(InventoryFilter(exclude_allergen="none").apply(ROWS)),
                         ["milk", "bread", "cake"])

    def test_filters_combine_with_and(self):
        f = InventoryFilter(food_category="Bakery", waste_risk_level="High", exclude_allergen="milk")
        self.assertEqual(foods(f.apply(ROWS)), ["cake"])
        f = InventoryFilter(food_category="Bakery", demand_level="High")
        self.assertEqual(f.apply(ROWS), [])

    def test_allergen_and_exclude_can_conflict(self):
        f = InventoryFilter(allergen="wheat", exclude_allergen="wheat")
        self.assertEqual(f.apply(ROWS), [])


class TestApply(unittest.TestCase):
    def test_returns_same_row_objects_in_original_order(self):
        result = InventoryFilter(food_category="Bakery").apply(ROWS)
        self.assertIs(result[0], ROWS[1])
        self.assertIs(result[1], ROWS[4])

    def test_returns_a_new_list(self):
        result = InventoryFilter().apply(ROWS)
        self.assertEqual(result, ROWS)
        self.assertIsNot(result, ROWS)

    def test_accepts_any_iterable(self):
        self.assertEqual(foods(InventoryFilter(food_category="Dairy").apply(iter(ROWS))), ["milk"])

    def test_empty_input(self):
        self.assertEqual(InventoryFilter(food_category="x").apply([]), [])


class TestRepr(unittest.TestCase):
    def test_inactive(self):
        self.assertEqual(repr(InventoryFilter()), "InventoryFilter()")

    def test_shows_only_used_filters(self):
        text = repr(InventoryFilter(food_category="Dairy", allergen=["a", "b"]))
        self.assertTrue(text.startswith("InventoryFilter("))
        self.assertIn("food_category=['Dairy']", text)
        self.assertIn("allergen=['a', 'b']", text)
        self.assertNotIn("demand_level", text)


if __name__ == "__main__":
    unittest.main()
