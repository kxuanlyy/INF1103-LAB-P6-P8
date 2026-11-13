import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "io_manager").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Run without displaying windows; also useful in CI/Docker with Qt installed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTableWidget

from io_manager.gui_view import GuiView
from io_manager.theme_switch import ThemeSwitch
from io_manager.calendar_date_edit import CalendarDateEdit


app = QApplication.instance() or QApplication(sys.argv)


class TestFoodRescueGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = GuiView(controller=None)

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def test_01_window_initialises(self):
        self.assertEqual(self.window.windowTitle(), "FoodRescue")
        self.assertIsNotNone(self.window.centralWidget())

    def test_02_navigation_buttons_exist(self):
        buttons = [
            "_btn_view_inv", "_btn_search_inv", "_btn_edit_inv",
            "_btn_ask_ai", "_btn_process_recipes", "_btn_view_recipes",
            "_btn_search_recipes", "_btn_inventory_alerts",
            "_btn_editbusinessrules", "_btn_exit",
        ]
        for name in buttons:
            with self.subTest(button=name):
                button = getattr(self.window, name)
                self.assertTrue(button.text().strip())
                self.assertTrue(button.isEnabled())

    def test_03_inventory_renders_records(self):
        records = [
            {"food": "Milk", "quantity": 2, "use-by": "15/11/2026"},
            {"food": "Bread", "quantity": 5, "use-by": "18/11/2026"},
        ]
        self.assertTrue(self.window.print_current_inventory(records))
        table = self.window._inventory_table
        self.assertIsInstance(table, QTableWidget)
        self.assertEqual(table.rowCount(), 2)
        self.assertEqual(table.item(0, 0).text(), "Milk")
        self.assertEqual(table.item(0, 1).text(), "2")
        self.assertEqual(table.item(1, 2).text(), "18/11/2026")

    def test_04_empty_inventory_handled(self):
        self.assertFalse(self.window.print_current_inventory([]))
        self.assertEqual(self.window._inventory_table.rowCount(), 0)

    def test_05_search_panel_opens(self):
        self.window._on_search_inventory_triggered()
        self.assertFalse(self.window._search_panel.isHidden())
        self.assertEqual(self.window._input_food.text(), "")

    def test_06_theme_changes(self):
        self.window._toggle_theme(True)
        self.assertTrue(self.window._dark_mode)
        self.window._toggle_theme(False)
        self.assertFalse(self.window._dark_mode)

    def test_07_theme_switch_widget(self):
        switch = ThemeSwitch()
        switch.setChecked(True)
        self.assertTrue(switch.isChecked())
        switch.setChecked(False)
        self.assertFalse(switch.isChecked())
        switch.close()

    def test_08_date_and_inventory_inputs(self):
        self.assertIsInstance(self.window._add_date, CalendarDateEdit)
        self.assertEqual(self.window._add_date.displayFormat(), "dd/MM/yyyy")
        self.assertEqual(self.window._add_qty.placeholderText(), "Stock Qty")
        self.assertGreater(self.window._add_category.count(), 0)


if __name__ == "__main__":
    print("=" * 60)
    print("FOODRESCUE AI - GUI TESTS")
    print("=" * 60)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestFoodRescueGUI)
    )
    print(f"FINAL RESULTS: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} TESTS PASSED")
    sys.exit(0 if result.wasSuccessful() else 1)
