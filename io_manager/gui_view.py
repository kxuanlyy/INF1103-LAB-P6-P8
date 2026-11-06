import sys
import abc
from io_manager.user_interface import UserInterface
from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox
)

class PySideABCMeta(type(QObject), abc.ABCMeta):
    pass

class GuiView(QMainWindow, UserInterface, metaclass=PySideABCMeta):
    
    def __init__(self, controller=None) -> None:
        super().__init__()
        self._controller = controller

        # Root Window Canvas Structure
        self._central_widget = QWidget()
        self._main_layout = QHBoxLayout(self._central_widget)
        
        # Sidebar Control Column
        self._sidebar_widget = QFrame()
        self._sidebar_layout = QVBoxLayout(self._sidebar_widget)
        self._status_label = QLabel("FoodRescue Operations")
        
        # Action Buttons for all Menu Options
        self._btn_view_inv = QPushButton("📋 View Inventory")
        self._btn_search_inv = QPushButton("🔍 Search Inventory")
        self._btn_edit_inv = QPushButton("✏ Edit Items Data")
        self._btn_ask_ai = QPushButton("🤖 Ask AI Assistant")
        self._btn_process_recipes = QPushButton("🍳 Process Recipes")
        self._btn_view_recipes = QPushButton("📖 View Recipes")
        self._btn_search_recipes = QPushButton("🏷 Search Recipes")
        self._btn_exit = QPushButton("🚪 Exit Application")

        # Right-side Display Component Area (Dynamic Layout)
        self._display_container = QWidget()
        self._display_layout = QVBoxLayout(self._display_container)
        
        # Dynamic swappable components
        self._inventory_table = QTableWidget()
        self._log_display = QTextEdit()

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
        self._display_layout.addWidget(self._log_display)

        # Hide the grid by default until data populates
        self._log_display.setReadOnly(True)
        self._inventory_table.hide()  

        # Configure Table properties
        self._inventory_table.setColumnCount(4)
        self._inventory_table.setHorizontalHeaderLabels(["Item ID", "Ingredient Name", "Quantity", "Expiry Date"])
        self._inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._inventory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._inventory_table.setAlternatingRowColors(True)

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
            QLabel { color: #ffffff; font-size: 14px; font-weight: bold; padding-bottom: 10px; border-bottom: 1px solid #2d2d2d; }
            QPushButton { background-color: #2a2a2a; color: #e0e0e0; border: 1px solid #3a3a3a; border-radius: 6px; padding: 10px 12px; text-align: left; }
            QPushButton:hover { background-color: #353535; border: 1px solid #4a4a4a; color: #ffffff; }
            QPushButton:pressed { background-color: #27ae60; border: 1px solid #219653; color: #ffffff; }
            QTextEdit { background-color: #1e1e1e; color: #f5f5f5; border: 1px solid #2d2d2d; border-radius: 8px; padding: 12px; font-family: 'Consolas', monospace; }
            QComboBox, QAbstractItemView { background-color: #2a2a2a;  color: #ffffff; selection-background-color: #27ae60;  selection-color: #ffffff;  border: 1px solid #3a3a3a; }
            QTableWidget { background-color: #1e1e1e;  color: #e0e0e0; gridline-color: #2d2d2d; border: 1px solid #2d2d2d;  border-radius: 8px; font-size: 13px; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:alternate { background-color: #252525; }
            QTableWidget::item:selected { background-color: #27ae60; color: #ffffff; }
            QHeaderView::section { background-color: #2a2a2a; color: #ffffff; padding: 6px; border: 1px solid #2d2d2d; font-weight: bold; font-size: 13px; }
        
        """       
        self.setStyleSheet(dark_stylesheet)

    def _connect_signals(self) -> None:
        self._btn_view_inv.clicked.connect(self._on_inventory_view_triggered)
        self._btn_search_inv.clicked.connect(self._on_search_inventory_triggered)
        self._btn_edit_inv.clicked.connect(self._on_edit_inventory_triggered)
        self._btn_ask_ai.clicked.connect(self._on_ask_ai_triggered)
        self._btn_process_recipes.clicked.connect(self._on_process_recipes_triggered)
        self._btn_view_recipes.clicked.connect(self._on_recipes_view_triggered)
        self._btn_search_recipes.clicked.connect(self._on_search_recipes_triggered)
        self._btn_exit.clicked.connect(self.close)

    def _on_search_inventory_triggered(self) -> None:
        # captures search strings directly inside a graphical popup dialog box
        if not self._controller:
            return
            
        search_term, ok = QInputDialog.getText(
            self, "Search Inventory", "Enter Food Name (or leave blank to skip):"
        )
        if not ok:
            # user cancel
            return

        id_term, ok_id = QInputDialog.getText(
            self, "Search Inventory", "Enter exact Item ID number (or leave blank to skip):"
        )
        if not ok_id:
            return

        # sanitize inputs to match expected datatypes
        food_filter = search_term.strip() if search_term.strip() else None
        
        id_filter = None
        if id_term.strip() and id_term.strip().isdigit():
            id_filter = int(id_term.strip())

        # trigger data query dynamically
        results = self._controller.data_manager.inventory.search(food=food_filter, item_id=id_filter)
        
        if results:
            # look up matching record positions inside global database cache array
            record_ids = self._controller._get_record_ids(self._controller.data_manager.inventory.records, results)
            self.print_current_inventory(results, record_ids)
            self._log_display.append(f"\n[Search Success]: Found {len(results)} matching item(s).")
        else:
            QMessageBox.information(self, "Search Results", "No inventory items matched that name or ID.")

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
        if self._controller:
            self._log_display.append("\n[System]: Starting Recipe Search... Please look at your Terminal window for inputs.")
            self._controller.handle_recipe_search()

    def _on_recipes_view_triggered(self) -> None:
        if self._controller and hasattr(self._controller, "data_manager"):
            self._controller.data_manager.load()
            records = self._controller.data_manager.recipes.records
            self.print_recipes(records)

    def set_controller(self, controller) -> None:
       # safely mutates internal controller reference
        self._controller = controller

    def _on_inventory_view_triggered(self) -> None:
        # internal callback to bridge data safely controller
        if self._controller and hasattr(self._controller, "data_manager"):
            # Pull records safely from the data framework layer
            records = self._controller.data_manager.inventory.records
            self.print_current_inventory(records)

    def display_main_menu(self) -> None:
        self.show()
    
    def display_edit_menu(self) -> None: pass
    def display_inventory_search_menu(self) -> None: pass
    def display_recipe_search_menu(self) -> None: pass

    def print_current_inventory(self, extracted_items: list, ids: list = None) -> bool:
        self._log_display.hide()
        self._inventory_table.show()
        self._inventory_table.setRowCount(0)
        
        if not extracted_items:
            return False
            
        self._inventory_table.setRowCount(len(extracted_items))
        for row, record in enumerate(extracted_items):
            # Resolve unique index positions safely 
            item_id = str(ids[row]) if ids else f"INV-{row+1:04d}"
            qty = "" if record.get('quantity') is None else str(record['quantity'])
            
            self._inventory_table.setItem(row, 0, QTableWidgetItem(item_id))
            self._inventory_table.setItem(row, 1, QTableWidgetItem(record.get('food', 'Unknown')))
            self._inventory_table.setItem(row, 2, QTableWidgetItem(qty))
            self._inventory_table.setItem(row, 3, QTableWidgetItem(record.get('use-by', 'N/A')))
        return True

    def print_recipes(self, recipe_list: list, ids: list = None) -> bool:
        self._inventory_table.hide()
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
