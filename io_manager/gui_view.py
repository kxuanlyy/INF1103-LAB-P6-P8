from datetime import datetime
import csv
import os
import re
from html import escape
from ai_module.ai_manager import RECIPES_PATH
from logic_manager.reciperesultservice import RecipeResultService
from logic_manager.edit_business_rules import BusinessRulesEditor
from logic_manager.inventory_alert_service import DEFAULT_EXPIRING_WITHIN_DAYS
from data_manager.inventory_filter import InventoryFilter
from io_manager.main_window_style import (
    APPLICATION_QSS, SIDEBAR_QSS, TOOLBAR_QSS, WELCOME_QSS,
    INVENTORY_QSS, apply_theme, set_themed_html, style_surface, style_inventory_table,
)
from io_manager.recipe_cards import RecipeCardsView
from io_manager.theme_switch import ThemeSwitch
from io_manager.combo_box import QComboBox
from io_manager.calendar_date_edit import CalendarDateEdit
from io_manager.ai_worker import AIWorker
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QInputDialog,
    QPushButton, QTextEdit, QLineEdit, QLabel, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QListWidget, QSizePolicy,
    QGridLayout, QScrollArea,
    QDialog, QDialogButtonBox, QPlainTextEdit,
    QCheckBox
)


# Coordinate the main window and its inventory, recipe and assessment screens.
class GuiView(QMainWindow):
    
    def __init__(self, controller=None) -> None:
        QMainWindow.__init__(self)
        self.setProperty("darkMode", False)
        self._dark_mode = False
        self._controller = controller
        self._home_alert_dismissed = False

        # Canvas Setup
        self._central_widget = QWidget()
        self._main_layout = QHBoxLayout(self._central_widget)
        
        # Sidebar Control
        self._sidebar_widget = QFrame()
        self._sidebar_layout = QVBoxLayout(self._sidebar_widget)
        self._status_label = QLabel("FoodRescue Operations")     
        self._status_label.setAlignment(Qt.AlignCenter)
        
        # Action Buttons for all Menu Options
        self._btn_view_inv = QPushButton("📋 View Inventory")
        self._btn_search_inv = QPushButton("🔍 Search Inventory")
        self._btn_edit_inv = QPushButton("✏ Edit Items Data")
        self._btn_ask_ai = QPushButton("🤖 Ask AI Assistant")
        self._btn_process_recipes = QPushButton("🍳 Process Recipes")
        self._btn_view_recipes = QPushButton("📖 View Recipes")
        self._btn_search_recipes = QPushButton("🏷 Search Recipes")
        self._btn_inventory_alerts = QPushButton("⚠ Inventory Alerts")
        self._btn_editbusinessrules = QPushButton("⚙ Edit Business Rules")
        self._btn_exit = QPushButton("🚪 Exit Application")

        # Right Display Component Area (Dynamic Layout)
        self._display_container = QWidget()
        self._display_layout = QVBoxLayout(self._display_container)
    
        self._inventory_table = QTableWidget()
        self._item_details_view = QTextEdit()
        self._log_display = QTextEdit()
        self._alert_panel = QWidget()
        self._alert_layout = QVBoxLayout(self._alert_panel)
        self._alert_summary = QLabel()
        self._alert_table = QTableWidget()
        self._btn_refresh_alerts = QPushButton("Refresh alerts")
        self._btn_delete_expired_alert = QPushButton("Delete checked expired items")
        self._btn_delete_expired_alert.setObjectName("ExecuteDeleteButton")
        self._btn_delete_expired_alert.setEnabled(False)
        self._expired_alert_ids = set()

        # Search Bar Tool
        self._search_panel = QFrame()
        self._search_layout = QVBoxLayout(self._search_panel)
        self._input_food = QLineEdit()
        self._input_id = QLineEdit()
        self._btn_submit_search = QPushButton("Apply Filter")
        # dropdown filters (their choices are filled from the inventory each time the screen opens)
        self._filter_combos = {
            "food_category": QComboBox(),
            "storage_condition": QComboBox(),
            "waste_risk_level": QComboBox(),
            "allergen": QComboBox(),
            "demand_level": QComboBox(),
        }
        self._btn_reset_search = QPushButton("Reset")
        self._btn_submit_search.setObjectName("ApplyFilterButton")

        # Recipe Search Bar Tool Panel
        self._recipe_search_panel = QFrame()
        self._recipe_search_layout = QHBoxLayout(self._recipe_search_panel)
        self._input_recipe_ingredient = QLineEdit()
        self._input_recipe_id = QLineEdit()
        self._btn_submit_recipe_search = QPushButton("Apply Filter")
        self._btn_submit_recipe_search.setObjectName("ApplyFilterButton")


        # Edit Operations
        self._edit_panel = QWidget()
        self._edit_panel_layout = QVBoxLayout(self._edit_panel)

        self._edit_panel_layout.setContentsMargins(0, 0, 15, 10)
        self._edit_panel_layout.setSpacing(12)

        # Add Item (a)
        self._frame_add = QFrame()
        self._frame_add.setObjectName("AddFrame")
        self._layout_add = QVBoxLayout(self._frame_add)
        self._lbl_add_title = QLabel("Add Item:")
        
        self._add_name = QLineEdit(); self._add_name.setPlaceholderText("Ingredient Name")
        self._add_qty = QLineEdit(); self._add_qty.setPlaceholderText("Stock Qty")
        self._add_date = CalendarDateEdit()
        self._add_date.setCalendarPopup(True)
        self._add_date.setDisplayFormat("dd/MM/yyyy")
        self._add_date.setDate(QDate.currentDate())
        self._add_date.setMinimumDate(QDate.currentDate())
        self._add_category = QComboBox(); self._add_category.addItems(["Dairy", "Meat & Seafood", "Fresh Produce", "Bakery", "Pantry", "Other"])
        self._add_storage = QComboBox(); self._add_storage.addItems(["Chilled", "Frozen", "Ambient"])
        self._add_risk = QComboBox(); self._add_risk.addItems(["Low", "Medium", "High"])
        self._add_demand = QComboBox(); self._add_demand.addItems(["Low", "Medium", "High"])
        self._add_allergens = QLineEdit(); self._add_allergens.setPlaceholderText("Allergens")
        
        self._btn_execute_add = QPushButton("Add")
        self._btn_execute_add.setObjectName("ApplyFilterButton")
        self._btn_execute_add.setFixedWidth(80)

        # Edit item (c)
        self._frame_edit = QFrame()
        self._frame_edit.setObjectName("EditFrame")
        self._layout_edit = QVBoxLayout(self._frame_edit)
        self._lbl_edit_title = QLabel("Edit:")
        self._input_edit_id = QLineEdit(); 
        self._input_edit_id.setPlaceholderText("e.g. 1")
        self._input_edit_id.setFixedWidth(120)
        
        # Inner Dynamic Fields for Edit Sub-Form
        self._edit_form_widget = QWidget()
        self._edit_form_layout = QHBoxLayout(self._edit_form_widget)
        self._edit_name = QLineEdit(); self._edit_name.setPlaceholderText("Ingredient Name")
        self._edit_qty = QLineEdit(); self._edit_qty.setPlaceholderText("Stock Qty")
        self._edit_date = CalendarDateEdit()
        self._edit_date.setCalendarPopup(True)
        self._edit_date.setDisplayFormat("dd/MM/yyyy")
        self._edit_category = QComboBox(); self._edit_category.addItems(["Dairy", "Meat & Seafood", "Fresh Produce", "Bakery", "Pantry", "Other"])
        self._edit_storage = QComboBox(); self._edit_storage.addItems(["Chilled", "Frozen", "Ambient"])
        self._edit_risk = QComboBox(); self._edit_risk.addItems(["Low", "Medium", "High"])
        self._edit_demand = QComboBox(); self._edit_demand.addItems(["Low", "Medium", "High"])
        self._edit_allergens = QLineEdit(); self._edit_allergens.setPlaceholderText("Allergens")
         
        self._btn_execute_update = QPushButton("Edit")
        self._btn_execute_update.setObjectName("ApplyFilterButton")
        self._btn_execute_update.setFixedWidth(80)

        # Delete item (b)
        self._frame_delete = QFrame()
        self._frame_delete.setObjectName("DeleteFrame")
        self._layout_delete = QHBoxLayout(self._frame_delete)
        self._lbl_delete_title = QLabel("Delete:")

        self._input_delete_id = QLineEdit(); 
        self._input_delete_id.setPlaceholderText("e.g. 1")
        self._input_delete_id.setFixedWidth(120)

        self._btn_execute_delete = QPushButton("Delete")
        self._btn_execute_delete.setObjectName("ExecuteDeleteButton")
        self._btn_execute_delete.setFixedWidth(80)

        # Option 4: AI
        self._frame_ai_input = QFrame()
        self._frame_ai_input.setObjectName("AddFrame")
        self._layout_ai_input = QVBoxLayout(self._frame_ai_input)
        
        self._lbl_ai_id_title = QLabel("Enter item id:")
        self._input_ai_id = QLineEdit()
        self._input_ai_id.setPlaceholderText("e.g. 1")
        self._input_ai_id.setFixedWidth(120)
        
        self._lbl_ai_notes_title = QLabel("Enter quality observations (leave blank):")
        self._input_ai_notes = QLineEdit()
        self._input_ai_notes.setPlaceholderText("No structural physical defects observed")
        
        self._btn_execute_ai = QPushButton("Enquire")
        self._btn_execute_ai.setObjectName("ApplyFilterButton")
        self._btn_execute_ai.setFixedWidth(100)


        # Configure button properties to latch their pressed visual states
        self._btn_view_inv.setCheckable(True)
        self._btn_search_inv.setCheckable(True)
        self._btn_edit_inv.setCheckable(True)
        self._btn_ask_ai.setCheckable(True)
        self._btn_process_recipes.setCheckable(True)
        self._btn_view_recipes.setCheckable(True)
        self._btn_search_recipes.setCheckable(True)
        self._btn_inventory_alerts.setCheckable(True)
        
        # Group them into a list for easy state clearing loops later
        self._nav_buttons = [
            self._btn_view_inv, self._btn_search_inv, self._btn_edit_inv,
            self._btn_ask_ai, self._btn_process_recipes, self._btn_view_recipes,
            self._btn_search_recipes, self._btn_inventory_alerts, self._btn_editbusinessrules,
        ]
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("FoodRescue")
        self.resize(1200, 860)
        self.setCentralWidget(self._central_widget)
        
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        self._sidebar_widget.setFrameShape(QFrame.StyledPanel)
        self._sidebar_widget.setFixedWidth(232)
        self._sidebar_layout.setContentsMargins(16, 28, 16, 20)
        self._sidebar_layout.setSpacing(4)
        self._setup_main_window_shell()
        

        self._display_layout.addWidget(self._inventory_table)
        self._display_layout.addWidget(self._item_details_view)
        self._display_layout.addWidget(self._log_display)
        self._display_layout.addWidget(self._alert_panel)
        self._recipe_cards = RecipeCardsView()
        self._display_layout.addWidget(self._recipe_cards)
        self._recipe_cards.hide()
        self._alert_layout.setContentsMargins(8, 8, 8, 8)
        self._alert_layout.setSpacing(10)
        self._alert_summary.setWordWrap(True)
        self._alert_table.setColumnCount(7)
        self._alert_table.setHorizontalHeaderLabels([
            "Select", "Item ID", "Item", "Quantity", "Use-by date",
            "Days remaining", "Alerts",
        ])
        self._alert_table.setAlternatingRowColors(True)
        self._alert_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._alert_table.verticalHeader().hide()
        alert_header = self._alert_table.horizontalHeader()
        alert_header.setDefaultAlignment(Qt.AlignCenter)
        alert_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        alert_header.setSectionResizeMode(2, QHeaderView.Stretch)
        alert_header.setSectionResizeMode(6, QHeaderView.Stretch)
        self._alert_table.setWordWrap(True)
        self._alert_summary.setAlignment(Qt.AlignCenter)
        self._alert_layout.addWidget(self._alert_summary)
        self._alert_layout.addWidget(self._alert_table)
        alert_actions = QHBoxLayout()
        alert_actions.addStretch()
        alert_actions.addWidget(self._btn_delete_expired_alert)
        alert_actions.addWidget(self._btn_refresh_alerts)
        self._alert_layout.addLayout(alert_actions)
        self._alert_panel.hide()

        # Setup Recipe Search Panel Controls for option 7
        self._recipe_search_panel.setFixedHeight(60)
        self._recipe_search_layout.setContentsMargins(10, 4, 10, 4)
        self._recipe_search_layout.setSpacing(10)      
        self._input_recipe_ingredient.setPlaceholderText("Filter by Ingredient Name...")
        self._input_recipe_id.setPlaceholderText("Filter by Recipe ID...")
        self._btn_submit_recipe_search.setFixedWidth(100)

        self._recipe_search_layout.addWidget(self._input_recipe_ingredient)
        self._recipe_search_layout.addWidget(self._input_recipe_id)
        self._recipe_search_layout.addWidget(self._btn_submit_recipe_search)
        self._display_layout.insertWidget(0, self._recipe_search_panel)
        self._recipe_search_panel.hide()



        self._edit_panel_layout.setContentsMargins(0, 0, 12, 10)
        self._edit_panel_layout.setSpacing(12)

        self._edit_scroll_area = QScrollArea()
        self._edit_scroll_area.setWidgetResizable(True)
        self._edit_scroll_area.setWidget(self._edit_panel)
        self._edit_scroll_area.setFrameShape(QFrame.NoFrame)
        self._display_layout.addWidget(self._edit_scroll_area)

        self._layout_ai_input.addWidget(self._lbl_ai_id_title)
        self._layout_ai_input.addWidget(self._input_ai_id)
        self._layout_ai_input.addWidget(self._lbl_ai_notes_title)
        self._layout_ai_input.addWidget(self._input_ai_notes)
        self._layout_ai_input.addWidget(self._btn_execute_ai, alignment=Qt.AlignRight)
        
        self._display_layout.addWidget(self._frame_ai_input)
        self._frame_ai_input.hide()

        self._edit_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._edit_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Hide the grid by default until data populates
        self._log_display.setReadOnly(True)
        self._item_details_view.setReadOnly(True)
        self._inventory_table.hide()  
        self._item_details_view.hide()
        self._edit_scroll_area.hide()

        # Add Section Layout
        self._layout_add.addWidget(self._lbl_add_title)
        # Split fields into a two-column clean row layout configuration grid
        add_grid_widget = QWidget()
        add_grid_layout = QGridLayout(add_grid_widget)
        add_grid_layout.setContentsMargins(10, 10, 10, 10)
        add_grid_layout.setSpacing(10)
        
        # Column 1
        add_grid_layout.addWidget(QLabel("Ingredient Name:"), 0, 0)
        add_grid_layout.addWidget(self._add_name, 0, 1)
        add_grid_layout.addWidget(QLabel("Category:"), 1, 0)
        add_grid_layout.addWidget(self._add_category, 1, 1)
        add_grid_layout.addWidget(QLabel("Use-By Date:"), 2, 0)
        add_grid_layout.addWidget(self._add_date, 2, 1)
        add_grid_layout.addWidget(QLabel("Storage Type:"), 3, 0)
        add_grid_layout.addWidget(self._add_storage, 3, 1)
        
        # Column 2
        add_grid_layout.addWidget(QLabel("Waste Risk Level:"), 0, 2)
        add_grid_layout.addWidget(self._add_risk, 0, 3)
        add_grid_layout.addWidget(QLabel("Demand Level:"), 1, 2)
        add_grid_layout.addWidget(self._add_demand, 1, 3)
        add_grid_layout.addWidget(QLabel("Stock Quantity:"), 2, 2)
        add_grid_layout.addWidget(self._add_qty, 2, 3)
        add_grid_layout.addWidget(QLabel("Allergen Info:"), 3, 2)
        add_grid_layout.addWidget(self._add_allergens, 3, 3)
        
        self._layout_add.addWidget(add_grid_widget)
        self._layout_add.addWidget(self._btn_execute_add, 0, Qt.AlignRight)

        # Edit Section Layout
        self._layout_edit.addWidget(self._lbl_edit_title)

        # Search Entry Bar Form Row
        edit_id_row = QWidget()
        edit_id_layout = QHBoxLayout(edit_id_row)
        edit_id_layout.setContentsMargins(10, 0, 10, 0)
        edit_id_layout.addWidget(QLabel("Enter Item ID to Edit:"))
        edit_id_layout.addWidget(self._input_edit_id)
        edit_id_layout.addStretch()
        self._layout_edit.addWidget(edit_id_row)
        
        # Subform Grid
        edit_grid_widget = QWidget()
        edit_grid_layout = QGridLayout(edit_grid_widget)
        edit_grid_layout.setContentsMargins(10, 10, 10, 10)
        edit_grid_layout.setSpacing(10)
        
        # Column 1
        edit_grid_layout.addWidget(QLabel("Ingredient Name:"), 0, 0)
        edit_grid_layout.addWidget(self._edit_name, 0, 1)
        edit_grid_layout.addWidget(QLabel("Category:"), 1, 0)
        edit_grid_layout.addWidget(self._edit_category, 1, 1)
        edit_grid_layout.addWidget(QLabel("Use-By Date:"), 2, 0)
        edit_grid_layout.addWidget(self._edit_date, 2, 1)
        edit_grid_layout.addWidget(QLabel("Storage Type:"), 3, 0)
        edit_grid_layout.addWidget(self._edit_storage, 3, 1)
        
        # Column 2
        edit_grid_layout.addWidget(QLabel("Waste Risk Level:"), 0, 2)
        edit_grid_layout.addWidget(self._edit_risk, 0, 3)
        edit_grid_layout.addWidget(QLabel("Demand Level:"), 1, 2)
        edit_grid_layout.addWidget(self._edit_demand, 1, 3)
        edit_grid_layout.addWidget(QLabel("Stock Quantity:"), 2, 2)
        edit_grid_layout.addWidget(self._edit_qty, 2, 3)
        edit_grid_layout.addWidget(QLabel("Allergen Info:"), 3, 2)
        edit_grid_layout.addWidget(self._edit_allergens, 3, 3)

        self._edit_form_layout.setContentsMargins(0, 0, 0, 0)
        self._edit_form_layout.addWidget(edit_grid_widget)

        self._edit_form_layout.addWidget(self._btn_execute_update, 0, Qt.AlignRight)
        self._layout_edit.addWidget(self._edit_form_widget)

        # Delete Section Layout
        self._layout_delete.setAlignment(Qt.AlignVCenter)
        self._layout_delete.setContentsMargins(10, 5, 10, 5)
        self._layout_delete.setSpacing(10)
        self._lbl_delete_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._layout_delete.addWidget(self._lbl_delete_title)
        self._layout_delete.addWidget(self._input_delete_id)
        self._layout_delete.addStretch()
        self._layout_delete.addWidget(self._btn_execute_delete)

        # Assemble inside the master edit layout
        self._edit_panel_layout.addWidget(self._frame_add)
        self._edit_panel_layout.addWidget(self._frame_edit)
        self._edit_panel_layout.addWidget(self._frame_delete)
        self._edit_panel_layout.addStretch()
        self._edit_form_widget.hide()  # Invisible until valid entry

        # Setup Inventory View Columns
        self._inventory_table.setColumnCount(3)
        self._inventory_table.setHorizontalHeaderLabels(["Ingredient Name", "Quantity", "Expiry Date"])
        self._inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        header = self._inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self._inventory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._inventory_table.setAlternatingRowColors(True)
        self._inventory_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._item_details_view.setFixedHeight(220)

        # Setup Embed Filter Controls
        self._search_panel.setFixedHeight(108)
        self._search_layout.setContentsMargins(10, 8, 10, 8)
        self._search_layout.setSpacing(8)
        # Lock text boxes to single-row heights
        self._input_food.setPlaceholderText("Filter by Ingredient Name... (or press Enter)")
        self._input_id.setPlaceholderText("Filter by precise ID... (or press Enter)")
        self._btn_submit_search.setFixedWidth(100)

        # Assemble embedded component toolbar elements
        search_text_row = QHBoxLayout()
        search_text_row.setSpacing(10)
        search_text_row.addWidget(self._input_food)
        search_text_row.addWidget(self._input_id)
        search_text_row.addWidget(self._btn_submit_search)
        search_filter_row = QHBoxLayout()
        search_filter_row.setSpacing(10)
        for combo in self._filter_combos.values():
            search_filter_row.addWidget(combo, 1)
        self._btn_reset_search.setFixedWidth(100)
        search_filter_row.addWidget(self._btn_reset_search)
        self._search_layout.addLayout(search_text_row)
        self._search_layout.addLayout(search_filter_row)
        # Add the widgets to your master right-side viewport panel layout stack
        self._display_layout.insertWidget(0, self._search_panel)
        self._search_panel.hide()

        # Assemble Main Layout
        self._main_layout.addWidget(self._sidebar_widget)
        self._workspace_layout.addWidget(self._display_container, 1)
        self._main_layout.addWidget(self._workspace, 1)
      
        self._log_display.setReadOnly(True)
        self._apply_theme_styles()
        self._connect_signals()

    def _setup_main_window_shell(self) -> None:
        """Build presentation around the existing panels and navigation buttons."""
        self._central_widget.setObjectName("MainCanvas")
        style_surface(
            self._central_widget,
            "QWidget#MainCanvas { background: #1b1f22; }"
        )
        self._sidebar_widget.setObjectName("MainSidebar")
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_mark = QLabel("FR")
        brand_mark.setObjectName("BrandMark")
        brand_mark.setFixedSize(40, 40)
        brand_mark.setAlignment(Qt.AlignCenter)
        self._status_label.setText("FoodRescue")
        self._status_label.setObjectName("Brand")
        self._status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        brand_row.addWidget(brand_mark)
        brand_row.addWidget(self._status_label, 1)
        self._sidebar_layout.addLayout(brand_row)
        tagline = QLabel("Less waste. More possibility.")
        self._sidebar_layout.addWidget(tagline)
        self._sidebar_layout.addSpacing(26)

        self._btn_home = QPushButton("Home")
        self._btn_home.setCheckable(True)
        self._btn_home.setChecked(True)
        self._btn_home.setMinimumHeight(38)
        self._btn_home.setCursor(Qt.PointingHandCursor)
        self._btn_home.clicked.connect(self._on_home_triggered)
        self._nav_buttons.insert(0, self._btn_home)
        self._sidebar_layout.addWidget(self._btn_home)
        self._sidebar_layout.addSpacing(16)

        self._navigation_titles = {
            self._btn_home: ("Home", "Your food rescue workspace."),
            self._btn_view_inv: ("Inventory", "Your ingredients, at a glance."),
            self._btn_search_inv: ("Search inventory", "Find ingredients and inspect item details."),
            self._btn_edit_inv: ("Edit inventory", "Manage the ingredients in your inventory."),
            self._btn_inventory_alerts: ("Inventory alerts", "Review expiry and stock alerts."),
            self._btn_ask_ai: ("AI assistant", "Assess ingredients and discover possibilities."),
            self._btn_process_recipes: ("Process recipes", "Evaluate your recipe suggestions."),
            self._btn_view_recipes: ("Recipe library", "Browse your saved recipes."),
            self._btn_search_recipes: ("Search recipes", "Find a recipe for your ingredients."),
        }
        groups = (
            ("INVENTORY", (self._btn_view_inv, self._btn_search_inv,
                           self._btn_edit_inv, self._btn_inventory_alerts)),
            ("KITCHEN", (self._btn_ask_ai, self._btn_process_recipes,
                         self._btn_view_recipes, self._btn_search_recipes)),
        )
        for title, buttons in groups:
            section = QLabel(title)
            section.setObjectName("NavSection")
            self._sidebar_layout.addWidget(section)
            self._sidebar_layout.addSpacing(6)
            for button in buttons:
                button.setText(self._navigation_titles[button][0])
                button.setMinimumHeight(38)
                button.setCursor(Qt.PointingHandCursor)
                self._sidebar_layout.addWidget(button)
            self._sidebar_layout.addSpacing(16)
        self._sidebar_layout.addStretch()
        self._btn_editbusinessrules.setText("Business rules")
        self._sidebar_layout.addWidget(self._btn_editbusinessrules)
        self._btn_exit.setText("Exit application")
        self._btn_exit.setObjectName("ExitButton")
        self._sidebar_layout.addWidget(self._btn_exit)
        style_surface(self._sidebar_widget, SIDEBAR_QSS)

        self._workspace = QWidget()
        self._workspace_layout = QVBoxLayout(self._workspace)
        self._workspace_layout.setContentsMargins(0, 0, 0, 0)
        self._workspace_layout.setSpacing(0)
        self._toolbar = QFrame()
        self._toolbar.setObjectName("MainToolbar")
        toolbar_layout = QHBoxLayout(self._toolbar)
        toolbar_layout.setContentsMargins(28, 20, 28, 20)
        toolbar_layout.setSpacing(10)
        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(4)
        self._page_title = QLabel("Home")
        self._page_title.setObjectName("PageTitle")
        self._page_subtitle = QLabel("Your food rescue workspace.")
        self._page_subtitle.setWordWrap(True)
        heading_layout.addWidget(self._page_title)
        heading_layout.addWidget(self._page_subtitle)
        toolbar_layout.addLayout(heading_layout, 1)
        self._toolbar_search = QPushButton("Search inventory")
        self._toolbar_edit = QPushButton("Edit inventory")
        # Forward to the original buttons so their existing slots remain authoritative.
        self._toolbar_search.clicked.connect(self._btn_search_inv.click)
        self._toolbar_edit.clicked.connect(self._btn_edit_inv.click)
        for button in (self._toolbar_search, self._toolbar_edit):
            button.setCursor(Qt.PointingHandCursor)
            toolbar_layout.addWidget(button)
            button.hide()
        self._theme_bulb = QLabel()
        self._theme_bulb.setFixedSize(32, 32)
        self._theme_bulb.setAlignment(Qt.AlignCenter)
        self._theme_button = ThemeSwitch()
        self._theme_bulb.setBuddy(self._theme_button)
        self._update_theme_icon(False)
        toolbar_layout.addWidget(self._theme_bulb)
        toolbar_layout.addSpacing(10)
        self._theme_button.setToolTip("Turn on dark mode")
        self._theme_button.toggled.connect(self._toggle_theme)
        toolbar_layout.addWidget(self._theme_button)
        style_surface(self._toolbar, TOOLBAR_QSS)
        self._workspace_layout.addWidget(self._toolbar)
        self._display_layout.setContentsMargins(28, 24, 28, 28)
        self._display_layout.setSpacing(16)

        self._welcome_panel = QFrame()
        self._welcome_panel.setObjectName("WelcomePanel")
        welcome_layout = QVBoxLayout(self._welcome_panel)
        welcome_layout.setContentsMargins(40, 40, 40, 40)
        welcome_layout.setSpacing(18)
        self._home_alert_banner = QFrame()
        self._home_alert_banner.setObjectName("HomeAlertBanner")
        home_alert_layout = QHBoxLayout(self._home_alert_banner)
        home_alert_layout.setContentsMargins(14, 10, 14, 10)
        home_alert_layout.setSpacing(10)
        self._home_alert_message = QLabel()
        self._home_alert_message.setWordWrap(True)
        self._home_alert_message.setObjectName("HomeAlertMessage")
        self._btn_home_alert_view = QPushButton("View dashboard")
        self._btn_home_alert_view.setObjectName("HomeAlertViewButton")
        self._btn_home_alert_dismiss = QPushButton("Dismiss")
        self._btn_home_alert_dismiss.setObjectName("HomeAlertDismissButton")
        home_alert_layout.addWidget(self._home_alert_message, 1)
        home_alert_layout.addWidget(self._btn_home_alert_view)
        home_alert_layout.addWidget(self._btn_home_alert_dismiss)
        welcome_layout.addStretch(2)
        eyebrow = QLabel("MAKE THE MOST OF WHAT YOU HAVE")
        eyebrow.setObjectName("WelcomeEyebrow")
        eyebrow.setWordWrap(True)
        title = QLabel("Good food.\nGreater possibilities.")
        title.setObjectName("WelcomeTitle")
        title.setWordWrap(True)
        description = QLabel(
            "Keep ingredients in view, spot what needs attention,\n"
            "and find another purpose for the food you have."
        )
        description.setWordWrap(True)
        for label in (eyebrow, title, description):
            welcome_layout.addWidget(label)
        welcome_layout.addSpacing(8)
        self._welcome_inventory_button = QPushButton("View inventory")
        self._welcome_inventory_button.setCursor(Qt.PointingHandCursor)
        self._welcome_inventory_button.clicked.connect(self._btn_view_inv.click)
        welcome_layout.addWidget(self._welcome_inventory_button, 0, Qt.AlignLeft)
        welcome_layout.addStretch(3)
        footnote = QLabel("Inventory  /  Recipes  /  AI assistance")
        footnote.setObjectName("WelcomeFootnote")
        footnote.setWordWrap(True)
        welcome_layout.addWidget(footnote)
        welcome_layout.addWidget(self._home_alert_banner)
        self._home_alert_banner.hide()
        style_surface(self._welcome_panel, WELCOME_QSS)
        self._display_layout.addWidget(self._welcome_panel, 1)
        self._log_display.hide()

    def _apply_theme_styles(self) -> None:
        for title in (self._lbl_add_title, self._lbl_edit_title, self._lbl_delete_title):
            title.setObjectName("SectionTitle")
        style_surface(self, APPLICATION_QSS)
        style_inventory_table(self._inventory_table)
        style_inventory_table(self._alert_table)
        style_surface(
            self._alert_table,
            INVENTORY_QSS
            + "\nQTableWidget::item:focus { border: none; }"
        )
        for editor in (self._log_display, self._item_details_view):
            editor.document().setDefaultFont(self.font())
        for layout in (self._layout_add, self._layout_edit):
            layout.setContentsMargins(18, 18, 18, 18)
            layout.setSpacing(12)
        apply_theme(self, False)

    def _dialog_text_color(self) -> str:
        # Black on the light theme, white on the dark theme.
        return "#ffffff" if self._dark_mode else "#000000"

    def _toggle_theme(self, dark: bool) -> None:
        self._dark_mode = dark
        apply_theme(self, dark)
        self._update_theme_icon(dark)
        self._theme_button.setToolTip("Turn off dark mode" if dark else "Turn on dark mode")

    def _update_theme_icon(self, dark: bool) -> None:
        name = "dark-mode.png" if dark else "light-mode.png"
        source = QPixmap(os.path.join(os.path.dirname(__file__), "icons", name))
        scale = self.devicePixelRatioF()
        pixmap = source.scaled(round(28 * scale), round(28 * scale),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap.setDevicePixelRatio(scale)
        # Keep the supplied silhouette visible against the dark toolbar.
        if dark:
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), Qt.lightGray)
            painter.end()
        self._theme_bulb.setPixmap(pixmap)
        description = "Dark mode" if dark else "Light mode"
        self._theme_bulb.setToolTip(description)
        self._theme_bulb.setAccessibleName(description)

    def _connect_signals(self) -> None:
        self._btn_view_inv.clicked.connect(self._on_inventory_view_triggered)
        self._btn_search_inv.clicked.connect(self._on_search_inventory_triggered)
        # live search: the list is re-filtered after every letter typed or deleted
        self._input_food.textChanged.connect(lambda _text: self._execute_embedded_search(show_card=False))
        self._input_id.textChanged.connect(lambda _text: self._execute_embedded_search(show_card=False))
        self._input_food.returnPressed.connect(self._execute_embedded_search)
        self._input_id.returnPressed.connect(self._execute_embedded_search)
        self._btn_submit_search.clicked.connect(self._execute_embedded_search)
        for combo in self._filter_combos.values():
            combo.currentIndexChanged.connect(lambda _index: self._execute_embedded_search(show_card=False))
        self._btn_reset_search.clicked.connect(self._on_reset_search_clicked)
        self._btn_edit_inv.clicked.connect(self._on_edit_inventory_triggered)
        self._btn_execute_add.clicked.connect(self._execute_gui_add)
        self._add_name.returnPressed.connect(self._execute_gui_add)
        self._add_qty.returnPressed.connect(self._execute_gui_add)
        self._add_allergens.returnPressed.connect(self._execute_gui_add)
        self._add_date.lineEdit().returnPressed.connect(self._execute_gui_add)
        self._btn_ask_ai.clicked.connect(self._on_ask_ai_triggered)
        self._btn_process_recipes.clicked.connect(self._on_process_recipes_triggered)
        self._btn_view_recipes.clicked.connect(self._on_recipes_view_triggered)
        self._btn_search_recipes.clicked.connect(self._on_search_recipes_triggered)
        self._btn_inventory_alerts.clicked.connect(self._on_inventory_alerts_triggered)
        self._btn_refresh_alerts.clicked.connect(self._refresh_inventory_alerts)
        self._btn_delete_expired_alert.clicked.connect(
            self._delete_selected_expired_item
        )
        self._btn_home_alert_dismiss.clicked.connect(self._dismiss_home_alert)
        self._btn_home_alert_view.clicked.connect(self._view_alerts_from_home)
        self._inventory_table.itemClicked.connect(self._on_table_row_clicked)
        self._inventory_table.verticalHeader().sectionClicked.connect(self._on_header_section_clicked)
        self._input_edit_id.returnPressed.connect(self._on_edit_id_modified)
        self._btn_execute_update.clicked.connect(self._execute_gui_update)
        self._edit_name.returnPressed.connect(self._execute_gui_update)
        self._edit_qty.returnPressed.connect(self._execute_gui_update)
        self._edit_date.lineEdit().returnPressed.connect(self._execute_gui_update)
        self._edit_allergens.returnPressed.connect(self._execute_gui_update)
        self._btn_execute_delete.clicked.connect(self._execute_gui_delete)
        self._input_delete_id.returnPressed.connect(self._execute_gui_delete)
        self._btn_execute_ai.clicked.connect(self._execute_threaded_ai_analysis)
        self._input_recipe_ingredient.returnPressed.connect(self._execute_embedded_recipe_search)
        self._input_recipe_id.returnPressed.connect(self._execute_embedded_recipe_search)        
        self._btn_submit_recipe_search.clicked.connect(self._execute_embedded_recipe_search)
        self._btn_editbusinessrules.clicked.connect(self._on_edit_business_rules_triggered)
        self._btn_exit.clicked.connect(self._execute_graceful_exit)

    def _show_success_message(self, title: str, text: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(480, 130)
        dialog.resize(520, 145)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(12)
        message = QLabel(text)
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(message)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons, 0, Qt.AlignRight)
        dialog.exec()

    def _show_error_message(self, title: str, text: str) -> None:
        # displays a custom themed alert dialog box for error messages
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setIcon(QMessageBox.Icon.NoIcon)

        content_label = QLabel()
        content_label.setWordWrap(True)
        
        formatted_rich_text = (
            f"<div style='vertical-align: middle; display: flex; align-items: center; word-break: break-all;'> "
            f"  <span style='color: #e74c3c; font-size: 24px; font-weight: bold; font-family: Arial;'>✘</span>"
            f"  <span style='color: {self._dialog_text_color()}; font-size: 13px; font-weight: normal; margin-left: 14px;'>{text}</span>"
            f"</div>"
        )
        content_label.setText(formatted_rich_text)
        msg.layout().addWidget(content_label, 0, 1)
        msg.setStyleSheet("QMessageBox { border-left: 5px solid #e74c3c; }")
        msg.exec()

    def _update_active_navigation_state(self, active_button: QPushButton) -> None:
        # Presentation only: existing handlers still own panel visibility and data.
        self._welcome_panel.hide()
        self._recipe_cards.hide()
        self._inventory_table.setMinimumHeight(0)
        self._inventory_table.setMaximumHeight(16777215)
        self._item_details_view.setMinimumHeight(0)
        self._item_details_view.setMaximumHeight(16777215)
        style_surface(self._log_display, "")
        title, subtitle = self._navigation_titles.get(
            active_button, ("FoodRescue", "Your food rescue workspace.")
        )
        self._page_title.setText(title)
        self._page_subtitle.setText(subtitle)
        is_inventory = active_button is self._btn_view_inv
        self._toolbar_search.setVisible(is_inventory)
        self._toolbar_edit.setVisible(is_inventory)
        for btn in self._nav_buttons:
            btn.setChecked(btn == active_button)
        self._alert_panel.hide()

    def _on_home_triggered(self) -> None:
        """Return to the welcome surface without changing data or background work."""
        self._update_active_navigation_state(self._btn_home)
        for panel in (
            self._search_panel, self._recipe_search_panel, self._edit_scroll_area,
            self._frame_ai_input, self._inventory_table, self._item_details_view,
            self._log_display,
        ):
            panel.hide()
        self._welcome_panel.show()
        self._refresh_home_alert_banner()

    def set_controller(self, controller) -> None:
       # safely mutates internal controller reference
        self._controller = controller
        self._refresh_home_alert_banner()

    def _refresh_home_alert_banner(self) -> None:
        if self._home_alert_dismissed or not self._controller:
            self._home_alert_banner.hide()
            return

        alerts = self._controller.inventory_alert_service.get_alerts(
            self._controller.data_manager.inventory.records
        )
        item_ids = {
            entry["id"]
            for entries in alerts.values()
            for entry in entries
        }
        if not item_ids:
            self._home_alert_banner.hide()
            return

        item_count = len(item_ids)
        message = (
            "1 inventory item requires attention."
            if item_count == 1
            else f"{item_count} inventory items require attention."
        )
        self._home_alert_message.setText(
            f"Attention needed: {message}"
        )
        self._home_alert_banner.show()

    def _dismiss_home_alert(self) -> None:
        self._home_alert_dismissed = True
        self._home_alert_banner.hide()

    def _view_alerts_from_home(self) -> None:
        self._dismiss_home_alert()
        self._on_inventory_alerts_triggered()
    
    def display_main_menu(self) -> None:
        self.show()
 
    # Option 1: View inventory Stocks
    def _on_inventory_view_triggered(self) -> None:
        # internal callback to bridge data safely controller
        if self._controller and hasattr(self._controller, "data_manager"):
            self._update_active_navigation_state(self._btn_view_inv)
            # Pull records safely from the data framework layer
            self._search_panel.hide()
            self._edit_scroll_area.hide()
            self._frame_ai_input.hide()
            self._item_details_view.clear()
            self._item_details_view.hide()
            self._recipe_search_panel.hide()

            self._inventory_table.setMaximumHeight(16777215)
            self._inventory_table.setMinimumHeight(0)
            self._inventory_table.show()
            records = self._controller.data_manager.inventory.records
            self.print_current_inventory(records)

    def _on_inventory_alerts_triggered(self) -> None:
        if not self._controller:
            return
        self._update_active_navigation_state(self._btn_inventory_alerts)
        for widget in (
            self._search_panel,
            self._recipe_search_panel,
            self._edit_scroll_area,
            self._frame_ai_input,
            self._inventory_table,
            self._item_details_view,
            self._log_display,
        ):
            widget.hide()
        self._alert_panel.show()
        self._refresh_inventory_alerts()

    def _on_edit_business_rules_triggered(self) -> None:
        if not self._controller:
            return

        try:
            rules = self._controller.load_business_rules()
        except (OSError, ValueError) as exc:
            self._show_error_message("Could not load business rules", str(exc))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Business Rules")
        dialog.resize(850, 600)
        dialog.setMinimumSize(760, 600)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Select a recipe:"))
        recipe_list = QListWidget()
        recipe_list.setObjectName("BusinessRulesRecipeList")
        recipe_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(recipe_list, 2)
                

        layout.addWidget(QLabel("Recipe name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        ingredient_list = QListWidget()
        ingredient_list.setMaximumHeight(170)
        layout.addWidget(ingredient_list)   

        ingredient_buttons = QHBoxLayout()
        add_ingredient_button = QPushButton("Add ingredient")
        remove_ingredient_button = QPushButton("Remove selected ingredient")
        ingredient_buttons.addWidget(add_ingredient_button)
        ingredient_buttons.addWidget(remove_ingredient_button)
        layout.addLayout(ingredient_buttons)
        

        recipe_buttons = QHBoxLayout()
        add_recipe_button = QPushButton("Add recipe")
        remove_recipe_button = QPushButton("Remove selected recipe")
        recipe_buttons.addWidget(add_recipe_button)
        recipe_buttons.addWidget(remove_recipe_button)
        layout.addLayout(recipe_buttons)


        save_buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=dialog,
        )
        layout.addWidget(save_buttons)

        current_index = None
        
        def store_current_recipe() -> None:
            if current_index is None:
                return

            rules[current_index]["name"] = name_input.text().strip()
            rules[current_index]["ingredients"] = [
                ingredient_list.item(i).text().strip()
                for i in range(ingredient_list.count())
            ]

        def show_recipe(index: int) -> None:
            nonlocal current_index
            store_current_recipe()

            current_index = index
            recipe = rules[index]
            name_input.setText(recipe["name"])

            ingredient_list.clear()
            ingredient_list.addItems(recipe["ingredients"])

        def refresh_recipe_list(select_index: int = 0) -> None:
            recipe_list.clear()
            recipe_list.addItems([rule["name"] for rule in rules])

            if rules:
                recipe_list.setCurrentRow(select_index)
                show_recipe(select_index)
            else:
                name_input.clear()
                ingredient_list.clear()

        recipe_list.currentRowChanged.connect(
            lambda index: show_recipe(index) if index >= 0 else None
        )

        def add_ingredient() -> None:
            ingredient, accepted = QInputDialog.getText(
                dialog, "Add ingredient", "Ingredient name:"
            )
            if accepted and ingredient.strip():
                ingredient_list.addItem(ingredient.strip())

        def remove_ingredient() -> None:
            row = ingredient_list.currentRow()
            if row >= 0:
                ingredient_list.takeItem(row)

        def add_recipe() -> None:
            name, accepted = QInputDialog.getText(
                dialog, "Add recipe", "Recipe name:"
            )
            if not accepted or not name.strip():
                return

            store_current_recipe()
            rules.append({"name": name.strip(), "ingredients": []})
            refresh_recipe_list(len(rules) - 1)

        def remove_recipe() -> None:
            nonlocal current_index
            row = recipe_list.currentRow()
            if row < 0:
                return

            rules.pop(row)
            current_index = None
            refresh_recipe_list(min(row, len(rules) - 1))
        def edit_ingredient(item) -> None:
            new_text, accepted = QInputDialog.getText(
                dialog,
                "Edit ingredient",
                "Ingredient name:",
                QLineEdit.Normal,
                item.text(),
            )

            if accepted and new_text.strip():
                item.setText(new_text.strip())

        ingredient_list.itemDoubleClicked.connect(edit_ingredient)

        def save_rules() -> None:
            store_current_recipe()
            try:
                self._controller.editbusinessrules(rules)
            except (OSError, ValueError) as exc:
                self._show_error_message("Could not save business rules", str(exc))
                return

            dialog.accept()
            self._show_success_message(
                "Business rules saved",
                "Your recipe rules were updated.",
            )

        add_ingredient_button.clicked.connect(add_ingredient)
        remove_ingredient_button.clicked.connect(remove_ingredient)
        add_recipe_button.clicked.connect(add_recipe)
        remove_recipe_button.clicked.connect(remove_recipe)
        save_buttons.accepted.connect(save_rules)
        save_buttons.rejected.connect(dialog.reject)

        refresh_recipe_list()
        dialog.exec()


    def _refresh_inventory_alerts(self) -> None:
        if not self._controller:
            return
        try:
            self._controller.data_manager.load()
            alerts = self._controller.inventory_alert_service.get_alerts(
                self._controller.data_manager.inventory.records
            )
        except (OSError, ValueError, TypeError) as error:
            self._alert_table.setRowCount(0)
            self._expired_alert_ids.clear()
            self._btn_delete_expired_alert.setEnabled(False)
            self._alert_summary.setText("Could not load inventory alerts.")
            self._show_error_message("Inventory alerts unavailable", str(error))
            return

        self._expired_alert_ids = {
            entry["id"] for entry in alerts["expired"]
        }
        status_labels = {
            "expired": "Expired",
            "expiring_soon": "Expiring soon",
            "low_stock": "Low stock",
            "unknown_expiry": "Check expiry date",
        }
        by_id = {}
        for alert_name, entries in alerts.items():
            for entry in entries:
                item_id = entry["id"]
                item = by_id.setdefault(item_id, {**entry, "statuses": []})
                item["statuses"].append(status_labels[alert_name])

        self._alert_table.setRowCount(len(by_id))
        for row, (item_id, item) in enumerate(by_id.items()):
            record = item["record"]
            quantity = record.get("quantity")
            values = (
                str(item_id),
                str(record.get("food", "")),
                str(quantity) if quantity is not None else "Unknown",
                str(record.get("use-by", "")),
                (
                    str(item["days_remaining"])
                    if item["days_remaining"] is not None
                    else "Unknown"
                ),
                ", ".join(item["statuses"]),
            )
            checkbox = QCheckBox()
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setEnabled(item_id in self._expired_alert_ids)
            checkbox.toggled.connect(self._update_expired_delete_button)
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.addWidget(checkbox)
            self._alert_table.setCellWidget(row, 0, checkbox_container)
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setTextAlignment(Qt.AlignCenter)
                self._alert_table.setItem(row, column + 1, cell)
            self._alert_table.item(row, 1).setData(Qt.UserRole, dict(record))

        self._alert_table.resizeRowsToContents()
        self._update_expired_delete_button()

        self._alert_summary.setText(
            f"Expired: {len(alerts['expired'])}  |  "
            f"Expiring within {DEFAULT_EXPIRING_WITHIN_DAYS} days: "
            f"{len(alerts['expiring_soon'])}  |  "
            f"Low stock: "
            f"{len(alerts['low_stock'])}  |  "
            f"Check expiry date: {len(alerts['unknown_expiry'])}"
        )
        if not by_id:
            self._alert_summary.setText(
                self._alert_summary.text() + "\nNo items currently need attention."
            )

    def _update_expired_delete_button(self) -> None:
        self._btn_delete_expired_alert.setEnabled(
            bool(self._get_checked_expired_items())
        )

    def _get_checked_expired_items(self) -> list:
        selected_items = []
        for row in range(self._alert_table.rowCount()):
            checkbox_container = self._alert_table.cellWidget(row, 0)
            checkbox = (
                checkbox_container.findChild(QCheckBox)
                if checkbox_container is not None
                else None
            )
            item_id_cell = self._alert_table.item(row, 1)
            if (
                checkbox is None
                or item_id_cell is None
                or not checkbox.isChecked()
            ):
                continue
            try:
                item_id = int(item_id_cell.text())
            except ValueError:
                continue
            if item_id in self._expired_alert_ids:
                selected_items.append(
                    (item_id, item_id_cell.data(Qt.UserRole))
                )
        return selected_items

    def _delete_selected_expired_item(self) -> None:
        if not self._controller:
            return

        selected_items = self._get_checked_expired_items()
        if not selected_items:
            self._show_error_message(
                "Select an expired item",
                "Check at least one expired inventory item before deleting.",
            )
            return

        inventory = self._controller.data_manager.inventory
        try:
            self._controller.data_manager.load()
            records = inventory.records
            expired_ids = {
                entry["id"]
                for entry in self._controller.inventory_alert_service.get_alerts(
                    records
                )["expired"]
            }
            stale_selection = any(
                not isinstance(selected_record, dict)
                or not 0 < item_id <= len(records)
                or records[item_id - 1] != selected_record
                or item_id not in expired_ids
                for item_id, selected_record in selected_items
            )
            if stale_selection:
                self._refresh_inventory_alerts()
                self._show_error_message(
                    "Inventory changed",
                    "One or more selected items changed or are no longer expired. "
                    "Alerts have been refreshed; check the items again.",
                )
                return

            named_items = [
                (item_id, records[item_id - 1].get("food", ""))
                for item_id, _ in selected_items
            ]
            item_lines = "\n".join(
                f"- {name} (ID: {item_id})"
                for item_id, name in named_items
            )
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Record Deletion")
            msg_box.setTextFormat(Qt.PlainText)
            msg_box.setText(
                "Are you sure you want to permanently remove these expired "
                f"items from active stock logs?\n\n{item_lines}"
            )
            msg_box.setMinimumWidth(620)
            msg_box.setStyleSheet("QLabel { min-width: 560px; }")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            if msg_box.exec() != QMessageBox.Yes:
                return

            for item_id, _ in sorted(selected_items, reverse=True):
                inventory.delete(item_id - 1)
            self._refresh_inventory_alerts()
            self._show_success_message(
                "Success",
                f"Success: Removed {len(selected_items)} expired "
                f"{'item' if len(selected_items) == 1 else 'items'} from the inventory.",
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "System Failure",
                f"Could not delete the expired inventory item: {error}",
            )

    # Option 2: Search Inventory
    def _on_search_inventory_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_search_inv)
        # displays the embedded search text bars row layout inside the dashboard
        self._log_display.hide()
        self._item_details_view.hide()
        self._edit_scroll_area.hide()
        self._frame_ai_input.hide()
        self._inventory_table.show()
        self._search_panel.show()

        self._inventory_table.setMaximumHeight(340)

        # start every visit with empty boxes and dropdowns so they match the full list shown below
        self._reset_search_fields()
        self._input_food.setFocus()

        if self._controller:
            self.print_current_inventory(self._controller.data_manager.inventory.records)

    @staticmethod
    def _build_filter_options(records: list) -> dict:
        # The values to offer in each dropdown, taken from the inventory itself.
        def unique(values) -> list:
            seen = {}
            for value in values:
                value = (value or "").strip()
                if value and value.lower() not in seen:
                    seen[value.lower()] = value
            return list(seen.values())

        def ordered(values, preferred) -> list:
            found = unique(values)
            first = [p for p in preferred if p.lower() in {f.lower() for f in found}]
            rest = [f for f in found if f.lower() not in {p.lower() for p in first}]
            return first + sorted(rest, key=str.lower)

        allergens = []
        for record in records:
            for part in re.split(r"[,;/]", record.get("allergen info") or ""):
                name = re.sub(r"\s*\(.*?\)", "", part).strip()        # "Wheat (Gluten)" -> "Wheat"
                if name.lower() != "none":
                    allergens.append(name)

        return {
            "food_category": sorted(unique(r.get("food_category") for r in records), key=str.lower),
            "storage_condition": sorted(unique(r.get("storage condition") for r in records), key=str.lower),
            "waste_risk_level": ordered((r.get("waste_risk_level") for r in records), ["Low", "Medium", "High", "Critical"]),
            "allergen": sorted(unique(allergens), key=str.lower),
            "demand_level": ordered((r.get("demand level") for r in records), ["Low", "Medium", "High"]),
        }

    def _reset_search_fields(self) -> None:
        # Empties both text boxes and refills every dropdown from the current inventory, set to "All".
        for box in (self._input_food, self._input_id):
            box.blockSignals(True)
            box.clear()
            box.blockSignals(False)

        records = self._controller.data_manager.inventory.records if self._controller else []
        options = self._build_filter_options(records)
        all_text = {
            "food_category": "All categories",
            "storage_condition": "Any storage",
            "waste_risk_level": "Any waste risk",
            "allergen": "Any allergen",
            "demand_level": "Any demand",
        }
        for key, combo in self._filter_combos.items():
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(all_text[key], None)
            if key == "allergen":
                combo.addItem("No allergens", "none")
            for value in options[key]:
                combo.addItem(value, value)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def _on_reset_search_clicked(self) -> None:
        self._reset_search_fields()
        self._input_food.setFocus()
        self._execute_embedded_search(show_card=False)

    def _selected_inventory_filters(self) -> dict:
        # The dropdowns that are set to something other than "All", as filter() arguments.
        chosen = {key: combo.currentData() for key, combo in self._filter_combos.items()}
        return {key: value for key, value in chosen.items() if value is not None}

    def _execute_embedded_search(self, *_signal_args, show_card: bool = True) -> None:
        # extracts data strings inline from GUI text bars n applies active queries
        # show_card=False is used while typing, so the layout doesn't jump around as the list narrows
        if not self._controller:
            return

        # xtract values cleanly directly from your desktop interface boxes
        food_text = self._input_food.text().strip()
        id_text = self._input_id.text().strip()

        # sanitize parameter types to pass cleanly to database search modules
        food_filter = food_text if food_text else None
        id_filter = int(id_text) if id_text and id_text.isdigit() else None

        results = self._controller.data_manager.inventory.search(food=food_filter, item_id=id_filter)

        # keep only the rows that also pass the dropdown filters
        dropdown_filter = InventoryFilter(**self._selected_inventory_filters())
        if dropdown_filter.is_active():
            results = dropdown_filter.apply(results)
        
        if results:
            record_ids = self._controller._get_record_ids(self._controller.data_manager.inventory.records, results)
            self.print_current_inventory(results, record_ids)
            
            if len(results) == 1 and show_card:
                    self._load_food_profile_by_row(0)
            else:
                self._item_details_view.hide()
        else:
            self._inventory_table.setRowCount(0)
            self._item_details_view.hide()

    def _on_table_row_clicked(self, item) -> None:
        if not item: return
        if self._btn_search_recipes.isChecked():
            self._load_recipe_profile_by_row(item.row())
        else:
            self._load_food_profile_by_row(item.row())

    def _on_header_section_clicked(self, row_idx: int) -> None:
        if self._btn_search_recipes.isChecked():
            self._load_recipe_profile_by_row(row_idx)
        else:
            self._load_food_profile_by_row(row_idx)

    # Item Details Card Loader
    def _load_food_profile_by_row(self, row_idx: int) -> None:
        # extracts complete underlying data metrics for the clicked row n renders them
        if not self._controller or not self._search_panel.isVisible():
            return

        header_item = self._inventory_table.verticalHeaderItem(row_idx)
        if not header_item:
            return

        try:
            db_id = int(header_item.text()) - 1
        except ValueError:
            return
            
        records = self._controller.data_manager.inventory.records

        if 0 <= db_id < len(records):
            target = records[db_id]
            self._item_details_view.show()
            self._item_details_view.clear()
            
            allergen = target.get('allergen info', 'None') or 'None'
            storage = target.get('storage condition', 'Ambient')
            days_left = target.get('days_to_expiry', 'N/A')
            expiry_str = f"{days_left} day(s) remaining" if str(days_left).isdigit() else str(days_left)

            fields = (
                ("Category", target.get('food_category', 'General')),
                ("Stock quantity", target.get('quantity', '0')),
                ("Use-by date", target.get('use-by', 'N/A')),
                ("Days to expiry", expiry_str), ("Storage", storage),
                ("Waste risk", target.get('waste_risk_level', 'Low')),
                ("Demand level", target.get('demand level', 'Normal')),
                ("Allergens", allergen),
            )
            rows = "".join(
                f"<tr><td style='color: #a7b7ad;'>{label}</td><td>{escape(str(value))}</td></tr>"
                for label, value in fields
            )
            set_themed_html(self._item_details_view,
                f"<p style='color: #a7cbb6;'>ITEM {db_id + 1:02d}</p>"
                f"<h2 style='color: #f0f3f1; font-size: 20px;'>{escape(target.get('food', 'Unknown'))}</h2>"
                f"<table width='100%' cellpadding='5' style='color: #dce3df;'>{rows}</table>"
            )

    # Data Renders
    def print_current_inventory(self, extracted_items: list, ids: list = None) -> bool:
        self._log_display.hide()
        self._item_details_view.hide()
        self._inventory_table.show()
        self._inventory_table.setRowCount(0)
        
        if not extracted_items:
            return False

        self._inventory_table.setColumnCount(3)
        self._inventory_table.setHorizontalHeaderLabels(["Ingredient Name", "Quantity", "Expiry Date"])

        header = self._inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)            
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  

        self._inventory_table.setRowCount(len(extracted_items))
        for row, record in enumerate(extracted_items):
            item_num = str(ids[row]) if ids else str(row + 1)
            qty = "" if record.get('quantity') is None else str(record['quantity'])
            
            self._inventory_table.setVerticalHeaderItem(row, QTableWidgetItem(item_num))

            # Ingrediant Name
            name_item = QTableWidgetItem(record.get('food', 'Unknown'))
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._inventory_table.setItem(row, 0, name_item)
            # Quantity
            qty_item = QTableWidgetItem(qty)
            qty_item.setTextAlignment(Qt.AlignCenter)
            self._inventory_table.setItem(row, 1, qty_item)
            # Expiry Date
            date_item = QTableWidgetItem(record.get('use-by', 'N/A'))
            date_item.setTextAlignment(Qt.AlignCenter)
            self._inventory_table.setItem(row, 2, date_item)
        return True

    # Option 3: Edit Inventory Items
    def _on_edit_inventory_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_edit_inv)
        self._search_panel.hide()
        self._item_details_view.hide()
        self._log_display.hide()
        self._frame_ai_input.hide()
        self._recipe_search_panel.hide()
        
        # Keep inventory table visible
        self._inventory_table.setFixedHeight(230)
        self._inventory_table.show()

        self._edit_form_widget.hide()        
        self._edit_scroll_area.show()

        self._display_layout.setStretchFactor(self._inventory_table, 1)
        self._display_layout.setStretchFactor(self._edit_panel, 2)
        
        if self._controller and hasattr(self._controller, "data_manager"):
            self._controller.data_manager.load()
            self.print_current_inventory(self._controller.data_manager.inventory.records)

    def _execute_gui_add(self) -> None:
        # Extracts and validates input variables when adding new stock items
        if not self._controller: return
        name = self._add_name.text().strip()
        qty_str = self._add_qty.text().strip()
        date_str = self._add_date.text().strip()
        
        if not name or not qty_str or not date_str:
            self._show_error_message("Validation Error", "Name, Quantity, and Expiry Date fields are mandatory.")
            return
        if not qty_str.isdigit():
            self._show_error_message("Validation Error", "Stock Quantity must be a valid whole number.")
            return

        try:
            parsed_dt = datetime.strptime(date_str, "%d/%m/%Y")
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if parsed_dt < today:
                self._show_error_message("Validation Error", "The expiration date cannot be in the past.")
                return
            calculated_days = max(0, (parsed_dt - datetime.today()).days + 1)
        except ValueError:
            self._show_error_message("Validation Error", "Invalid date format. Use DD/MM/YYYY.")
            return

        allergens = self._add_allergens.text().strip()
        details = {
            "food": name,
            "food_category": self._add_category.currentText(),
            "use_by": date_str,
            "storage_condition": self._add_storage.currentText(),
            "days_to_expiry": calculated_days,
            "waste_risk_level": self._add_risk.currentText(),
            "allergen_info": allergens if allergens else "None",
            "demand_level": self._add_demand.currentText(),
            "quantity": int(qty_str)
        }

        try:
            self._controller.data_manager.inventory.add(**details)
            self._show_success_message("Success", f"Success: '{name}' successfully added.")
            # Clear input fields upon success
            self._add_name.clear(); self._add_qty.clear(); self._add_date.clear(); self._add_allergens.clear()
            self.print_current_inventory(self._controller.data_manager.inventory.records)
        except Exception as e:
            QMessageBox.critical(self, "System Failure", f"Could not sync file records: {e}")

    def _on_edit_id_modified(self) -> None:
       # fires when the ID changes. Pre-populates fields as transparent reminders
        text = self._input_edit_id.text().strip()
        if not text or not text.isdigit() or not self._controller:
            self._lbl_edit_title.setText("Edit:")
            self._edit_form_widget.hide()
            return

        idx = int(text) - 1
        records = self._controller.data_manager.inventory.records
        
        if 0 <= idx < len(records):
            target = records[idx]
            self._lbl_edit_title.setText(f"Edit {target.get('food', '')}:")
            
            # Map database record fields directly into inputs
            self._edit_name.setText(target.get('food', ''))
            self._edit_qty.setText(str(target.get('quantity', '0')))
            use_by = target.get("use-by", "")
            edit_date = QDate.fromString(use_by, "dd/MM/yyyy")
            if not edit_date.isValid():
                edit_date = QDate.fromString(use_by, "dd-MM-yyyy")
            self._edit_date.setDate(edit_date if edit_date.isValid() else QDate.currentDate())
            self._edit_category.setCurrentText(target.get('food_category', 'Other'))
            self._edit_storage.setCurrentText(target.get('storage condition', 'Ambient'))
            self._edit_risk.setCurrentText(target.get('waste_risk_level', 'Low'))
            self._edit_demand.setCurrentText(target.get('demand level', 'Low').capitalize())
            self._edit_allergens.setText(target.get('allergen info', 'None'))
            
            self._edit_form_widget.show()
        else:
            self._lbl_edit_title.setText("Edit (ID out of bounds):")
            self._edit_form_widget.hide()

    def _execute_gui_update(self) -> None:
       # validates entry modifications and commits changes to files
        if not self._controller: return
        idx = int(self._input_edit_id.text().strip()) - 1
        
        name = self._edit_name.text().strip()
        qty_str = self._edit_qty.text().strip()
        date_str = self._edit_date.date().toString("dd/MM/yyyy")

        if not name or not qty_str or not date_str:
            self._show_error_message("Validation Error", "All primary edit lines must be populated.")
            return

        if not qty_str.isdigit():
            self._show_error_message("Validation Error", "Stock Quantity must be a valid whole number.")
            return

        try:
            parsed_dt = datetime.strptime(date_str, "%d/%m/%Y")
            calculated_days = max(0, (parsed_dt - datetime.today()).days + 1)
        except ValueError:
            self._show_error_message("Validation Error", "Invalid date format. Use DD/MM/YYYY.")
            return

        details = {
            "food": name,
            "food_category": self._edit_category.currentText(),
            "use_by": date_str,
            "storage_condition": self._edit_storage.currentText(),
            "days_to_expiry": calculated_days,
            "waste_risk_level": self._edit_risk.currentText(),
            "allergen_info": self._edit_allergens.text().strip(),
            "demand_level": self._edit_demand.currentText(),
            "quantity": int(qty_str)
        }

        try:
            self._controller.data_manager.inventory.update(idx, **details)
            self._show_success_message("Success", f"Success: Updated data for '{name}'.")
            self._input_edit_id.clear()
            self._edit_form_widget.hide()
            self.print_current_inventory(self._controller.data_manager.inventory.records)
        except Exception as e:
            QMessageBox.critical(self, "System Failure", f"Could not write configuration updates: {e}")

    def _execute_gui_delete(self) -> None:
        # removes the record by its row tracking index index
        if not self._controller: 
            return
            
        id_str = self._input_delete_id.text().strip()
        if not id_str or not id_str.isdigit():
            self._show_error_message("Validation Error", "Please provide a valid item ID to remove.")
            return

        idx = int(id_str) - 1
        records = self._controller.data_manager.inventory.records
        
        if 0 <= idx < len(records):
            removed_name = records[idx]['food']
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Record Deletion")
            msg_box.setStyleSheet(
                "QMessageBox { border-left: 5px solid #c0392b; } "
                "QLabel { min-width: 480px; color: " + self._dialog_text_color() + "; font-size: 13px; }"
            )
            msg_box.setText(f"Are you sure you want to permanently remove '{removed_name}' (ID: {id_str}) from active stock logs?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            if msg_box.exec() == QMessageBox.Yes:
                try:
                    self._controller.data_manager.inventory.delete(idx)
                    self._show_success_message("Success", f"Success: Removed '{removed_name}' from the inventory.")
                    self._input_delete_id.clear()
                    self.print_current_inventory(self._controller.data_manager.inventory.records)
                except Exception as e:
                    QMessageBox.critical(self, "System Failure", f"Deletion failed: {e}")
        else:
            self._show_error_message("Validation Error", "Item ID out of active inventory limits.")

    # Option 4: AI Assistant
    def _on_ask_ai_triggered(self) -> None:
        # selects items via GUI popups and forwards execution context directly to the controller engine
        if not self._controller:
            return

        self._update_active_navigation_state(self._btn_ask_ai)
        self._search_panel.hide()
        self._item_details_view.hide()
        self._edit_scroll_area.hide()
        self._recipe_search_panel.hide()

        self._inventory_table.setFixedHeight(340)
        self._inventory_table.show()
        
        if self._frame_ai_input.layout() is not None:
            old_layout = self._frame_ai_input.layout()
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget() and child.widget() != self._log_display:
                    child.widget().hide()
                    child.widget().deleteLater()
            QWidget().setLayout(old_layout)

        master_layout = QVBoxLayout(self._frame_ai_input)
        master_layout.setContentsMargins(20, 20, 20, 20)
        master_layout.setSpacing(14)

        # Main Descriptive Title Header Label block
        title_lbl = QLabel("Ingredient assessment")
        title_lbl.setObjectName("SectionTitle")
        master_layout.addWidget(title_lbl)

        self._ai_inputs_row = QWidget()
        row_layout = QHBoxLayout(self._ai_inputs_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        self._input_ai_id = QLineEdit()
        self._input_ai_id.setPlaceholderText("Item ID, e.g. 36")
        self._input_ai_id.setFixedWidth(145)

        self._input_ai_notes = QLineEdit()
        self._input_ai_notes.setPlaceholderText("Quality observations (optional)")

        self._btn_execute_ai = QPushButton("Assess item")
        self._btn_execute_ai.setObjectName("ApplyFilterButton")
        self._btn_execute_ai.setFixedWidth(116)
        self._btn_execute_ai.clicked.connect(self._execute_threaded_ai_analysis)

        # Assemble inline components horizontally onto the row layout matrix
        row_layout.addWidget(self._input_ai_id)
        row_layout.addWidget(self._input_ai_notes)
        row_layout.addWidget(self._btn_execute_ai)
        master_layout.addWidget(self._ai_inputs_row)

        status_row = QWidget()
        status_row_layout = QHBoxLayout(status_row)
        status_row_layout.setContentsMargins(0, 0, 0, 0)
        
        self._lbl_ai_loading = QLabel("Choose an item from your inventory to begin.")
        self._lbl_ai_loading.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._lbl_ai_loading.setObjectName("AssistantStatus")
        self._lbl_ai_loading.setWordWrap(True)
        status_row_layout.addWidget(self._lbl_ai_loading)
        
        self._btn_more_details = QPushButton("More details")
        self._btn_more_details.setObjectName("ApplyFilterButton")
        self._btn_more_details.setFixedWidth(145)
        self._btn_more_details.hide()
        status_row_layout.addWidget(self._btn_more_details)
        
        master_layout.addWidget(status_row)

        self._log_display.setParent(self._frame_ai_input)
        self._log_display.setMinimumHeight(240)
        self._log_display.setMaximumHeight(16777215)
        master_layout.addWidget(self._log_display, 1)
        self._log_display.hide()
        self._log_display.clear()

        master_layout.setAlignment(Qt.AlignTop)

        self._frame_ai_input.show()
        self._btn_execute_ai.setEnabled(True)

        if hasattr(self._controller, "data_manager"):
            self._controller.data_manager.load()
            self.print_current_inventory(self._controller.data_manager.inventory.records)

    def _execute_threaded_ai_analysis(self) -> None:
        # extracts input fields n initiates the non-blocking worker thread
        if not self._controller:
            return

        id_text = self._input_ai_id.text().strip()
        if not id_text or not id_text.isdigit():
            self._show_error_message("Validation Error", "Please provide a valid numeric item ID from the list.")
            return

        idx = int(id_text) - 1
        records = self._controller.data_manager.inventory.records
        
        if not (0 <= idx < len(records)):
            self._show_error_message("Validation Error", f"Item ID '{id_text}' is out of tracking limits.")
            return

        selected_record = records[idx]
        notes_text = self._input_ai_notes.text().strip()
        notes = notes_text if notes_text else "No structural physical defects observed"

        payload = {
            "item": selected_record["food"],
            "category": selected_record["food_category"],
            "use_by_date": selected_record["use-by"],
            "file_storage_condition": selected_record["storage condition"],
            "days_to_expiry": selected_record["days_to_expiry"],
            "waste_risk_level": selected_record["waste_risk_level"],
            "allergen_info": selected_record["allergen info"] or "None",
            "demand_level": selected_record["demand level"].lower(),
            "quantity": selected_record["quantity"],
            "staff_observations": notes
        }

        self._inventory_table.show()
        self._ai_inputs_row.hide()
        self._btn_more_details.hide()
        self._log_display.setParent(self._frame_ai_input)
        self._frame_ai_input.layout().addWidget(self._log_display, 1)
        self._lbl_ai_loading.setText(f"Assessing {selected_record['food']} - Please wait.")
        self._log_display.show()
        self._log_display.clear()
        self._log_display.setMinimumHeight(240)
        self._log_display.setMaximumHeight(16777215)

        self._ai_thread = AIWorker(self._controller.ai_manager, payload)

        self._ai_thread.result_ready.connect(lambda res: self._handle_ai_success(res, selected_record))
        self._ai_thread.error_occurred.connect(self._handle_ai_failure)

        self._ai_thread.finished.connect(self._ai_thread.deleteLater)

        self._ai_thread.start()

    def _handle_ai_success(self, res: dict, selected_record: dict) -> None:
        # Handles updating the main text UI view elements once the thread exits successfully
        brief_html = f"""
        <div style='font-size: 13px; color: #dce3df;'>
            <p style='color: #a7c6b4; font-size: 11px;'>ASSESSMENT SAVED</p>
            <h2 style='color: #f1f4f2; font-size: 20px;'>{escape(selected_record['food'].capitalize())}</h2>
            <p style='color: #b9c6bf;'>Waste risk checked: <b>{escape(str(selected_record['waste_risk_level']))}</b></p>
            <p><b>Suggested recipes</b></p>
            <table width='100%' cellspacing='4' cellpadding='8'>
        """
        
        if res and isinstance(res, dict) and res.get('recipes'):
            for number, recipe in enumerate(res.get('recipes', []), start=1):
                brief_html += (
                    "<tr style='background-color: #30463a;'>"
                    f"<td width='36' style='color: #a7c6b4;'>{number:02d}</td>"
                    f"<td>{escape(recipe.get('name', 'Unknown Recipe'))}</td></tr>"
                )
            self._btn_more_details.setProperty("latest_res", res)
            if not hasattr(self._btn_more_details, '_is_connected'):
                self._btn_more_details.clicked.connect(lambda: self.print_ai_result(self._btn_more_details.property("latest_res"), RECIPES_PATH))
                self._btn_more_details._is_connected = True
            self._btn_more_details.show()
        else:
            brief_html += "<tr><td>No recipe suggestions returned.</td></tr>"

        brief_html += "</table></div>"
        style_surface(self._log_display, "QTextEdit { background: #273a31; border-color: #425b4c; }")
        set_themed_html(self._log_display, brief_html)
        self._controller.data_manager.load()  
        self._lbl_ai_loading.setText("Assessment complete - Suggestions ready to review")

    def _handle_ai_failure(self, err_msg: str) -> None:
        # Handles displaying connection exceptions without crashing the UI loop thread
        QMessageBox.critical(self, "API Connection Failure", f"Assessment failed: {err_msg}")
        self._lbl_ai_loading.setText("Assessment failed. Please try again.")
        self._ai_inputs_row.show()

    def print_ai_result(self, result: dict, recipes_path: str) -> None:
        # renders complete terminal profile recipes across full-screen view spaces
        if hasattr(self, '_btn_more_details'):
            self._btn_more_details.hide()

        self._log_display.setParent(self._display_container)
        self._display_layout.addWidget(self._log_display)
        
        self._log_display.setMaximumHeight(16777215)
        self._log_display.setMinimumHeight(650)

        self._inventory_table.hide()
        self._item_details_view.hide()
        self._log_display.show()
        self._log_display.clear()

        html_content = f"""
        <div style='font-family: Arial, sans-serif; font-size: 13px; color: #f5f5f5; line-height: 1.6;'>
            
            <!-- Master Summary Header Cards -->
            <div style='background-color: #1a1a1a; border: 1px solid #2d2d2d; border-radius: 6px; padding: 15px; margin-bottom: 15px;'>
                <h2 style='color: #ffffff; margin-top: 0px; font-size: 16px; border-bottom: 2px solid #27ae60; padding-bottom: 5px;'>
                    📊 AI ANALYSIS METRICS: {result['stock_item']['name'].upper()}
                </h2>
                <table width='100%' cellpadding='4' style='color: #e0e0e0;'>
                    <tr><td><b>📦 Item Name:</b> {result['stock_item']['name']}</td><td><b>📂 Category:</b> {result['category']}</td></tr>
                    <tr><td><b>📈 Demand Level:</b> {result['demand_level'].capitalize()}</td><td><b>🚨 Spoilage Risk:</b> {result['spoilage_risk'].capitalize()}</td></tr>
                    <tr><td><b>⭐ Suitability Score:</b> <span style='color: #f1c40f; font-weight: bold;'>{result['suitability_score']}/100</span></td><td><b>🎯 Confidence:</b> {result['confidence']:.0%}</td></tr>
                </table>
                <p style='margin-top: 10px; background-color: #252526; padding: 8px; border-radius: 4px; font-style: italic; color: #bdc3c7;'>
                    <b>💡 Assessment Insight:</b> {result['reason']}
                </p>
            </div>
            
            <h3 style='color: #ffffff; font-size: 14px; margin-top: 20px; margin-bottom: 10px;'>🍳 RECOMMENDED DISHES BREAKDOWN</h3>
        """

        for number, recipe in enumerate(result.get('recipes', []), start=1):
            html_content += f"""
            <!-- Individual Recipe Cards Display Panels Grid -->
            <div style='background-color: #1e1e1e; border: 1px solid #3a3a3a; border-left: 5px solid #3498db; border-radius: 6px; padding: 15px; margin-bottom: 15px;'>
                <h4 style='color: #3498db; margin-top: 0px; font-size: 14px; text-transform: uppercase;'>
                    🍴 Recipe {number}: {recipe['name']}
                </h4>
                <p><b>🛒 Ingredients Checklist:</b><br/>
                <span style='color: #bdc3c7;'>{", ".join(recipe.get('ingredients', []))}</span></p>
                
                <p style='margin-bottom: 5px;'><b>📝 Preparation Steps:</b></p>
                <div style='color: #ecf0f1; margin-left: 10px;'>
            """
            
            instructions = recipe.get('instructions', [])
            if isinstance(instructions, list):
                for step_number, instruction in enumerate(instructions, start=1):
                    html_content += f"<div style='margin-bottom: 4px;'><b>{step_number}.</b> {instruction}</div>"
            else:
                html_content += f"<div>{instructions}</div>"

            html_content += """
                </div>
            </div>
            """

        html_content += f"""
            <div style='background-color: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; text-align: center; margin-top: 15px; font-family: monospace;'>
                📁 Data logs committed securely to: {recipes_path}
            </div>
        </div>
        """
        
        set_themed_html(self._log_display,html_content)

    # Option 5: Process Recipes
    def _on_process_recipes_triggered(self) -> None:
        if not self._controller:
            return
        # Update active menu button and hide all other split-screen panels
        self._update_active_navigation_state(self._btn_process_recipes)
        self._search_panel.hide()
        self._edit_scroll_area.hide()
        self._frame_ai_input.hide()
        self._item_details_view.hide()
        self._inventory_table.hide()
        self._recipe_search_panel.hide()

        # reset text display box back onto the main screen container layer
        self._log_display.setParent(self._display_container)
        self._display_layout.addWidget(self._log_display)
        
        # clear any fixed heights so log display takes the maximum full-screen height space
        self._log_display.setMaximumHeight(16777215)
        self._log_display.setMinimumHeight(0)
        
        self._log_display.show()
        self._log_display.clear()
        
        # fire up the backend recipe processor engine matrix
        set_themed_html(self._log_display,
            "<div style=' font-size: 13px; color: #b4c1b9; padding: 10px;'>"
            " <b>Preparing recipe evaluation...</b><br/> Processing recipes... please wait...</div>"
        )
        self.repaint()
        try:
            accepted_rules = self._controller.load_business_rules()

            service = RecipeResultService(
            evaluator=self._controller.logic_evaluator,
            results_store=self._controller.results_store,
            )
            report = service.create_results(accepted_recipes=accepted_rules)
            if isinstance(report, dict) and "error" in report:
                self._show_error_message("Data Processing Issue", report["error"])
                return

            self._controller.data_manager.load()
            folder = self._controller.results_store.get_folder_path()
            r_file = str(folder / "recipe_results.csv")
            rej_file = str(folder / "rejected.txt")

            table_html = """
            <table width='100%' cellpadding='10' cellspacing='0' style='border-collapse: collapse; font-size: 13px; margin-top: 15px; color: #f5f5f5;'>
                <thead>
                    <tr style='background-color: #30383c;'>
                        <th width='20%' style='border: 1px solid #3c464a; text-align: left; padding: 10px; color: #ffffff; font-weight: bold;'>Status</th>
                        <th width='35%' style='border: 1px solid #3c464a; text-align: left; padding: 10px; color: #ffffff; font-weight: bold;'>Recipe Name</th>
                        <th width='45%' style='border: 1px solid #3c464a; text-align: left; padding: 10px; color: #ffffff; font-weight: bold;'>Evaluation Details</th>
                    </tr>
                </thead>
                <tbody>
            """
            row_idx = 0

            if os.path.exists(r_file):
                with open(r_file, mode='r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip CSV header line if present
                    for row in reader:
                        if row:
                            recipe_name = row[0].strip().title()
                            bg_color = "#293034" if row_idx % 2 == 0 else "#242a2d"
                            table_html += f"""
                            <tr style='background-color: {bg_color}; '>
                                <td style='border: 1px solid #3c464a; padding: 8px;'><span style='color: #b0cfbc; font-weight: bold;'>Accepted</span></td>
                                <td style='border: 1px solid #3c464a; padding: 8px;'><b>{recipe_name}</b></td>
                                <td style='border: 1px solid #3c464a; padding: 8px;'><span style='color: #99a3a9;'>Passed business rules verification (Matched template)</span></td>
                            </tr>
                            """
                            row_idx += 1

            if os.path.exists(rej_file):
                with open(rej_file, mode='r', encoding='utf-8') as f:
                    for line in f:
                        clean_line = line.strip()
                        if not clean_line or "Total rejected" in clean_line:
                            continue
                            
                        recipe_name = "Unknown Rejected Recipe"
                        reason = "Ingredients do not match valid accepted criteria"
                        
                        if " | Reason: " in clean_line:
                            parts = clean_line.split(" | Reason: ", 1)
                            raw_name = parts[0].replace("Rejected recipe:", "").replace("Rejected recipe :", "")
                            recipe_name = raw_name.strip().title()
                            reason = parts[1].strip()
                        else:
                            clean_line = clean_line.replace("Rejected recipe:", "").strip()
                            recipe_name = clean_line.title()

                        bg_color = "#293034" if row_idx % 2 == 0 else "#242a2d"
                        table_html += f"""
                        <tr style='background-color: {bg_color}; '>
                            <td style='border: 1px solid #3c464a; padding: 8px;'><span style='color: #dcaaa9; font-weight: bold;'>Rejected</span></td>
                            <td style='border: 1px solid #3c464a; padding: 8px;'><b>{recipe_name}</b></td>
                            <td style='border: 1px solid #3c464a; padding: 8px;'><span style='color: #cfbc97;'>{reason}</span></td>
                        </tr>
                        """
                        row_idx += 1

            if row_idx == 0:
                table_html += """
                <tr style=''>
                    <td colspan='3' style='border: 1px solid #3c464a; text-align: center; padding: 15px; color: #bdc3c7;'>
                        No validation data records found. Run an evaluation via 'Ask AI Assistant' first!
                    </td>
                </tr>
                """

            table_html += "</tbody></table>"

            full_html = f"""
            <div style='font-size: 13px; color: #f5f5f5; line-height: 1.6;'>
                <div style='background-color: #273a31; color: #ffffff; padding: 12px; font-weight: bold; border-radius: 6px; text-align: center; font-size: 16px; margin-bottom: 15px;'>
                    Recipe processing results
                </div>
                
                {table_html}
                
                <div style='margin-top: 25px; background-color: #242a2d; border: 1px solid #3c464a; border-radius: 6px; padding: 15px;'>
                    <h3 style='color: #ffffff; margin-top: 0px; margin-bottom: 12px; font-size: 16px; border-bottom: 2px solid #b0cfbc; padding-bottom: 6px;'>
                        Evaluation summary
                    </h3>
                    <p style='margin: 6px 0; font-size: 13px;'><span style='color: #b0cfbc; font-weight: bold;'>Accepted Recipes :</span> <b>{report.get("accepted", 0)}</b></p>
                    <p style='margin: 6px 0; font-size: 13px;'><span style='color: #dcaaa9; font-weight: bold;'>Rejected Recipes :</span> <b>{report.get("rejected", 0)}</b></p>
                    
                    <div style='margin-top: 14px; padding-top: 10px; border-top: 1px dashed #3a3a3a; font-size: 12px; color: #bdc3c7;'>
                        <p style='margin: 0 0 6px 0; color: #ffffff; font-weight: bold;'>Saved files</p>
                        <p style='margin: 4px 0; color: #b0cfbc; word-break: break-all;'><b>Accepted:</b> {r_file}</p>
                        <p style='margin: 4px 0; color: #dcaaa9; word-break: break-all;'><b>Rejections:</b> {rej_file}</p>
                    </div>
                </div>
            </div>
            """
            set_themed_html(self._log_display, full_html)
            
            # show a desktop completion alert box
            self._show_success_message(
                "Processor Update", 
                f"Validation finished!\nAccepted: {report.get('accepted', 0)} | Rejected: {report.get('rejected', 0)}"
            )           
        except Exception as e:
            self._show_error_message("System Error", f"Could not complete validation pass: {str(e)}")

    # Option 6: Fetches all stored recipe logs  
    def _on_recipes_view_triggered(self):
        if not self._controller:
            return        
        # Update active menu button and hide all other split-screen panels
        self._update_active_navigation_state(self._btn_view_recipes)
        self._search_panel.hide()
        self._edit_scroll_area.hide()
        self._frame_ai_input.hide()
        self._item_details_view.hide()
        self._inventory_table.hide()
        self._recipe_search_panel.hide()

        self._log_display.hide()

        try:
            self._controller.data_manager.load()
            saved_recipes = self._controller.data_manager.recipes.records
            # Reuse the themed, naturally sized cards without changing stored recipes.
            self._recipe_cards.set_recipes(saved_recipes)
            self._recipe_cards.show()

        except Exception as e:
            self._show_error_message("System Error", f"Could not load recipe history: {str(e)}")

    # Option 7: Search Recipes
    def _on_search_recipes_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_search_recipes)
        self._search_panel.hide()
        self._edit_scroll_area.hide()
        self._frame_ai_input.hide()
        self._log_display.hide()
        self._recipe_cards.hide()
        
        self._inventory_table.show()
        self._item_details_view.hide()

        self._inventory_table.setMaximumHeight(340)
        self._inventory_table.setMinimumHeight(180)

        self._item_details_view.setMinimumHeight(450)
        self._item_details_view.setMaximumHeight(16777215)

        self._display_layout.setStretchFactor(self._inventory_table, 1)
        self._display_layout.setStretchFactor(self._item_details_view, 5)
        
        if self._controller:
            self._controller.data_manager.load()
            recipes = self._controller.data_manager.recipes.records
            self._recipe_search_panel.setVisible(bool(recipes))
            if recipes:
                self.print_recipes_table(recipes)
            else:
                self._show_recipe_search_empty_state(
                    "No saved recipes yet",
                    "Process recipes or use the AI assistant to start building your recipe library.",
                )

    def _execute_embedded_recipe_search(self) -> None:
        if not self._controller:
            return

        # Extract values cleanly directly from interface boxes
        ingredient_text = self._input_recipe_ingredient.text().strip()
        id_text = self._input_recipe_id.text().strip()
        
        ingredients_list = [i.strip() for i in ingredient_text.split(",") if i.strip()] if ingredient_text else None
        id_filter = int(id_text) if id_text and id_text.isdigit() else None

        results = self._controller.data_manager.recipes.search(ingredient=ingredients_list, item_id=id_filter)
        
        if results:
            record_ids = self._controller._get_record_ids(self._controller.data_manager.recipes.records, results)
            self.print_recipes_table(results, record_ids)
            if len(results) == 1:
                self._load_recipe_profile_by_row(0)
            else:
                self._item_details_view.hide()
        else:
            self._show_recipe_search_empty_state(
                "No matching recipes",
                "Try a different ingredient or recipe ID, or clear the search fields.",
            )

    def _show_recipe_search_empty_state(self, title: str, message: str) -> None:
        self._inventory_table.hide()
        self._item_details_view.hide()
        self._recipe_cards.set_recipes(
            [],
            empty_title=title,
            empty_message=message,
        )
        self._recipe_cards.show()

    def print_recipes_table(self, recipe_list: list, ids: list = None) -> bool:
        self._log_display.hide()
        self._item_details_view.hide()
        self._recipe_cards.hide()
        self._inventory_table.show()
        self._inventory_table.setRowCount(0)
        if not recipe_list: return False

        self._inventory_table.setColumnCount(1)
        self._inventory_table.setHorizontalHeaderLabels(["Recipe Name"])
        self._inventory_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        self._inventory_table.setRowCount(len(recipe_list))
        for row, record in enumerate(recipe_list):
            item_num = str(ids[row]) if ids else str(row + 1)
            self._inventory_table.setVerticalHeaderItem(row, QTableWidgetItem(item_num))
            
            name_item = QTableWidgetItem(record.get('name', 'Unknown Recipe'))
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._inventory_table.setItem(row, 0, name_item)
        return True

    def _load_recipe_profile_by_row(self, row_idx: int) -> None:
        if not self._controller or not self._recipe_search_panel.isVisible(): 
            return
        header_item = self._inventory_table.verticalHeaderItem(row_idx)
        if not header_item: 
            return
        try:
            db_id = int(header_item.text()) - 1
        except ValueError: 
            return
            
        records = self._controller.data_manager.recipes.records
        if 0 <= db_id < len(records):
            target = records[db_id]
            self._item_details_view.show()
            self._item_details_view.clear()
            
            recipe_name = target.get('name', 'Unknown Recipe').upper()
            ingredients = target.get('ingredients', 'None listed')
            instructions = target.get('instructions', 'No execution steps provided.')

            formatted_steps = ""
            if "Step " in instructions or "1. " in instructions:
                formatted_steps = f"<div style='color: #ecf0f1; white-space: pre-wrap;'>{instructions}</div>"
            else:
                steps = [step.strip() for step in instructions.split(". ") if step.strip()]
                formatted_steps = "".join(
                    f"<p>{index}. {escape(step if step.endswith('.') else step + '.')}</p>"
                    for index, step in enumerate(steps, start=1)
                )
            set_themed_html(self._item_details_view, f"""
                <p style='color: #a7cbb6;'>RECIPE {db_id + 1:02d}</p>
                <h2 style='color: #f0f3f1; font-size: 20px;'>{escape(recipe_name)}</h2>
                <p style='color: #c2d2c9;'><b>Ingredients</b></p>
                <p style='color: #b9c6bf;'>{escape(ingredients)}</p>
                <p style='color: #c2d2c9;'><b>Preparation steps</b></p>
                <div style='color: #dce4df;'>{formatted_steps}</div>
            """)

    # Option 8: Exit Application
    def _execute_graceful_exit(self) -> None:
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Exit")
        
        msg_box.setStyleSheet(
            "QMessageBox { border-left: 5px solid #27ae60; } "
            "QLabel { min-width: 440px; color: " + self._dialog_text_color() + "; font-size: 13px; }"
        )
        msg_box.setText("Are you sure you want to exit and close the management dashboard?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        if msg_box.exec() == QMessageBox.Yes:
            if self._controller and hasattr(self._controller, "data_manager"):
                self._controller.data_manager.save_all()
            self.close()
    
