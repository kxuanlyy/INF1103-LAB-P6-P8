import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "io_manager").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Run without displaying windows; also useful in CI/Docker with Qt installed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QTableWidget, QTableWidgetItem,
)

from io_manager.gui_view import GuiView
from io_manager.theme_switch import ThemeSwitch
from io_manager.calendar_date_edit import CalendarDateEdit
from io_manager.main_window_style import (
    APPLICATION_QSS, _NoFocusItemDelegate, theme_colors,
)


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

    def test_07_checkbox_indicators_are_styled_in_both_themes(self):
        dark_styles = theme_colors(APPLICATION_QSS, True)
        light_styles = theme_colors(APPLICATION_QSS, False)

        for styles in (dark_styles, light_styles):
            self.assertIn("QCheckBox::indicator:disabled", styles)
            self.assertIn("QCheckBox::indicator:checked", styles)
        self.assertIn("border: 1px solid #718179", dark_styles)
        self.assertIn("border: 1px solid #879a8e", light_styles)
        self.assertIn(
            "QCheckBox#ExpiredAlertCheckbox::indicator:checked",
            dark_styles,
        )
        self.assertIn("background-color: #573c40", dark_styles)
        self.assertIn("border-color: #b57a7d", dark_styles)
        self.assertIn("background-color: #f1d9d9", light_styles)
        self.assertIn("border-color: #d4a4a4", light_styles)

    def test_08_theme_switch_widget(self):
        switch = ThemeSwitch()
        switch.setChecked(True)
        self.assertTrue(switch.isChecked())
        switch.setChecked(False)
        self.assertFalse(switch.isChecked())
        switch.close()

    def test_09_date_and_inventory_inputs(self):
        self.assertIsInstance(self.window._add_date, CalendarDateEdit)
        self.assertEqual(self.window._add_date.displayFormat(), "dd/MM/yyyy")
        self.assertEqual(self.window._add_qty.placeholderText(), "Stock Qty")
        self.assertGreater(self.window._add_category.count(), 0)

    def test_10_home_alert_banner_surfaces_refresh_error(self):
        service = Mock()
        service.get_alerts.side_effect = ValueError("invalid inventory data")
        self.window._controller = SimpleNamespace(
            inventory_alert_service=service,
            data_manager=SimpleNamespace(
                inventory=SimpleNamespace(records=[])
            ),
        )

        self.window._refresh_home_alert_banner()

        self.assertFalse(self.window._home_alert_banner.isHidden())
        self.assertIn(
            "Inventory alerts are unavailable: invalid inventory data",
            self.window._home_alert_message.text(),
        )
        self.window._controller = None
        self.window._home_alert_banner.hide()

    def test_11_alert_table_keeps_row_highlight_without_focus_border(self):
        record = {"food": "Milk", "quantity": 1, "use-by": "01/01/2000"}
        expired_item = {
            "id": 1,
            "record": record,
            "days_remaining": -1,
        }
        alerts = {
            "expired": [expired_item],
            "expiring_soon": [],
            "low_stock": [],
            "unknown_expiry": [],
        }
        self.window._controller = SimpleNamespace(
            data_manager=SimpleNamespace(
                load=Mock(),
                inventory=SimpleNamespace(records=[record]),
            ),
            inventory_alert_service=SimpleNamespace(
                get_alerts=Mock(return_value=alerts)
            ),
        )

        self.window._refresh_inventory_alerts()

        self.assertEqual(
            self.window._alert_table.selectionMode(),
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.assertIsInstance(
            self.window._inventory_table.itemDelegate(),
            _NoFocusItemDelegate,
        )
        self.assertIsInstance(
            self.window._alert_table.itemDelegate(),
            _NoFocusItemDelegate,
        )
        self.window._alert_table.selectRow(0)
        self.assertTrue(self.window._alert_table.item(0, 2).isSelected())
        self.window._inventory_table.setRowCount(1)
        self.window._inventory_table.setItem(0, 0, QTableWidgetItem("Milk"))
        self.window._inventory_table.selectRow(0)
        self.assertTrue(self.window._inventory_table.item(0, 0).isSelected())
        checkbox_container = self.window._alert_table.cellWidget(0, 0)
        checkbox = checkbox_container.findChild(QCheckBox)
        checkbox.setChecked(True)
        self.assertTrue(checkbox.isChecked())
        self.assertTrue(self.window._btn_delete_expired_alert.isEnabled())

        self.window._controller = None
        self.window._alert_table.setRowCount(0)
        self.window._btn_delete_expired_alert.setEnabled(False)

    def test_12_search_item_expands_inventory_table(self):
        record = {"food": "Milk", "quantity": 1, "use-by": "01/01/2000"}
        self.window._controller = SimpleNamespace(
            data_manager=SimpleNamespace(
                inventory=SimpleNamespace(records=[record])
            )
        )
        self.window.show()
        self.window._search_panel.show()
        self.window._inventory_table.setRowCount(1)
        self.window._inventory_table.setVerticalHeaderItem(
            0, QTableWidgetItem("1")
        )
        self.window._inventory_table.setMaximumHeight(340)

        try:
            self.window._load_food_profile_by_row(0)

            self.assertEqual(
                self.window._inventory_table.maximumHeight(),
                16777215,
            )
            self.assertFalse(self.window._item_details_view.isHidden())
            self.assertEqual(
                self.window._item_details_view.verticalScrollBar().maximum(),
                0,
            )
        finally:
            self.window._controller = None
            self.window._item_details_view.hide()
            self.window._search_panel.hide()
            self.window.hide()


if __name__ == "__main__":
    print("=" * 60)
    print("FOODRESCUE AI - GUI TESTS")
    print("=" * 60)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestFoodRescueGUI)
    )
    print(f"FINAL RESULTS: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} TESTS PASSED")
    sys.exit(0 if result.wasSuccessful() else 1)
