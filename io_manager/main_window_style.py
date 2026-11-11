"""Shared Qt styling for FoodRescue windows, controls and recipe cards."""

from PySide6.QtGui import QFontDatabase


APPLICATION_QSS = """
QMainWindow, QDialog, QMessageBox, QInputDialog { background: #1b1f22; }
QWidget { color: #dce3df; font-size: 13px; }
QLabel { background: transparent; border: none; padding: 0; margin: 0;
    color: #c3ccc7; font-weight: normal; }
QLabel#SectionTitle { color: #f0f3f1; font-size: 18px; font-weight: 600; }
QLabel#AssistantStatus { color: #b0cfbc; font-size: 12px; }
QFrame#AddFrame, QFrame#EditFrame, QFrame#DeleteFrame,
QFrame#SearchPanelFrame, QFrame#AssistantPanel {
    background: #242a2d; border: 1px solid #3a4347; border-radius: 12px;
    padding: 0; margin: 0;
}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    background: #2c3337; color: #e5ebe7; border: 1px solid #475158;
    border-radius: 7px; padding: 7px 10px; min-height: 18px;
    selection-background-color: #466451; selection-color: #f2f6f3;
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover { border-color: #627269; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
QPlainTextEdit:focus, QTextEdit:focus { border-color: #a7cbb6; }
QComboBox { padding-right: 26px; }
QComboBox::drop-down, QDateEdit::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView, QListWidget {
    background: #293034; color: #e3e9e5; border: 1px solid #46514b;
    selection-background-color: #3c5648; selection-color: #f0f6f2;
    outline: 0;
}
QListWidget { border-radius: 8px; padding: 6px; }
QListWidget::item { padding: 8px; border-radius: 4px; }
QPushButton {
    background: #30383c; color: #e2e8e4; border: 1px solid #4a565c;
    border-radius: 7px; padding: 7px 12px; min-height: 18px; text-align: center;
}
QPushButton:hover { background: #3b464b; border-color: #718179; }
QPushButton:pressed, QPushButton:checked { background: #3c5648; }
QPushButton:focus { border-color: #b2d4bf; }
QPushButton#ApplyFilterButton { background: #afd1bb; color: #192c21;
    border-color: #afd1bb; font-weight: 600; }
QPushButton#ApplyFilterButton:hover { background: #c2e0cb; border-color: #c2e0cb; }
QPushButton#ApplyFilterButton:pressed { background: #93bca2; }
QPushButton#ExecuteDeleteButton { background: #443235; color: #edbab9; border-color: #765052; }
QPushButton#ExecuteDeleteButton:hover { background: #573c40; border-color: #b57a7d; }
QPushButton:disabled { background: #292f32; color: #78847d; border-color: #3c4548; }
QTextEdit, QPlainTextEdit {
    background: #242a2d; color: #dce3df; border: 1px solid #3c464a;
    border-radius: 12px; padding: 16px; margin: 0;
    selection-background-color: #3c5648; selection-color: #eff7f1;
}
QScrollArea { background: transparent; border: none; padding: 0; margin: 0; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: #22272a; width: 10px; margin: 0; border: none; }
QScrollBar:horizontal { background: #22272a; height: 10px; margin: 0; border: none; }
QScrollBar::handle { background: #536059; border-radius: 4px; min-height: 28px; min-width: 28px; }
QScrollBar::handle:hover { background: #74867a; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QMessageBox QLabel { min-width: 300px; font-weight: normal; }
QMessageBox QPushButton, QDialogButtonBox QPushButton { min-width: 70px; }
QToolTip { background: #303a34; color: #edf3ef; border: 1px solid #63796b; padding: 6px; }
QCalendarWidget QWidget { background: #293034; color: #e3e9e5; }
QCalendarWidget QAbstractItemView { background: #242a2d;
    selection-background-color: #466451; selection-color: #f0f6f2; }
"""


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
QFrame#HomeAlertBanner { background: #332e22; border: 1px solid #665334;
    border-radius: 10px; padding: 0; margin: 0; }
QLabel { background: transparent; border: none; padding: 0; margin: 0;
    color: #a6afb3; font-size: 14px; font-weight: normal; }
QLabel#WelcomeEyebrow { color: #a5cbb4; font-size: 11px; font-weight: 600; }
QLabel#WelcomeTitle { color: #f0f3f1; font-size: 32px; font-weight: 600; }
QLabel#WelcomeFootnote { color: #818d93; font-size: 12px; }
QLabel#HomeAlertMessage { color: #e6d3a8; font-size: 13px; font-weight: 600; }
QPushButton { background: #afd1bb; color: #192c21; border: 1px solid #afd1bb;
    border-radius: 8px; padding: 10px 20px; font-size: 13px;
    font-weight: 600; text-align: center; }
QPushButton:hover { background: #c2e0cb; border-color: #c2e0cb; }
QPushButton:pressed { background: #93bca2; }
QPushButton:focus { border: 2px solid #edf6ef; }
QPushButton#HomeAlertDismissButton { background: transparent; color: #e6d3a8;
    border-color: #806b45; padding: 8px 12px; }
QPushButton#HomeAlertDismissButton:hover { background: #49402e; }
"""

RECIPE_CARDS_QSS = """
QScrollArea#RecipeLibrary { background: transparent; border: none; padding: 0; margin: 0; }
QWidget#RecipeCardContents { background: transparent; }
QFrame#RecipeCard { border: 1px solid #42564b; border-radius: 14px;
    background: #273a31; padding: 0; margin: 0; }
QFrame#AssessmentCard { border: 1px solid #3c464a; border-radius: 14px;
    background: #242a2d; padding: 0; margin: 0; }
QFrame#RecipeCard[tone="slate"] { background: #293640; border-color: #435461; }
QFrame#RecipeCard[tone="plum"] { background: #36303d; border-color: #51465b; }
QLabel { background: transparent; color: #dce4df; border: none;
    padding: 0; margin: 0; font-size: 13px; font-weight: normal; }
QLabel#RecipeNumber { color: #a7c6b4; font-size: 11px; font-weight: 600; }
QLabel#RecipeTitle { color: #f1f4f2; font-size: 20px; font-weight: 600; }
QLabel#RecipeSection { color: #c2d2c9; font-size: 12px; font-weight: 600; }
QLabel#RecipeIngredients { color: #b9c6bf; }
QFrame#RecipeCard[tone="slate"] QLabel#RecipeNumber,
QFrame#RecipeCard[tone="slate"] QLabel#RecipeSection { color: #b3cadb; }
QFrame#RecipeCard[tone="plum"] QLabel#RecipeNumber,
QFrame#RecipeCard[tone="plum"] QLabel#RecipeSection { color: #c9bad8; }
QFrame#RecipeDivider { background: #56675e; border: none;
    border-radius: 0; padding: 0; margin: 0; max-height: 1px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: #515c62; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #718179; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
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


def style_inventory_table(table):
    """Keep tables consistent while retaining clickable row IDs and item data."""
    style_surface(table, INVENTORY_QSS)
    table.setShowGrid(False)
    table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
    table.verticalHeader().setMinimumSectionSize(46)
    table.verticalHeader().setDefaultSectionSize(46)
    table.horizontalHeader().setMinimumHeight(44)
