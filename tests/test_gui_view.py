"""Offline GUI checks: python -m unittest discover -s tests -v."""

import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from io_manager.gui_view import AIWorker, CalendarDateEdit, GuiView, QComboBox


class GuiViewTests(unittest.TestCase):
    # Check Qt rendering and worker signals without live AI calls or file writes.

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_window_and_controls_render_in_both_themes(self):
        view = GuiView()
        try:
            view.show()
            self.assertIsInstance(view._add_category, QComboBox)
            self.assertIsInstance(view._add_date, CalendarDateEdit)
            view._add_category.setCurrentText("Bakery")
            tomorrow = QDate.currentDate().addDays(1)
            view._add_date.setDate(tomorrow)
            for dark in (False, True):
                view._toggle_theme(dark)
                view._on_edit_inventory_triggered()
                self.app.processEvents()
                self.assertFalse(view.grab().isNull())
                self.assertFalse(view._add_category.grab().isNull())
                self.assertFalse(view._add_date.grab().isNull())
                self.assertEqual(view._add_category.currentText(), "Bakery")
                self.assertEqual(view._add_date.date(), tomorrow)
        finally:
            view.close()
            view.deleteLater()
            self.app.processEvents()

    def test_worker_emits_result_or_error_from_background_thread(self):
        cases = [
            (({"recipes": []}, None), None, {"recipes": []}, None),
            ((None, "Service unavailable"), None, None, "Service unavailable"),
            (None, RuntimeError("Request failed"), None, "Request failed"),
        ]
        for response, exception, expected_result, expected_error in cases:
            with self.subTest(error=expected_error):
                manager = Mock()
                manager.suggest_recipes.return_value = response
                manager.suggest_recipes.side_effect = exception
                payload = {"item": "Tomatoes"}
                worker = AIWorker(manager, payload)
                results = QSignalSpy(worker.result_ready)
                errors = QSignalSpy(worker.error_occurred)
                worker.start()
                self.assertTrue(worker.wait(5000), "Offline worker did not finish")
                self.app.processEvents()
                manager.suggest_recipes.assert_called_once_with(payload)
                if expected_error is None:
                    self.assertEqual(results.count(), 1)
                    self.assertEqual(results.at(0)[0], expected_result)
                    self.assertEqual(errors.count(), 0)
                else:
                    self.assertEqual(errors.count(), 1)
                    self.assertEqual(errors.at(0)[0], expected_error)
                    self.assertEqual(results.count(), 0)


if __name__ == "__main__":
    unittest.main()
