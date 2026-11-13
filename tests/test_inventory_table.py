#Tests for data_manager/inventory_table.py (InventoryTable)
import csv
import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from data_manager.inventory_table import (
    DATE_FORMAT, INVENTORY_ARGS, INVENTORY_COLUMNS, INVENTORY_INT_FIELDS, InventoryTable,
)

HEADER = ",".join(INVENTORY_COLUMNS)
# food, category, use-by, storage, days, risk, allergen, demand, quantity
FIXTURE = [
    "milk,Dairy,10/11/2026,Chilled,3,High,Milk,High,10",
    "bread,Bakery,20/11/2026,Ambient,13,Medium,\"Wheat, Gluten\",Medium,5",
    "rice,Grains,01/01/2027,Ambient dry,50,Low,,Low,20",
    "apple,Fruit,15/11/2026,Chilled,8,Low,None,High,0",
    "cake,Bakery,not a date,Ambient,abc,High,\"Eggs, Wheat\",Low,",
    "Tofu,Protein,05/11/2026,Chilled,-2,High,Soy,High,7",
]


class InventoryTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "inventory.csv")

    def make(self, lines=None) -> InventoryTable:
        lines = FIXTURE if lines is None else lines
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(HEADER + "\n" + "\n".join(lines) + ("\n" if lines else ""))
        t = InventoryTable(self.path)
        with self.assertLogs("data_manager", "WARNING") if lines is FIXTURE else _nullctx():
            t.load()
        return t

    def disk_rows(self):
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def foods(self, records):
        return [r["food"] for r in records]


class _nullctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestConstants(unittest.TestCase):
    def test_columns(self):
        self.assertEqual(len(INVENTORY_COLUMNS), 9)
        self.assertEqual(InventoryTable.COLUMNS, INVENTORY_COLUMNS)

    def test_int_fields(self):
        self.assertEqual(INVENTORY_INT_FIELDS, ("days_to_expiry", "quantity"))

    def test_date_format(self):
        self.assertEqual(DATE_FORMAT, "%d/%m/%Y")

    def test_args_map_to_real_columns(self):
        self.assertEqual(set(INVENTORY_ARGS.values()), set(INVENTORY_COLUMNS))
        self.assertEqual(INVENTORY_ARGS["use_by"], "use-by")
        self.assertEqual(INVENTORY_ARGS["storage_condition"], "storage condition")


class TestDates(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(InventoryTable._parse_date("05/11/2026"), datetime(2026, 11, 5))

    def test_parse_date_failures_give_none(self):
        for bad in ("", "nonsense", "2026-11-05", "31/02/2026", "05-11-2026", None, 5):
            with self.subTest(bad=bad):
                self.assertIsNone(InventoryTable._parse_date(bad))

    def test_to_date_accepts_both_separators(self):
        self.assertEqual(InventoryTable._to_date("05/11/2026"), datetime(2026, 11, 5))
        self.assertEqual(InventoryTable._to_date("05-11-2026"), datetime(2026, 11, 5))

    def test_to_date_passes_through_none_and_datetime(self):
        d = datetime(2026, 1, 1)
        self.assertIsNone(InventoryTable._to_date(None))
        self.assertIs(InventoryTable._to_date(d), d)

    def test_to_date_rejects_garbage(self):
        with self.assertRaisesRegex(ValueError, r"Unrecognised date 'tomorrow'.*DD-MM-YYYY"):
            InventoryTable._to_date("tomorrow")


class TestLoadClean(InventoryTestCase):
    def test_numbers_become_ints(self):
        t = self.make()
        self.assertEqual(t.records[0]["days_to_expiry"], 3)
        self.assertEqual(t.records[0]["quantity"], 10)
        self.assertIsInstance(t.records[0]["quantity"], int)

    def test_negative_numbers_are_kept(self):
        self.assertEqual(self.make().records[5]["days_to_expiry"], -2)

    def test_bad_or_blank_numbers_become_none_with_warning(self):
        t = InventoryTable(self.path)
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(HEADER + "\ncake,Bakery,x,Ambient,abc,High,,Low,\n")
        with self.assertLogs("data_manager", "WARNING") as logs:
            t.load()
        self.assertIsNone(t.records[0]["days_to_expiry"])
        self.assertIsNone(t.records[0]["quantity"])
        self.assertEqual(len(logs.output), 2)
        self.assertIn("'abc'", logs.output[0])
        self.assertIn("cake", logs.output[0])

    def test_unnamed_row_wording(self):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(HEADER + "\n,Bakery,x,Ambient,1,High,,Low,zz\n")
        t = InventoryTable(self.path)
        with self.assertLogs("data_manager", "WARNING") as logs:
            t.load()
        self.assertIn("(unnamed row)", logs.output[0])

    def test_float_text_is_not_a_whole_number(self):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(HEADER + "\nx,c,d,s,2.5,High,,Low,3\n")
        t = InventoryTable(self.path)
        with self.assertLogs("data_manager", "WARNING"):
            t.load()
        self.assertIsNone(t.records[0]["days_to_expiry"])
        self.assertEqual(t.records[0]["quantity"], 3)

    def test_empty_inventory_loads_with_no_records(self):
        t = self.make([])
        self.assertEqual(t.records, [])


class TestSaving(InventoryTestCase):
    def test_none_is_saved_as_blank(self):
        t = self.make()
        t.save()
        rows = self.disk_rows()
        self.assertEqual(rows[4]["days_to_expiry"], "")
        self.assertEqual(rows[4]["quantity"], "")

    def test_rows_for_saving_does_not_change_memory(self):
        t = self.make()
        t._rows_for_saving()
        self.assertIsNone(t.records[4]["days_to_expiry"])

    def test_round_trip_keeps_everything(self):
        t = self.make()
        before = [dict(r) for r in t.records]
        t.save()
        again = InventoryTable(self.path)
        with self.assertLogs("data_manager", "WARNING"):
            again.load()
        self.assertEqual(again.records, before)


class TestAdd(InventoryTestCase):
    def new(self, t, **over):
        args = dict(food="Cheese", food_category="Dairy", use_by="01/12/2026",
                    storage_condition="Chilled", days_to_expiry=20, waste_risk_level="Low")
        args.update(over)
        return t.add(**args)

    def test_add_appends_and_saves(self):
        t = self.make([])
        rec = self.new(t)
        self.assertEqual(t.records, [rec])
        self.assertEqual(rec["food"], "Cheese")
        self.assertEqual(self.disk_rows()[0]["food"], "Cheese")

    def test_defaults(self):
        t = self.make([])
        rec = self.new(t)
        self.assertEqual(rec["allergen info"], "")
        self.assertEqual(rec["demand level"], "")
        self.assertEqual(rec["quantity"], 0)

    def test_values_are_stripped_and_ints_cast(self):
        t = self.make([])
        rec = self.new(t, food="  Cheese ", food_category=" Dairy ", days_to_expiry="7",
                       quantity="4", allergen_info=" Milk ", demand_level=" High ")
        self.assertEqual(rec["food"], "Cheese")
        self.assertEqual(rec["food_category"], "Dairy")
        self.assertEqual(rec["days_to_expiry"], 7)
        self.assertEqual(rec["quantity"], 4)
        self.assertEqual(rec["allergen info"], "Milk")
        self.assertEqual(rec["demand level"], "High")

    def test_blank_food_is_rejected_and_nothing_saved(self):
        t = self.make([])
        for bad in ("", "   "):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "food is required"):
                    self.new(t, food=bad)
        self.assertEqual(t.records, [])

    def test_non_numeric_days_raises(self):
        t = self.make([])
        with self.assertRaises(ValueError):
            self.new(t, days_to_expiry="soon")
        self.assertEqual(t.records, [])

    def test_failed_save_rolls_back(self):
        t = self.make([])
        with mock.patch("os.replace", side_effect=PermissionError("locked")):
            with self.assertLogs("data_manager", "ERROR"):
                with self.assertRaises(PermissionError):
                    self.new(t)
        self.assertEqual(t.records, [])

    def test_added_item_can_be_found(self):
        t = self.make()
        self.new(t, food="Zucchini")
        self.assertEqual(self.foods(t.search(food="zucc")), ["Zucchini"])


class TestUpdate(InventoryTestCase):
    def test_changes_only_the_given_fields_and_saves(self):
        t = self.make()
        rec = t.update(0, quantity=99, storage_condition=" Frozen ")
        self.assertEqual(rec["quantity"], 99)
        self.assertEqual(rec["storage condition"], "Frozen")
        self.assertEqual(rec["food"], "milk")
        self.assertEqual(t.records[0], rec)
        self.assertEqual(self.disk_rows()[0]["quantity"], "99")

    def test_int_fields_are_cast(self):
        t = self.make()
        self.assertEqual(t.update(0, days_to_expiry="12")["days_to_expiry"], 12)

    def test_none_clears_text_fields(self):
        t = self.make()
        self.assertEqual(t.update(0, allergen_info=None)["allergen info"], "")

    def test_use_by_keyword_maps_to_column(self):
        t = self.make()
        self.assertEqual(t.update(0, use_by="01/01/2030")["use-by"], "01/01/2030")

    def test_unknown_field_rejected(self):
        t = self.make()
        with self.assertRaisesRegex(ValueError, "Unknown inventory field.*colour"):
            t.update(0, colour="red")

    def test_column_names_are_not_keywords(self):
        t = self.make()
        with self.assertRaises(ValueError):
            t.update(0, **{"use-by": "01/01/2030"})

    def test_blank_food_rejected_and_record_unchanged(self):
        t = self.make()
        with self.assertRaisesRegex(ValueError, "food is required"):
            t.update(0, food="  ")
        self.assertEqual(t.records[0]["food"], "milk")

    def test_bad_index(self):
        t = self.make()
        for bad in (-1, 6, True):
            with self.subTest(bad=bad):
                with self.assertRaises(IndexError):
                    t.update(bad, quantity=1)

    def test_bad_number_leaves_record_unchanged(self):
        t = self.make()
        with self.assertRaises(ValueError):
            t.update(0, quantity="lots")
        self.assertEqual(t.records[0]["quantity"], 10)

    def test_failed_save_restores_old_record(self):
        t = self.make()
        old = t.records[0]
        with mock.patch("os.replace", side_effect=PermissionError("locked")):
            with self.assertLogs("data_manager", "ERROR"):
                with self.assertRaises(PermissionError):
                    t.update(0, quantity=1)
        self.assertIs(t.records[0], old)
        self.assertEqual(old["quantity"], 10)

    def test_update_with_no_changes_is_allowed(self):
        t = self.make()
        self.assertEqual(t.update(0), t.records[0])


class TestDelete(InventoryTestCase):
    def test_delete_inventory_item(self):
        t = self.make()
        gone = t.delete(0)
        self.assertEqual(gone["food"], "milk")
        self.assertEqual(len(t.records), 5)
        self.assertEqual(len(self.disk_rows()), 5)


class TestSearch(InventoryTestCase):
    def setUp(self):
        super().setUp()
        self.t = self.make()

    def found(self, **kw):
        return self.foods(self.t.search(**kw))

    def test_no_filters_returns_everything(self):
        self.assertEqual(len(self.t.search()), 6)

    def test_returns_the_actual_records(self):
        self.assertIs(self.t.search(food="milk")[0], self.t.records[0])

    def test_food_substring_case_insensitive(self):
        self.assertEqual(self.found(food="IL"), ["milk"])
        self.assertEqual(self.found(food="tofu"), ["Tofu"])
        self.assertEqual(self.found(food="zzz"), [])

    def test_category_exact(self):
        self.assertEqual(self.found(food_category="bakery"), ["bread", "cake"])
        self.assertEqual(self.found(food_category="bake"), [])

    def test_use_by_before_is_inclusive(self):
        self.assertEqual(self.found(use_by_before="10/11/2026"), ["milk", "Tofu"])

    def test_use_by_after_is_inclusive(self):
        self.assertEqual(self.found(use_by_after="20/11/2026"), ["bread", "rice"])

    def test_use_by_range(self):
        self.assertEqual(self.found(use_by_after="10/11/2026", use_by_before="15/11/2026"), ["milk", "apple"])

    def test_use_by_accepts_dashes_and_datetimes(self):
        self.assertEqual(self.found(use_by_before="10-11-2026"), ["milk", "Tofu"])
        self.assertEqual(self.found(use_by_before=datetime(2026, 11, 10)), ["milk", "Tofu"])

    def test_unparsable_use_by_excluded_from_date_filters(self):
        self.assertNotIn("cake", self.found(use_by_before="31/12/2099"))
        self.assertNotIn("cake", self.found(use_by_after="01/01/1990"))
        self.assertIn("cake", self.found())

    def test_bad_filter_date_raises(self):
        with self.assertRaises(ValueError):
            self.t.search(use_by_before="soon")

    def test_storage_substring(self):
        self.assertEqual(self.found(storage_condition="ambient"), ["bread", "rice", "cake"])
        self.assertEqual(self.found(storage_condition="dry"), ["rice"])

    def test_days_range(self):
        self.assertEqual(self.found(min_days_to_expiry=8), ["bread", "rice", "apple"])
        self.assertEqual(self.found(max_days_to_expiry=3), ["milk", "Tofu"])
        self.assertEqual(self.found(min_days_to_expiry=3, max_days_to_expiry=13), ["milk", "bread", "apple"])

    def test_days_bounds_are_inclusive_and_zero_counts(self):
        self.assertEqual(self.found(min_days_to_expiry=3, max_days_to_expiry=3), ["milk"])
        self.assertEqual(self.found(max_days_to_expiry=0), ["Tofu"])

    def test_missing_days_excluded_by_any_bound(self):
        self.assertNotIn("cake", self.found(min_days_to_expiry=-1000))
        self.assertNotIn("cake", self.found(max_days_to_expiry=1000))

    def test_risk_exact(self):
        self.assertEqual(self.found(waste_risk_level="high"), ["milk", "cake", "Tofu"])
        self.assertEqual(self.found(waste_risk_level="hig"), [])

    def test_allergen_substring(self):
        self.assertEqual(self.found(allergen="wheat"), ["bread", "cake"])
        self.assertEqual(self.found(allergen=""), self.found())

    def test_exclude_allergen(self):
        self.assertEqual(self.found(exclude_allergen="wheat"), ["milk", "rice", "apple", "Tofu"])

    def test_allergen_free_only_blank_rows(self):
        # a literal "None" in the data is not blank, so it is not returned
        self.assertEqual(self.found(allergen_free=True), ["rice"])

    def test_allergen_free_false_is_ignored(self):
        self.assertEqual(len(self.t.search(allergen_free=False)), 6)

    def test_demand_exact(self):
        self.assertEqual(self.found(demand_level="high"), ["milk", "apple", "Tofu"])

    def test_quantity_range(self):
        self.assertEqual(self.found(min_quantity=10), ["milk", "rice"])
        self.assertEqual(self.found(max_quantity=5), ["bread", "apple"])
        self.assertEqual(self.found(min_quantity=0, max_quantity=0), ["apple"])

    def test_missing_quantity_excluded_by_any_bound(self):
        self.assertNotIn("cake", self.found(min_quantity=-1000))
        self.assertNotIn("cake", self.found(max_quantity=1000))

    def test_item_id_is_position_plus_one(self):
        self.assertEqual(self.found(item_id=1), ["milk"])
        self.assertEqual(self.found(item_id=6), ["Tofu"])

    def test_item_id_out_of_range_finds_nothing(self):
        for bad in (0, -1, 7, 99):
            with self.subTest(bad=bad):
                self.assertEqual(self.found(item_id=bad), [])

    def test_item_id_combines_with_other_filters(self):
        self.assertEqual(self.found(item_id=1, food_category="Bakery"), [])
        self.assertEqual(self.found(item_id=2, food_category="Bakery"), ["bread"])

    def test_filters_combine_with_and(self):
        self.assertEqual(self.found(food_category="Bakery", waste_risk_level="High"), ["cake"])
        self.assertEqual(self.found(storage_condition="chilled", demand_level="high",
                                    max_quantity=5), ["apple"])

    def test_empty_table(self):
        self.assertEqual(self.make([]).search(food="x", min_quantity=1), [])


if __name__ == "__main__":
    unittest.main()
