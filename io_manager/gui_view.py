import sys
import abc
from io_manager.user_interface import UserInterface
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLineEdit, QLabel, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox
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
        self.resize(1024, 680)
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

        # Hide the grid by default until data populates
        self._log_display.setReadOnly(True)
        self._item_details_view.setReadOnly(True)
        self._inventory_table.hide()  
        self._item_details_view.hide()

        # Setup Inventory View Columns
        self._inventory_table.setColumnCount(3)
        self._inventory_table.setHorizontalHeaderLabels(["Ingredient Name", "Quantity", "Expiry Date"])
        self._inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._inventory_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._inventory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._inventory_table.setAlternatingRowColors(True)
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
            QMainWindow { background-color: #121212; }
            QFrame { background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 8px; }
            QLabel {  background: transparent; border: none; color: #ffffff; font-size: 14px; font-weight: bold; padding-bottom: 10px; border-bottom: 10px; }
            QPushButton { background-color: #2a2a2a; color: #e0e0e0; border: 1px solid #3a3a3a; border-radius: 6px; padding: 10px 12px; text-align: left; }
            QPushButton:hover { background-color: #353535; border: 1px solid #4a4a4a; color: #ffffff; }
            QPushButton:pressed, QPushButton:checked { background-color: #2ecc71  ; border: 1px solid #219653; color: #ffffff; }
            QTextEdit { background-color: #1e1e1e; color: #f5f5f5; border: 1px solid #2d2d2d; border-radius: 8px; padding: 12px; font-family: 'Consolas', monospace; }
            QComboBox, QAbstractItemView { background-color: #2a2a2a;  color: #ffffff; selection-background-color: #27ae60;  selection-color: #ffffff;  border: 1px solid #3a3a3a; }
            QTableWidget { background-color: #1e1e1e;  color: #e0e0e0; gridline-color: #2d2d2d; border: 1px solid #2d2d2d;  border-radius: 8px; font-size: 13px; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:alternate { background-color: #252525; }
            QTableWidget::item:selected { background-color: #27ae60; color: #ffffff; }
            QHeaderView::section { background-color: #2a2a2a; color: #ffffff; padding: 6px; border: 1px solid #2d2d2d; font-weight: bold; font-size: 13px; }
            QLineEdit { background-color: #252526; color: #ffffff; border: 1px solid #3e3e42; border-radius: 6px; padding: 6px 10px; font-size: 13px; selection-background-color: #27ae60;  }
            QLineEdit:hover { border: 1px solid #555555; }
            QLineEdit:focus { border: 1px solid #27ae60; background-color: #1e1e1e; }
            #SearchPanelFrame, QFrame[frameShape="0"] { background-color: transparent; border: none; padding: 2px; }
            QPushButton#ApplyFilterButton { background-color: #27ae60 !important; color: #ffffff !important; border: 1px solid #219653 !important; border-radius: 6px; font-weight: bold; text-align: center; padding: 6px 12px; }
            QPushButton#ApplyFilterButton:hover { background-color: #2ecc71 !important; border: 1px solid #27ae60 !important; }
            QPushButton#ApplyFilterButton:pressed { background-color: #1e8449 !important; }

        """       
        self.setStyleSheet(dark_stylesheet)

    def _connect_signals(self) -> None:
        self._btn_view_inv.clicked.connect(self._on_inventory_view_triggered)
        self._btn_search_inv.clicked.connect(self._on_search_inventory_triggered)
        self._input_food.returnPressed.connect(self._execute_embedded_search)
        self._input_id.returnPressed.connect(self._execute_embedded_search)
        self._btn_submit_search.clicked.connect(self._execute_embedded_search)
        self._btn_edit_inv.clicked.connect(self._on_edit_inventory_triggered)
        self._btn_ask_ai.clicked.connect(self._on_ask_ai_triggered)
        self._btn_process_recipes.clicked.connect(self._on_process_recipes_triggered)
        self._btn_view_recipes.clicked.connect(self._on_recipes_view_triggered)
        self._btn_search_recipes.clicked.connect(self._on_search_recipes_triggered)
        self._btn_submit_search.clicked.connect(self._execute_embedded_search)
        self._btn_exit.clicked.connect(self.close)
        self._inventory_table.itemClicked.connect(self._on_table_row_clicked)
        self._inventory_table.verticalHeader().sectionClicked.connect(self._on_header_section_clicked)

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
            self._item_details_view.clear()
            self._item_details_view.hide()
            self._inventory_table.setMaximumHeight(16777215)
            records = self._controller.data_manager.inventory.records
            self.print_current_inventory(records)

    # Option 2: Search Inventory
    def _on_search_inventory_triggered(self) -> None:
        self._update_active_navigation_state(self._btn_search_inv)
        # displays the embedded search text bars row layout inside the dashboard
        self._log_display.hide()
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
        self._inventory_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


        self._inventory_table.setRowCount(len(extracted_items))
        for row, record in enumerate(extracted_items):
            # Resolve unique index positions safely 
            item_num = str(ids[row]) if ids else str(row + 1)
            qty = "" if record.get('quantity') is None else str(record['quantity'])
            
            self._inventory_table.setVerticalHeaderItem(row, QTableWidgetItem(item_num))
            self._inventory_table.setItem(row, 0, QTableWidgetItem(record.get('food', 'Unknown')))
            self._inventory_table.setItem(row, 1, QTableWidgetItem(qty))
            self._inventory_table.setItem(row, 2, QTableWidgetItem(record.get('use-by', 'N/A')))
        return True



    # NOT DONE YET :/
    def _on_edit_inventory_triggered(self) -> None:
        if self._controller:
            self._log_display.append("\n[System]: Starting Inventory Editor... Please look at your Terminal window for inputs.")
            self._controller.handle_edit_menu()

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
