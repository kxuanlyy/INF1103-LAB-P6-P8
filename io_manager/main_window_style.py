"""Presentation helpers scoped to the main shell, not application-wide dialogs."""

from PySide6.QtGui import QFontDatabase


SIDEBAR_QSS = """
QFrame#MainSidebar {
    background: #202326; border: none; border-right: 1px solid #34383b;
    border-radius: 0; padding: 0; margin: 0;
}
QLabel { background: transparent; border: none; padding: 0; margin: 0;
    color: #a0a7ab; font-size: 12px; font-weight: normal; }
QLabel#Brand { color: #f0f2f0; font-size: 20px; font-weight: 600; }
QLabel#BrandMark { background: #344b40; color: #bcdec9; border-radius: 12px;
    font-size: 15px; font-weight: 600; }
QLabel#NavSection { color: #818b91; font-size: 11px; font-weight: 600; }
QPushButton { background: transparent; color: #bac1c4; border: 1px solid transparent;
    border-radius: 8px; padding: 9px 12px; margin: 0; text-align: left;
    font-size: 13px; font-weight: normal; }
QPushButton:hover { background: #2b3034; color: #f0f3f1; border-color: transparent; }
QPushButton:checked { background: #34483e; color: #d7efdf; border-color: #415b4d; }
QPushButton:pressed { background: #3d5146; }
QPushButton:focus { border: 1px solid #92bda4; }
QPushButton#ExitButton { color: #929cA1; }
"""

TOOLBAR_QSS = """
QFrame#MainToolbar { background: #24282b; border: none;
    border-bottom: 1px solid #34383b; border-radius: 0; padding: 0; margin: 0; }
QLabel { background: transparent; border: none; padding: 0; margin: 0;
    color: #99a3a9; font-size: 12px; font-weight: normal; }
QLabel#PageTitle { color: #f0f2f1; font-size: 19px; font-weight: 600; }
QPushButton { background: #30363a; color: #e2e7e4; border: 1px solid #464d51;
    border-radius: 7px; padding: 7px 14px; text-align: center; font-size: 12px; }
QPushButton:hover { background: #3b4347; border-color: #63716a; }
QPushButton:pressed { background: #45584d; }
QPushButton:focus { border-color: #a7cfb7; }
"""

WELCOME_QSS = """
QFrame#WelcomePanel { background: #24282b; border: 1px solid #363d40;
    border-radius: 16px; padding: 0; margin: 0; }
QLabel { background: transparent; border: none; padding: 0; margin: 0;
    color: #a6afb3; font-size: 14px; font-weight: normal; }
QLabel#WelcomeEyebrow { color: #a5cbb4; font-size: 11px; font-weight: 600; }
QLabel#WelcomeTitle { color: #f0f3f1; font-size: 32px; font-weight: 600; }
QLabel#WelcomeFootnote { color: #818d93; font-size: 12px; }
QPushButton { background: #afd1bb; color: #192c21; border: 1px solid #afd1bb;
    border-radius: 8px; padding: 10px 20px; font-size: 13px;
    font-weight: 600; text-align: center; }
QPushButton:hover { background: #c2e0cb; border-color: #c2e0cb; }
QPushButton:pressed { background: #93bca2; }
QPushButton:focus { border: 2px solid #edf6ef; }
"""

INVENTORY_QSS = """
QTableWidget { background: #23272a; alternate-background-color: #272c2f;
    color: #dde3df; border: 1px solid #3a4145; border-radius: 10px;
    padding: 0; margin: 0; font-size: 13px; selection-background-color: #3c5648;
    selection-color: #eff7f1; }
QTableWidget::item { padding: 10px 14px; border: none;
    border-bottom: 1px solid #303639; }
QTableWidget::item:alternate { background: #272c2f; }
QTableWidget::item:selected { background: #3c5648; color: #eff7f1; }
QTableWidget::item:focus { border: 1px solid #9cbda9; }
QHeaderView { background: #2c3236; border: none; padding: 0; margin: 0; }
QHeaderView::section { background: #2c3236; color: #acb7bc;
    padding: 10px 14px; border: none; border-bottom: 1px solid #41494d;
    font-size: 12px; font-weight: 600; }
QTableCornerButton::section { background: #2c3236; border: none;
    border-bottom: 1px solid #41494d; }
QScrollBar:vertical { background: #23272a; width: 10px; margin: 3px; border: none; }
QScrollBar:horizontal { background: #23272a; height: 10px; margin: 3px; border: none; }
QScrollBar::handle { background: #515c62; border-radius: 3px; min-height: 28px;
    min-width: 28px; }
QScrollBar::handle:hover { background: #718179; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


def style_surface(widget, stylesheet):
    """Use the platform UI font (SF on macOS, Segoe UI on Windows)."""
    widget.setFont(QFontDatabase.systemFont(QFontDatabase.GeneralFont))
    widget.setStyleSheet(stylesheet)


def style_inventory_table(table, enabled):
    """Apply the first-iteration table treatment only on View Inventory.

    The same widget is reused by other workflows; restore its original view
    properties there, retaining clickable row IDs and all underlying items.
    """
    if not hasattr(table, "_main_window_original_style"):
        table._main_window_original_style = (
            table.styleSheet(), table.showGrid(), table.selectionBehavior(),
            table.verticalHeader().minimumSectionSize(),
            table.verticalHeader().defaultSectionSize(),
            table.horizontalHeader().minimumHeight(), table.font(),
        )
    original = table._main_window_original_style
    if enabled:
        style_surface(table, INVENTORY_QSS)
        table.setShowGrid(False)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.verticalHeader().setMinimumSectionSize(46)
        table.verticalHeader().setDefaultSectionSize(46)
        table.horizontalHeader().setMinimumHeight(44)
    else:
        table.setStyleSheet(original[0])
        table.setShowGrid(original[1])
        table.setSelectionBehavior(original[2])
        table.verticalHeader().setMinimumSectionSize(original[3])
        table.verticalHeader().setDefaultSectionSize(original[4])
        table.horizontalHeader().setMinimumHeight(original[5])
        table.setFont(original[6])
