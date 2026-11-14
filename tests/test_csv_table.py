#Tests for data_manager/csv_table.py (CsvTable).

#Run from the project root:   python -m unittest discover tests -v

import csv
import os
import tempfile
import unittest
from unittest import mock

from data_manager.csv_table import CsvTable


class People(CsvTable):
    COLUMNS = ["name", "age"]


class CsvTableTestCase(unittest.TestCase):
    # Every test gets its own empty temp folder, so the real CSV files are never touched.

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = tmp.name
        self.path = os.path.join(self.folder, "people.csv")

    # ---- helpers ----
    def write_bytes(self, data: bytes, path=None):
        with open(path or self.path, "wb") as f:
            f.write(data)

    def write_text(self, text: str, path=None):
        self.write_bytes(text.encode("utf-8"), path)

    def read_rows(self, path=None):
        with open(path or self.path, newline="", encoding="utf-8") as f:
            return list(csv.reader(f))

    def read_bytes(self, path=None) -> bytes:
        with open(path or self.path, "rb") as f:
            return f.read()

    def table(self, text=None) -> People:
        if text is not None:
            self.write_text(text)
        return People(self.path)

    def loaded_table(self, *rows) -> People:
        # a table already loaded from a file holding the given (name, age) rows
        lines = ["name,age"] + [f"{n},{a}" for n, a in rows]
        t = self.table("\n".join(lines) + "\n")
        t.load()
        return t

    def corrupt_copies(self):
        return [f for f in os.listdir(self.folder) if ".corrupt-" in f]


class TestConstructor(CsvTableTestCase):
    def test_starts_empty_and_remembers_path(self):
        t = People(self.path)
        self.assertEqual(t.path, self.path)
        self.assertEqual(t.records, [])

    def test_base_class_has_no_columns(self):
        self.assertEqual(CsvTable.COLUMNS, [])

    def test_instances_do_not_share_records(self):
        a, b = People(self.path), People(self.path)
        a.records.append({"name": "x", "age": "1"})
        self.assertEqual(b.records, [])


class TestWrite(CsvTableTestCase):
    def test_writes_header_then_rows(self):
        People(self.path)._write([{"name": "Ann", "age": "30"}, {"name": "Bo", "age": "7"}])
        self.assertEqual(self.read_rows(), [["name", "age"], ["Ann", "30"], ["Bo", "7"]])

    def test_creates_missing_folders(self):
        nested = os.path.join(self.folder, "a", "b", "people.csv")
        People(nested)._write([])
        self.assertTrue(os.path.exists(nested))

    def test_overwrites_an_existing_file(self):
        t = self.table("name,age\nOld,1\n")
        t._write([{"name": "New", "age": "2"}])
        self.assertEqual(self.read_rows(), [["name", "age"], ["New", "2"]])

    def test_quotes_commas_and_newlines(self):
        People(self.path)._write([{"name": 'Smith, "Bob"', "age": "line1\nline2"}])
        self.assertEqual(self.read_rows()[1], ['Smith, "Bob"', "line1\nline2"])

    def test_leaves_no_temp_files_behind(self):
        People(self.path)._write([{"name": "A", "age": "1"}])
        self.assertEqual(os.listdir(self.folder), ["people.csv"])

    def test_failed_replace_keeps_original_and_removes_temp_file(self):
        self.write_text("name,age\nKeep,1\n")
        with mock.patch("os.replace", side_effect=PermissionError("locked")):
            with self.assertRaises(PermissionError):
                People(self.path)._write([{"name": "New", "age": "2"}])
        self.assertEqual(self.read_bytes(), b"name,age\nKeep,1\n")
        self.assertEqual(os.listdir(self.folder), ["people.csv"])

    def test_bad_row_raises_and_keeps_original(self):
        self.write_text("name,age\nKeep,1\n")
        with self.assertRaises(ValueError):                       # unknown column "oops"
            People(self.path)._write([{"name": "A", "age": "1", "oops": "x"}])
        self.assertEqual(self.read_bytes(), b"name,age\nKeep,1\n")
        self.assertEqual(os.listdir(self.folder), ["people.csv"])


class TestCreateEmpty(CsvTableTestCase):
    def test_creates_a_header_only_file(self):
        People(self.path)._create_empty()
        self.assertEqual(self.read_rows(), [["name", "age"]])

    def test_failure_is_logged_not_raised(self):
        t = People(self.path)
        with mock.patch.object(People, "_write", side_effect=OSError("disk full")):
            with self.assertLogs("data_manager", "ERROR") as logs:
                t._create_empty()                                 # must not raise
        self.assertIn("Could not create", logs.output[0])
        self.assertIn("disk full", logs.output[0])
        self.assertFalse(os.path.exists(self.path))


class TestQuarantine(CsvTableTestCase):
    def test_moves_the_file_aside_with_its_content(self):
        self.write_bytes(b"garbage")
        backup = People(self.path)._quarantine()
        self.assertFalse(os.path.exists(self.path))
        self.assertIn(".corrupt-", backup)
        self.assertEqual(self.read_bytes(backup), b"garbage")

    def test_never_overwrites_an_earlier_quarantined_copy(self):
        fixed = mock.MagicMock()
        fixed.now.return_value.strftime.return_value = "01012026-000000"   # same second every time
        t = People(self.path)
        backups = []
        with mock.patch("data_manager.csv_table.datetime", fixed):
            for n in range(3):
                self.write_bytes(f"copy {n}".encode())
                backups.append(t._quarantine())
        self.assertEqual(len(set(backups)), 3)
        self.assertEqual([self.read_bytes(b) for b in backups], [b"copy 0", b"copy 1", b"copy 2"])
        self.assertTrue(backups[1].endswith("-2") and backups[2].endswith("-3"))

    def test_failure_returns_none_and_logs(self):
        self.write_bytes(b"garbage")
        with mock.patch("os.replace", side_effect=OSError("denied")):
            with self.assertLogs("data_manager", "ERROR") as logs:
                result = People(self.path)._quarantine()
        self.assertIsNone(result)
        self.assertIn("denied", logs.output[0])
        self.assertTrue(os.path.exists(self.path))                # original left in place


class TestRead(CsvTableTestCase):
    def test_missing_file_gives_no_rows_and_creates_a_header_only_file(self):
        with self.assertLogs("data_manager", "WARNING") as logs:
            rows = People(self.path)._read()
        self.assertEqual(rows, [])
        self.assertIn("missing or empty", logs.output[0])
        self.assertEqual(self.read_rows(), [["name", "age"]])

    def test_zero_byte_file_is_treated_like_a_missing_one(self):
        self.write_bytes(b"")
        with self.assertLogs("data_manager", "WARNING"):
            rows = People(self.path)._read()
        self.assertEqual(rows, [])
        self.assertEqual(self.read_rows(), [["name", "age"]])
        self.assertEqual(self.corrupt_copies(), [])               # empty is not "corrupt"

    def test_reads_rows_as_dicts_of_strings(self):
        rows = self.table("name,age\nAnn,30\nBo,7\n")._read()
        self.assertEqual(rows, [{"name": "Ann", "age": "30"}, {"name": "Bo", "age": "7"}])

    def test_header_only_file_gives_no_rows(self):
        self.assertEqual(self.table("name,age\n")._read(), [])

    def test_values_are_stripped(self):
        self.assertEqual(self.table("name,age\n  Ann  , 30 \n")._read(), [{"name": "Ann", "age": "30"}])

    def test_blank_rows_are_skipped(self):
        rows = self.table("name,age\nAnn,1\n\n,\n  ,  \nBo,2\n")._read()
        self.assertEqual([r["name"] for r in rows], ["Ann", "Bo"])

    def test_column_order_in_the_file_does_not_matter(self):
        self.assertEqual(self.table("age,name\n30,Ann\n")._read(), [{"name": "Ann", "age": "30"}])

    def test_extra_columns_are_ignored(self):
        self.assertEqual(self.table("name,age,colour\nAnn,30,red\n")._read(), [{"name": "Ann", "age": "30"}])

    def test_short_rows_get_empty_strings(self):
        self.assertEqual(self.table("name,age\nAnn\n")._read(), [{"name": "Ann", "age": ""}])

    def test_utf8_bom_is_accepted(self):
        self.write_bytes(b"\xef\xbb\xbfname,age\nAnn,30\n")
        self.assertEqual(People(self.path)._read(), [{"name": "Ann", "age": "30"}])

    def test_windows_line_endings_and_no_final_newline(self):
        self.write_bytes(b"name,age\r\nAnn,30\r\nBo,7")
        self.assertEqual([r["name"] for r in People(self.path)._read()], ["Ann", "Bo"])

    def test_quoted_commas_and_newlines_survive(self):
        rows = self.table('name,age\n"Smith, Bob","a\nb"\n')._read()
        self.assertEqual(rows, [{"name": "Smith, Bob", "age": "a\nb"}])

    def test_non_ascii_text(self):
        self.assertEqual(self.table("name,age\nJosé 🍎,30\n")._read()[0]["name"], "José 🍎")

    def assert_quarantined_and_reset(self, rows):
        self.assertEqual(rows, [])
        self.assertEqual(len(self.corrupt_copies()), 1)
        self.assertEqual(self.read_rows(), [["name", "age"]])      # fresh header-only replacement

    def test_missing_required_column_is_quarantined(self):
        t = self.table("name,colour\nAnn,red\n")
        with self.assertLogs("data_manager", "ERROR") as logs:
            rows = t._read()
        self.assertIn("required column(s) missing: age", logs.output[0])
        self.assert_quarantined_and_reset(rows)
        # the original data is kept in the quarantined copy
        self.assertEqual(self.read_bytes(os.path.join(self.folder, self.corrupt_copies()[0])), b"name,colour\nAnn,red\n")

    def test_invalid_utf8_is_quarantined(self):
        self.write_bytes(b"name,age\n\xff\xfe,1\n")
        with self.assertLogs("data_manager", "ERROR"):
            rows = People(self.path)._read()
        self.assert_quarantined_and_reset(rows)

    def test_binary_garbage_is_quarantined(self):
        self.write_bytes(bytes(range(256)) * 3)
        with self.assertLogs("data_manager", "ERROR"):
            rows = People(self.path)._read()
        self.assert_quarantined_and_reset(rows)

    def test_unterminated_quote_is_quarantined(self):
        t = self.table('name,age\n"abc,1\n')
        with self.assertLogs("data_manager", "ERROR"):
            rows = t._read()
        self.assert_quarantined_and_reset(rows)

    def test_corrupt_file_that_cannot_be_moved_is_left_in_place(self):
        t = self.table("foo,bar\n1,2\n")
        with mock.patch.object(People, "_quarantine", return_value=None):
            with self.assertLogs("data_manager", "ERROR") as logs:
                rows = t._read()
        self.assertEqual(rows, [])
        self.assertIn("Original left in place", logs.output[0])


class TestLoadAndSave(CsvTableTestCase):
    def test_default_hooks_change_nothing(self):
        t = People(self.path)
        rows = [{"name": "A", "age": "1"}]
        self.assertIs(t._clean(rows), rows)
        t.records.append(rows[0])
        self.assertIs(t._rows_for_saving(), t.records)

    def test_load_fills_records(self):
        t = self.loaded_table(("Ann", 30), ("Bo", 7))
        self.assertEqual(t.records, [{"name": "Ann", "age": "30"}, {"name": "Bo", "age": "7"}])

    def test_load_replaces_the_list_in_place(self):
        t = self.loaded_table(("Ann", 30))
        outside_reference = t.records
        self.write_text("name,age\nZed,99\nYan,98\n")
        t.load()
        self.assertIs(t.records, outside_reference)               # same list object
        self.assertEqual([r["name"] for r in outside_reference], ["Zed", "Yan"])

    def test_loading_twice_does_not_duplicate_rows(self):
        t = self.loaded_table(("Ann", 30))
        t.load()
        t.load()
        self.assertEqual(len(t.records), 1)

    def test_load_of_a_missing_file_creates_it(self):
        t = People(self.path)
        with self.assertLogs("data_manager", "WARNING"):
            t.load()
        self.assertEqual(t.records, [])
        self.assertTrue(os.path.exists(self.path))

    def test_load_uses_the_clean_hook(self):
        class Shouty(People):
            def _clean(self, rows):
                return [{**r, "name": r["name"].upper()} for r in rows]
        self.write_text("name,age\nann,1\n")
        t = Shouty(self.path)
        t.load()
        self.assertEqual(t.records[0]["name"], "ANN")

    def test_save_uses_the_rows_for_saving_hook(self):
        class Hidden(People):
            def _rows_for_saving(self):
                return [{"name": r["name"], "age": "?"} for r in self.records]
        t = Hidden(self.path)
        t.records.append({"name": "Ann", "age": "30"})
        t.save()
        self.assertEqual(self.read_rows(), [["name", "age"], ["Ann", "?"]])

    def test_save_then_load_round_trip(self):
        t = People(self.path)
        t.records.extend([{"name": "A, B", "age": "1"}, {"name": "C", "age": "2"}])
        t.save()
        other = People(self.path)
        other.load()
        self.assertEqual(other.records, t.records)


class TestCheckIndex(CsvTableTestCase):
    def test_valid_positions_pass(self):
        t = self.loaded_table(("A", 1), ("B", 2), ("C", 3))
        for index in (0, 1, 2):
            with self.subTest(index=index):
                t._check_index(index)                             # no exception

    def test_invalid_positions_raise_indexerror(self):
        t = self.loaded_table(("A", 1), ("B", 2))
        for index in (-1, 2, 99, True, False, "0", 1.0, None):
            with self.subTest(index=index):
                with self.assertRaises(IndexError):
                    t._check_index(index)

    def test_message_names_the_index_and_the_size(self):
        t = self.loaded_table(("A", 1))
        with self.assertRaisesRegex(IndexError, r"No record at index 5.*1 record"):
            t._check_index(5)

    def test_empty_table_has_no_valid_index(self):
        with self.assertRaises(IndexError):
            People(self.path)._check_index(0)


class TestChangeBookkeeping(CsvTableTestCase):
    # add / replace / delete write to disk straight away and undo the change in memory if the write fails.

    def fail_saves(self):
        return mock.patch("os.replace", side_effect=PermissionError("locked"))

    # ---- append ----
    def test_append_and_save(self):
        t = self.loaded_table(("A", 1))
        record = {"name": "B", "age": "2"}
        self.assertIs(t._append_and_save(record), record)
        self.assertEqual(t.records[-1], record)
        self.assertEqual(self.read_rows(), [["name", "age"], ["A", "1"], ["B", "2"]])

    def test_append_failure_removes_the_record_and_reraises(self):
        t = self.loaded_table(("A", 1))
        before = self.read_bytes()
        with self.fail_saves(), self.assertLogs("data_manager", "ERROR"):
            with self.assertRaises(PermissionError):
                t._append_and_save({"name": "B", "age": "2"})
        self.assertEqual([r["name"] for r in t.records], ["A"])
        self.assertEqual(self.read_bytes(), before)

    # ---- replace ----
    def test_replace_and_save(self):
        t = self.loaded_table(("A", 1), ("B", 2))
        new = {"name": "Z", "age": "9"}
        self.assertIs(t._replace_and_save(1, new), new)
        self.assertEqual(t.records[1], new)
        self.assertEqual(self.read_rows()[2], ["Z", "9"])

    def test_replace_failure_puts_the_old_record_back(self):
        t = self.loaded_table(("A", 1), ("B", 2))
        old = t.records[1]
        with self.fail_saves(), self.assertLogs("data_manager", "ERROR"):
            with self.assertRaises(PermissionError):
                t._replace_and_save(1, {"name": "Z", "age": "9"})
        self.assertIs(t.records[1], old)

    # ---- delete ----
    def test_delete_returns_the_removed_record_and_saves(self):
        t = self.loaded_table(("A", 1), ("B", 2), ("C", 3))
        removed = t.delete(1)
        self.assertEqual(removed, {"name": "B", "age": "2"})
        self.assertEqual([r["name"] for r in t.records], ["A", "C"])
        self.assertEqual(self.read_rows(), [["name", "age"], ["A", "1"], ["C", "3"]])

    def test_delete_with_a_bad_index_changes_nothing(self):
        t = self.loaded_table(("A", 1))
        before = self.read_bytes()
        for index in (-1, 1, True):
            with self.subTest(index=index):
                with self.assertRaises(IndexError):
                    t.delete(index)
        self.assertEqual(len(t.records), 1)
        self.assertEqual(self.read_bytes(), before)

    def test_delete_failure_restores_the_record_at_the_same_position(self):
        t = self.loaded_table(("A", 1), ("B", 2), ("C", 3))
        with self.fail_saves(), self.assertLogs("data_manager", "ERROR"):
            with self.assertRaises(PermissionError):
                t.delete(1)
        self.assertEqual([r["name"] for r in t.records], ["A", "B", "C"])

    def test_deleting_everything_leaves_a_header_only_file(self):
        t = self.loaded_table(("A", 1))
        t.delete(0)
        self.assertEqual(self.read_rows(), [["name", "age"]])


class TestMatchingHelpers(CsvTableTestCase):
    def test_contains(self):
        self.assertTrue(CsvTable._contains("Whole Milk", "milk"))
        self.assertTrue(CsvTable._contains("Whole Milk", "WHOLE"))
        self.assertFalse(CsvTable._contains("Whole Milk", "cheese"))

    def test_contains_with_none_means_no_filter(self):
        self.assertTrue(CsvTable._contains("anything", None))
        self.assertTrue(CsvTable._contains("", None))

    def test_equals(self):
        self.assertTrue(CsvTable._equals("High", "high"))
        self.assertFalse(CsvTable._equals("High", "hig"))          # exact, not substring

    def test_equals_with_none_means_no_filter(self):
        self.assertTrue(CsvTable._equals("anything", None))

    def test_as_list(self):
        self.assertEqual(CsvTable._as_list(None), [])
        self.assertEqual(CsvTable._as_list("milk"), ["milk"])     # a string is ONE item, not letters
        self.assertEqual(CsvTable._as_list(["a", "b"]), ["a", "b"])
        self.assertEqual(CsvTable._as_list(("a", "b")), ["a", "b"])
        self.assertEqual(CsvTable._as_list(x for x in "ab"), ["a", "b"])
        self.assertEqual(CsvTable._as_list([]), [])

    def test_as_list_returns_a_copy(self):
        original = ["a"]
        copy = CsvTable._as_list(original)
        copy.append("b")
        self.assertEqual(original, ["a"])


if __name__ == "__main__":
    unittest.main()
