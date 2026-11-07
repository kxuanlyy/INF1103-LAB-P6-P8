import sys
import abc
from datetime import datetime
from io_manager.user_interface import UserInterface
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLineEdit, QLabel, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox, 
    QComboBox, QGridLayout, QScrollArea
)

class PySideABCMeta(type(QObject), abc.ABCMeta):
    pass

class GuiView(QMainWindow, UserInterface, metaclass=PySideABCMeta):
    
    def __init__(self, controller=None) -> None:
        super().__init__()
        self._controller = controller

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
        self._btn_exit = QPushButton("🚪 Exit Application")

        # Right Display Component Area (Dynamic Layout)
        self._display_container = QWidget()
        self._display_layout = QVBoxLayout(self._display_container)
    
        self._inventory_table = QTableWidget()
        self._item_details_view = QTextEdit()
        self._log_display = QTextEdit()

        # Search Bar Tool
        self._search_panel = QFrame()
        self._search_layout = QHBoxLayout(self._search_panel)
        self._input_food = QLineEdit()
        self._input_id = QLineEdit()
        self._btn_submit_search = QPushButton("Apply Filter")
        self._btn_submit_search.setObjectName("ApplyFilterButton")

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
        
        self._layout_add_inputs = QHBoxLayout()
        self._add_name = QLineEdit(); self._add_name.setPlaceholderText("Ingredient Name")
        self._add_qty = QLineEdit(); self._add_qty.setPlaceholderText("Stock Qty")
        self._add_date = QLineEdit(); self._add_date.setPlaceholderText("Use-By (DD/MM/YYYY)")
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
        self._edit_date = QLineEdit(); self._edit_date.setPlaceholderText("Use-By (DD/MM/YYYY)")
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


        # Configure button properties to latch their pressed visual states
        self._btn_view_inv.setCheckable(True)
        self._btn_search_inv.setCheckable(True)
        self._btn_edit_inv.setCheckable(True)
        self._btn_ask_ai.setCheckable(True)
        self._btn_process_recipes.setCheckable(True)
        self._btn_view_recipes.setCheckable(True)
        self._btn_search_recipes.setCheckable(True)
        
        # Group them into a list for easy state clearing loops later
        self._nav_buttons = [
            self._btn_view_inv, self._btn_search_inv, self._btn_edit_inv,
            self._btn_ask_ai, self._btn_process_recipes, self._btn_view_recipes,
            self._btn_search_recipes
        ]

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("FoodRescue Enterprise Management Dashboard")
        self.resize(1120, 860)
        self.setCentralWidget(self._central_widget)
        
        self._main_layout.setContentsMargins(15, 15, 15, 15)
        self._main_layout.setSpacing(15)
        
        self._sidebar_widget.setFrameShape(QFrame.StyledPanel)
        self._sidebar_widget.setFixedWidth(240)
        self._sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self._sidebar_layout.setSpacing(8)
        
        self._sidebar_layout.addWidget(self._status_label)
        self._sidebar_layout.addWidget(self._btn_view_inv)
        self._sidebar_layout.addWidget(self._btn_search_inv)
        self._sidebar_layout.addWidget(self._btn_edit_inv)
        self._sidebar_layout.addWidget(self._btn_ask_ai)
        self._sidebar_layout.addWidget(self._btn_process_recipes)
        self._sidebar_layout.addWidget(self._btn_view_recipes)
        self._sidebar_layout.addWidget(self._btn_search_recipes)
        self._sidebar_layout.addStretch()
        self._sidebar_layout.addWidget(self._btn_exit)
        

        self._display_layout.addWidget(self._inventory_table)
        self._display_layout.addWidget(self._item_details_view)
        self._display_layout.addWidget(self._log_display)

        self._edit_panel_layout.setContentsMargins(0, 0, 12, 10)
        self._edit_panel_layout.setSpacing(12)

        self._edit_scroll_area = QScrollArea()
        self._edit_scroll_area.setWidgetResizable(True)
        self._edit_scroll_area.setWidget(self._edit_panel)
        self._edit_scroll_area.setFrameShape(QFrame.NoFrame)
        self._display_layout.addWidget(self._edit_scroll_area)

        self._edit_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._edit_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._edit_scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #121212 !important; 
            }
            QScrollBar:vertical {
                background-color: #1e1e1e; /* Matches your QFrame card panel background color */
                border-left: 1px solid #2d2d2d; /* Subtle divider separator line */
                width: 10px;
                margin: 0px;
            }            
            QScrollBar::handle:vertical {
                background-color: #2a2a2a; /* Matches the default button layout color shades */
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #27ae60; /* Matches your active theme green accent hue color */
                border: 1px solid #219653;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

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

        QWidget().setLayout(self._edit_form_layout) 
        self._edit_form_layout = QVBoxLayout(self._edit_form_widget)
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
        self._search_panel.setFixedHeight(60)
        self._search_layout.setContentsMargins(10, 4, 10, 4)
        self._search_layout.setSpacing(10)      
        # Lock text boxes to single-row heights
        self._input_food.setPlaceholderText("Filter by Ingredient Name... (or press Enter)")
        self._input_id.setPlaceholderText("Filter by precise ID... (or press Enter)")
        self._btn_submit_search.setFixedWidth(100)

        # Assemble embedded component toolbar elements
        self._search_layout.addWidget(self._input_food)
        self._search_layout.addWidget(self._input_id)
        self._search_layout.addWidget(self._btn_submit_search)
        # Add the widgets to your master right-side viewport panel layout stack
        self._display_layout.insertWidget(0, self._search_panel)
        self._search_panel.hide()

        # Assemble Main Layout
        self._main_layout.addWidget(self._sidebar_widget)
        self._main_layout.addWidget(self._display_container)
      
        self._log_display.setReadOnly(True)
        self._apply_theme_styles()
        self._connect_signals()

    def _apply_theme_styles(self) -> None:
        dark_stylesheet = """
            /* primary window canvas n system frames */
            QMainWindow { 
                background-color: #121212; 
            }
            QFrame { 
                background-color: #1e1e1e; 
                border: 1px solid #2d2d2d; 
                border-radius: 8px; 
                padding: 12px;
                margin-bottom: 4px;
            }
            QFrame#AddFrame, QFrame#EditFrame, QFrame#DeleteFrame {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                padding: 16px;
                margin-top: 8px;
                border-radius: 10px;
            }
            #SearchPanelFrame, QFrame[frameShape="0"] { 
                background-color: transparent; 
                border: none; 
                padding: 2px; 
            }
            QScrollArea, QScrollArea > QWidget > QWidget {
                background-color: #121212 !important;
                border: none;
            }
            QScrollArea QWidget {
                background-color: transparent;
            }
            QFrame#AddFrame, QFrame#EditFrame, QFrame#DeleteFrame {
                background-color: #1a1a1a !important;
                border: 1px solid #333333;
                border-radius: 10px;
                padding: 16px;
                margin-top: 8px;
            }

            /* text interaction views n form labels */
            QLabel {  
                background: transparent; 
                border: none; 
                color: #ffffff; 
                font-size: 13px; 
                font-weight: bold; 
                padding: 0px !important;
                margin: 0px !important;
            }
            QTextEdit { 
                background-color: #1e1e1e; 
                color: #f5f5f5; 
                border: 1px solid #2d2d2d; 
                border-radius: 8px; 
                padding: 6px 12px; 
                font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 12px;
                line-height: 14px;
            }

            /* input n selection widget*/
            QLineEdit { 
                background-color: #252526; 
                color: #ffffff; 
                border: 1px solid #3e3e42; 
                border-radius: 6px; 
                padding: 6px 10px; 
                font-size: 13px; 
                selection-background-color: #27ae60;  
            }
            QLineEdit:hover { 
                border: 1px solid #555555; 
            }
            QLineEdit:focus { 
                border: 1px solid #27ae60; 
                background-color: #1e1e1e; 
            }
            QComboBox { 
                background-color: #252526; 
                color: #ffffff; 
                border: 1px solid #3e3e42; 
                border-radius: 6px; 
                padding: 5px 10px; 
                font-size: 13px;
                min-width: 130px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 4px;
            }
            QAbstractItemView { 
                background-color: #2a2a2a;  
                color: #ffffff; 
                border: 1px solid #3a3a3a;
                selection-background-color: #27ae60;  
                selection-color: #ffffff;  
            }

            /* nav action buttons*/
            QPushButton { 
                background-color: #2a2a2a; 
                color: #e0e0e0; 
                border: 1px solid #3a3a3a; 
                border-radius: 6px; 
                padding: 10px 12px; 
                text-align: left; 
                font-size: 13px;
            }
            QPushButton:hover { 
                background-color: #353535; 
                border: 1px solid #4a4a4a; 
                color: #ffffff; 
            }
            QPushButton:pressed, QPushButton:checked { 
                background-color: #2ecc71; 
                border: 1px solid #219653; 
                color: #ffffff; 
            }
            QPushButton#ApplyFilterButton { 
                background-color: #27ae60 !important; 
                color: #ffffff !important; 
                border: 1px solid #219653 !important; 
                border-radius: 6px; 
                font-weight: bold; 
                text-align: center; 
                padding: 6px 16px; 
                min-width: 80px;
            }
            QPushButton#ExecuteDeleteButton {
                background-color: #c0392b !important;
                color: #ffffff !important;
                border: 1px solid #a93226 !important;
                border-radius: 6px;
                font-weight: bold;
                text-align: center !important;
                padding: 6px 16px;
            }
            QPushButton#ExecuteDeleteButton:hover {
                background-color: #e74c3c !important;
                border: 1px solid #c0392b !important;
            }
            QPushButton#ExecuteDeleteButton:pressed {
                background-color: #922b21 !important;
            }

            /* database table */
            QTableWidget { 
                background-color: #1e1e1e;  
                color: #e0e0e0; 
                gridline-color: #2d2d2d; 
                border: 1px solid #2d2d2d;  
                border-radius: 8px; 
                font-size: 13px; 
            }
            QTableWidget::item { 
                padding: 6px; 
            }
            QTableWidget::item:alternate { 
                background-color: #252525; 
            }
            QTableWidget::item:selected { 
                background-color: #27ae60; 
                color: #ffffff; 
            }
            QHeaderView::section { 
                background-color: #2a2a2a; 
                color: #ffffff; 
                padding: 6px; 
                border: 1px solid #2d2d2d; 
                font-weight: bold; 
                font-size: 13px; 
            }

            /* form execution anchors */
            QPushButton#ApplyFilterButton { 
                background-color: #27ae60 !important; 
                color: #ffffff !important; 
                border: 1px solid #219653 !important; 
                border-radius: 6px; 
                font-weight: bold; 
                text-align: center; 
                padding: 6px 16px; 
                min-width: 80px;
            }
            QPushButton#ApplyFilterButton:hover { 
                background-color: #2ecc71 !important; 
                border: 1px solid #27ae60 !important; 
            }
            QPushButton#ApplyFilterButton:pressed { 
                background-color: #1e8449 !important; 
            }

            /* dialog noti (QMessageBox) */
            QMessageBox {
                background-color: #1e1e1e;
                border: 1px solid #2d2d2d;
            }
            QMessageBox QLabel {
                color: #ffffff !important;
                font-size: 13px;
                font-weight: normal;
                min-width: 320px;
                max-width: 500px;
                qproperty-wordWrap: true;
            }
            QMessageBox QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 5px 18px;
                text-align: center;
                min-width: 65px;
            }
            QMessageBox QPushButton:hover {
                background-color: #353535;
                color: #ffffff;
            }


        """       
        self.setStyleSheet(dark_stylesheet)

    def _connect_signals(self) -> None:
        self._btn_view_inv.clicked.connect(self._on_inventory_view_triggered)
        self._btn_search_inv.clicked.connect(self._on_search_inventory_triggered)
        self._input_food.returnPressed.connect(self._execute_embedded_search)
        self._input_id.returnPressed.connect(self._execute_embedded_search)
        self._btn_submit_search.clicked.connect(self._execute_embedded_search)
        self._btn_edit_inv.clicked.connect(self._on_edit_inventory_triggered)
        self._btn_execute_add.clicked.connect(self._execute_gui_add)
        self._btn_ask_ai.clicked.connect(self._on_ask_ai_triggered)
        self._btn_process_recipes.clicked.connect(self._on_process_recipes_triggered)
        self._btn_view_recipes.clicked.connect(self._on_recipes_view_triggered)
        self._btn_search_recipes.clicked.connect(self._on_search_recipes_triggered)
        self._btn_submit_search.clicked.connect(self._execute_embedded_search)
        self._btn_exit.clicked.connect(self.close)
        self._inventory_table.itemClicked.connect(self._on_table_row_clicked)
        self._inventory_table.verticalHeader().sectionClicked.connect(self._on_header_section_clicked)
        self._input_edit_id.returnPressed.connect(self._on_edit_id_modified)
        self._btn_execute_update.clicked.connect(self._execute_gui_update)
        self._btn_execute_delete.clicked.connect(self._execute_gui_delete)

    def _show_success_message(self, title: str, text: str) -> None:
        # displays a custom themed alert dialog box for success messages
        msg = QMessageBox(self)
        msg.setWindowTitle(title)        
        msg.setIcon(QMessageBox.Icon.NoIcon)

        content_label = QLabel()
        content_label.setWordWrap(True)

        formatted_rich_text = (
            f"<div style='vertical-align: middle; display: flex; align-items: center; word-break: break-all;'>"
            f"  <span style='color: #27ae60; font-size: 24px; font-weight: bold; font-family: Arial;'>✔</span>"
            f"  <span style='color: #ffffff; font-size: 13px; font-weight: normal; margin-left: 14px;'>{text}</span>"
            f"</div>"
        )

        content_label.setText(formatted_rich_text)       
        msg.layout().addWidget(content_label, 0, 1)
        # Apply an inline green border highlight style just to this popup's icon layout box
        msg.setStyleSheet("QMessageBox { border-left: 5px solid #27ae60; }")
        msg.exec()

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
            f"  <span style='color: #ffffff; font-size: 13px; font-weight: normal; margin-left: 14px;'>{text}</span>"
            f"</div>"
        )
        content_label.setText(formatted_rich_text)
        msg.layout().addWidget(content_label, 0, 1)
        msg.setStyleSheet("QMessageBox { border-left: 5px solid #e74c3c; }")
        msg.exec()

    def _update_active_navigation_state(self, active_button: QPushButton) -> None:
        # unchecks all navigation shortcuts n locks the green background on the active menu choice
        for btn in self._nav_buttons:
            btn.setChecked(btn == active_button)

    def set_controller(self, controller) -> None:
       # safely mutates internal controller reference
        self._controller = controller
    
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
            self._item_details_view.clear()
            self._item_details_view.hide()
            self._inventory_table.setMaximumHeight(16777215)
            self._inventory_table.setMinimumHeight(0)
            self._inventory_table.show()
            records = self._controller.data_manager.inventory.records
            self.print_current_inventory(records)

    # Option 2: Search Inventory
    def _on_search_inventory_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_search_inv)
        # displays the embedded search text bars row layout inside the dashboard
        self._log_display.hide()
        self._item_details_view.hide()
        self._edit_scroll_area.hide()
        self._inventory_table.show()
        self._search_panel.show()

        self._inventory_table.setMaximumHeight(340)
        
        if self._controller:
            self.print_current_inventory(self._controller.data_manager.inventory.records)

    def _execute_embedded_search(self) -> None:
        # extracts data strings inline from GUI text bars n applies active queries
        if not self._controller:
            return

        # xtract values cleanly directly from your desktop interface boxes
        food_text = self._input_food.text().strip()
        id_text = self._input_id.text().strip()

        # sanitize parameter types to pass cleanly to database search modules
        food_filter = food_text if food_text else None
        id_filter = int(id_text) if id_text and id_text.isdigit() else None

        results = self._controller.data_manager.inventory.search(food=food_filter, item_id=id_filter)
        
        if results:
            record_ids = self._controller._get_record_ids(self._controller.data_manager.inventory.records, results)
            self.print_current_inventory(results, record_ids)
            
            if len(results) == 1:
                    self._load_food_profile_by_row(0)
            else:
                self._item_details_view.hide()
        else:
            self._inventory_table.setRowCount(0)
            self._item_details_view.hide()

    def _on_table_row_clicked(self, item) -> None:
        if item:
            self._load_food_profile_by_row(item.row())

    def _on_header_section_clicked(self, row_idx: int) -> None:
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

            # Replicates your terminal string formatting layout perfectly
            self._item_details_view.append("============================================================")
            self._item_details_view.append(f"                        FOOD ID: [{db_id + 1}]")
            self._item_details_view.append("============================================================")
            self._item_details_view.append(f"Item Name:        {target.get('food', 'Unknown')}")
            self._item_details_view.append(f"Category:         {target.get('food_category', 'General')}")
            self._item_details_view.append(f"Stock Quantity:   {target.get('quantity', '0')}")
            self._item_details_view.append(f"Use-By Date:      {target.get('use-by', 'N/A')}")
            self._item_details_view.append(f"Days to Expiry:   {expiry_str}")
            self._item_details_view.append(f"Storage Type:     {storage}")
            self._item_details_view.append(f"Waste Risk Level: {target.get('waste_risk_level', 'Low')}")
            self._item_details_view.append(f"Demand Level:     {target.get('demand level', 'Normal')}")
            self._item_details_view.append(f"Allergen Info:    {allergen}")
            self._item_details_view.append("============================================================")

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

    # Option 3:Edit Inventory Items
    def _on_edit_inventory_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_edit_inv)
        self._search_panel.hide()
        self._item_details_view.hide()
        self._log_display.hide()
        
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
            self._edit_date.setText(target.get('use-by', ''))
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
        date_str = self._edit_date.text().strip()

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
            try:
                self._controller.data_manager.inventory.delete(idx)
                self._show_success_message("Success", f"Success: Removed '{removed_name}' from the inventory.")
                self._input_delete_id.clear()
                self.print_current_inventory(self._controller.data_manager.inventory.records)
            except Exception as e:
                QMessageBox.critical(self, "System Failure", f"Deletion failed: {e}")
        else:
            self._show_error_message("Validation Error", "Item ID out of active inventory limits.")

    # NOT DONE YET :/
    def _on_ask_ai_triggered(self) -> None:
        # selects items via GUI popups and forwards execution context directly to the controller engine
        if not self._controller:
            return

        records = self._controller.data_manager.inventory.records
        if not records:
            QMessageBox.warning(self, "AI Assistant Blocked", "No inventory data available to process.")
            return

        # select item via graphical dropdown popup checklist
        items_list = [f"[{i+1}] {r['food']} (Qty: {r['quantity']})" for i, r in enumerate(records)]
        selected_item_str, ok = QInputDialog.getItem(
            self, "Ask AI Assistant", "Select an inventory item to assess:", items_list, 0, False
        )
        if not ok or not selected_item_str:
            return

        # extract selected array index to identify the exact chosen record row entry
        choice_idx = items_list.index(selected_item_str)
        selected_record = records[choice_idx]

        # prompt for staff note text observations
        staff_notes, ok_notes = QInputDialog.getText(
            self, "Quality Observations", f"Enter structural notes for {selected_record['food']} (or click OK to skip):"
        )
        if not ok_notes:
            return
        
        notes = staff_notes.strip() if staff_notes.strip() else "No structural physical defects observed"

        # build data dictionary package structures
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

        self._log_display.clear()
        self._log_display.append("🤖 Contacting AI Model Pipeline Core... Please wait.")
        sys.modules['PySide6.QtWidgets'].QApplication.processEvents()

        # execute backend model analysis pipelines
        last_result, last_error = self._controller.ai_manager.suggest_recipes(payload)
        if last_error:
            QMessageBox.critical(self, "API Connection Failure", f"Assessment failed: {last_error}")
        else:
            from ai_module.ai_manager import RECIPES_PATH
            self.print_ai_result(last_result, RECIPES_PATH)

    def _on_process_recipes_triggered(self) -> None:
        if self._controller:
            self._controller.handle_recipe_processor()

    def _on_search_recipes_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_search_recipes)
        if self._controller:
            self._log_display.append("\n[System]: Starting Recipe Search... Please look at your Terminal window for inputs.")
            self._controller.handle_recipe_search()

    def _on_recipes_view_triggered(self) -> None:
        if self._controller and hasattr(self._controller, "data_manager"):
            self._controller.data_manager.load()
            records = self._controller.data_manager.recipes.records
            self.print_recipes(records)

    def display_edit_menu(self) -> None: pass
    def display_inventory_search_menu(self) -> None: pass
    def display_recipe_search_menu(self) -> None: pass


    def print_recipes(self, recipe_list: list, ids: list = None) -> bool:
        self._inventory_table.hide()
        self._item_details_view.hide()
        self._log_display.show()
        self._log_display.clear()
        if not recipe_list:
            self._log_display.append("There are no recipes saved yet.")
            return False
            
        for x, recipe in enumerate(recipe_list, start=1):
            self._log_display.append(f"\n[{x}] {recipe.get('name', 'Unknown Recipe')}")
            self._log_display.append("-" * 40)
            self._log_display.append(f"Ingredients: {recipe.get('ingredients', '')}")
            self._log_display.append(f"Instructions: {recipe.get('instructions', '')}\n")
        return True

    def print_item_card(self, choice_num: int, match: dict) -> None:
        self._inventory_table.hide()
        self._log_display.show()
        self._log_display.clear()
        quantity = "Unknown" if match.get('quantity') is None else match['quantity']
        self._log_display.append(f"=== FOOD CARD ID: [{choice_num}] ===")
        self._log_display.append(f"Name: {match.get('food')}")
        self._log_display.append(f"Category: {match.get('food_category')}")
        self._log_display.append(f"Qty: {quantity}")
        self._log_display.append(f"Expiry: {match.get('use-by')}")

    def print_recipe_card(self, choice_num: int, match: dict) -> None:
        self._inventory_table.hide()
        self._log_display.show()
        self._log_display.clear()
        self._log_display.append(f"=== RECIPE CARD ID: [{choice_num}] ===")
        self._log_display.append(f"Name: {match.get('name')}")
        self._log_display.append(f"Ingredients: {match.get('ingredients')}")
        self._log_display.append(f"Instructions: {match.get('instructions')}")

    def print_ai_result(self, result: dict, recipes_path: str) -> None:
        self._inventory_table.hide()
        self._item_details_view.hide()
        self._log_display.show()
        self._log_display.clear()
        self._log_display.append(f"=== AI ASSESSMENT FOR: {result['stock_item']['name'].upper()} ===")
        self._log_display.append(f"Reason: {result.get('reason')}")
        self._log_display.append(f"Suitability Score: {result.get('suitability_score')}/100")
        self._log_display.append(f"Confidence: {result.get('confidence'):.0%}")
        
        for number, recipe in enumerate(result.get('recipes', []), start=1):
            self._log_display.append(f"\n  [Recipe {number}] {recipe.get('name').upper()}")
            self._log_display.append(f"  Ingredients: {', '.join(recipe.get('ingredients', []))}")
        self._log_display.append(f"\nRecipes saved to: {recipes_path}")

    def print_recipe_processor_header(self) -> None:
        self._inventory_table.hide()
        self._item_details_view.hide()
        self._log_display.show()
        self._log_display.clear()
        self._log_display.append("\n🍳 RECIPE VALIDATION PROCESSOR ACTIVE 🍳\n")

    def print_recipe_processor_step(self, accept_flag: bool, name: str, reason: str = None) -> None:
        status = "✔ ACCEPTED" if accept_flag else f"✖ REJECTED -> {reason}"
        self._log_display.append(f"  {status}: {name}")

    def print_recipe_processor_summary(self, accept_len: int, reject_len: int, r_file: str, rej_file: str) -> None:
        self._log_display.append("\n=== SUMMARY REPORT ===")
        self._log_display.append(f"Accepted Recipes: {accept_len}")
        self._log_display.append(f"Rejected Recipes: {reject_len}")
        self._log_display.append(f"Saved: {r_file} | Rejections logged: {rej_file}")
