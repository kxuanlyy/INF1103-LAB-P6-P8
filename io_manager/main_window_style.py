"""Shared Qt styling for FoodRescue windows, controls and recipe cards."""

import re

from PySide6.QtGui import QColor, QFontDatabase, QPalette, QTextCursor
from PySide6.QtWidgets import QWidget, QTextEdit


# Match the existing dark colors to deliberately chosen light surfaces/text.
# Both QSS and rich-text reports share this palette; the original dark theme is retained.
_LIGHT_GROUPS = {
    "#f5f6f7": "#1b1f22 #22272a",
    "#eceef0": "#202326",
    "#ffffff": "#23272a #24282b #242a2d #2c3337",
    "#f5f7f6": "#272c2f #293034",
    "#edf5ef": "#273a31 #293b33",
    "#edf2f8": "#293640",
    "#f4eff7": "#36303d",
    "#eff1f2": "#292f32 #2c3236 #30363a #30383c #303a3f",
    "#e3e7e5": "#2b3034 #3b4347 #3b464b",
    "#dfede4": "#303a34 #30463a #34483e #344b40 #3c5648 #466451",
    "#ccdfd3": "#3d5146 #45584d",
    "#d7ddda": "#303639 #34383b #363d40 #3a3a3a #3a4145 #3a4347 #3c4548 #3c464a #41494d #414b50 #464d51 #475158 #4a565c",
    "#bbd2c3": "#415b4d #42564b #425b4c #46514b #56675e",
    "#c2cfdf": "#435461",
    "#d5c8df": "#51465b",
    "#b0bab4": "#515c62 #536059",
    "#879a8e": "#627269 #63716a #63796b #718179 #74867a",
    "#69746e": "#78847d #818b91 #818d93 #8e9d94 #929ca1",
    "#58655e": "#99a3a9 #a0a0a0 #a0a7ab #a6afb3 #a7b7ad #aabfb2 #acb7bc #b4c1b9 #b8c5bd #b9c6bf #bac1c4 #bbc7bf",
    "#36634d": "#92bda4 #9cbda9 #a5cbb4 #a6c6b3 #a7c6b4 #a7cbb6 #a7cfb7 #b0cfbc #b2d4bf #b4d4c0 #bcdec9",
    "#cce3d5": "#afd1bb",
    "#b9d9c5": "#c2e0cb #93bca2",
    "#3b4e42": "#c2d2c9 #c3ccc7 #c4d2ca #d4ded8 #d7efdf",
    "#355f7c": "#b3cadb",
    "#715282": "#c9bad8",
    "#27332c": "#dce3df #dce4df #dde3df #e0e0e0 #e0e9e3 #e2e7e4 #e2e8e4 #e3e9e5 #e3ede6 #e5ebe7 #edf3ef #edf6ef #eff7f1 #f0f2f0 #f0f2f1 #f0f3f1 #f0f4f1 #f0f6f2 #f1f4f2 #f2f6f3",
    "#fff5df": "#332e22",
    "#f4e7c9": "#49402e",
    "#dfc994": "#665334 #806b45",
    "#74591e": "#e6d3a8 #cfbc97",
    "#f9eaea": "#443235",
    "#f1d9d9": "#573c40",
    "#d4a4a4": "#765052 #b57a7d",
    "#943f42": "#edbab9 #dcaaa9",
}
_LIGHT_COLORS = {dark: light for light, colors in _LIGHT_GROUPS.items() for dark in colors.split()}


def is_dark(widget):
    while widget is not None:
        mode = widget.property("darkMode")
        if mode is not None:
            return bool(mode)
        widget = widget.parentWidget()
    return False


def theme_colors(css, dark):
    if dark:
        return css
    return re.sub(r"#[0-9a-fA-F]{6}\b", lambda match: _LIGHT_COLORS.get(match[0].lower(), match[0]), css)


def set_themed_html(widget, html):
    # Only change style attributes, never recipe content containing a hex string.
    rendered = re.sub(
        r"\b(style|bgcolor)=(['\"])(.*?)\2",
        lambda match: f"{match[1]}={match[2]}{theme_colors(match[3], is_dark(widget))}{match[2]}",
        html, flags=re.DOTALL,
    )
    if isinstance(widget, QTextEdit):
        if not widget.property("themeHtmlConnected"):
            widget.document().contentsChanged.connect(lambda: widget.setProperty("themeHtml", None))
            widget.setProperty("themeHtmlConnected", True)
        widget.setHtml(rendered)
    else:
        widget.setText(rendered)
    widget.setProperty("themeHtml", html)


def apply_theme(window, dark):
    """Recolor existing widgets without rebuilding forms or invoking their actions."""
    window.setProperty("darkMode", dark)
    palette = window.palette()
    for role, color in (
        (QPalette.Window, "#1b1f22"), (QPalette.WindowText, "#dce3df"),
        (QPalette.Base, "#242a2d"), (QPalette.AlternateBase, "#272c2f"),
        (QPalette.Text, "#dce3df"), (QPalette.Button, "#30383c"),
        (QPalette.ButtonText, "#e2e8e4"), (QPalette.Highlight, "#3c5648"),
        (QPalette.HighlightedText, "#eff7f1"), (QPalette.PlaceholderText, "#818d93"),
    ):
        palette.setColor(role, QColor(theme_colors(color, dark)))
    window.setPalette(palette)
    for widget in [window, *window.findChildren(QWidget)]:
        source = widget.property("themeStylesheet")
        if source is not None:
            widget.setStyleSheet(theme_colors(source, dark))
        html = widget.property("themeHtml")
        if html is not None:
            if isinstance(widget, QTextEdit):
                cursor = widget.textCursor()
                anchor, position = cursor.anchor(), cursor.position()
                vertical = widget.verticalScrollBar().value()
                horizontal = widget.horizontalScrollBar().value()
                set_themed_html(widget, html)
                cursor = widget.textCursor()
                cursor.setPosition(anchor)
                cursor.setPosition(position, QTextCursor.KeepAnchor)
                widget.setTextCursor(cursor)
                widget.verticalScrollBar().setValue(vertical)
                widget.horizontalScrollBar().setValue(horizontal)
            else:
                set_themed_html(widget, html)


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
QListWidget#BusinessRulesRecipeList::item:selected {
    background: #3c5648; color: #f0f6f2; border-left: 3px solid #afd1bb;
}
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
