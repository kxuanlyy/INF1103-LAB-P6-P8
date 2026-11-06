import sys
import abc
from io_manager.user_interface import UserInterface
from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QFrame
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

        # Right-side Display Viewport Pane
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
        
        self._main_layout.addWidget(self._sidebar_widget)
        self._main_layout.addWidget(self._log_display)
        
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
        """       
        self.setStyleSheet(dark_stylesheet)

    def _connect_signals(self) -> None:
        self._btn_view_inv.clicked.connect(self._on_inventory_view_triggered)
        self._btn_view_recipes.clicked.connect(self._on_recipes_view_triggered)
        self._btn_exit.clicked.connect(self.close)

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
        self._log_display.clear()
        if not extracted_items:
            self._log_display.append("The inventory list is currently empty.")
            return False
            
        self._log_display.append(f"{'Ingredient Name':<30} | {'Qty':<10} | {'Expiry Date'}")
        self._log_display.append("-" * 60)
        for record in extracted_items:
            qty = "" if record.get('quantity') is None else record['quantity']
            self._log_display.append(f"{record.get('food', 'Unknown'):<30} | {str(qty):<10} | {record.get('use-by', 'N/A')}")
        return True

    def print_recipes(self, recipe_list: list, ids: list = None) -> bool:
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
        self._log_display.clear()
        quantity = "Unknown" if match.get('quantity') is None else match['quantity']
        self._log_display.append(f"=== FOOD CARD ID: [{choice_num}] ===")
        self._log_display.append(f"Name: {match.get('food')}")
        self._log_display.append(f"Category: {match.get('food_category')}")
        self._log_display.append(f"Qty: {quantity}")
        self._log_display.append(f"Expiry: {match.get('use-by')}")

    def print_recipe_card(self, choice_num: int, match: dict) -> None:
        self._log_display.clear()
        self._log_display.append(f"=== RECIPE CARD ID: [{choice_num}] ===")
        self._log_display.append(f"Name: {match.get('name')}")
        self._log_display.append(f"Ingredients: {match.get('ingredients')}")
        self._log_display.append(f"Instructions: {match.get('instructions')}")

    def print_ai_result(self, result: dict, recipes_path: str) -> None:
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
        self._log_display.append("\n🍳 RECIPE VALIDATION PROCESSOR ACTIVE 🍳\n")

    def print_recipe_processor_step(self, accept_flag: bool, name: str, reason: str = None) -> None:
        status = "✔ ACCEPTED" if accept_flag else f"✖ REJECTED -> {reason}"
        self._log_display.append(f"  {status}: {name}")

    def print_recipe_processor_summary(self, accept_len: int, reject_len: int, r_file: str, rej_file: str) -> None:
        self._log_display.append("\n=== SUMMARY REPORT ===")
        self._log_display.append(f"Accepted Recipes: {accept_len}")
        self._log_display.append(f"Rejected Recipes: {reject_len}")
        self._log_display.append(f"Saved: {r_file} | Rejections logged: {rej_file}")
