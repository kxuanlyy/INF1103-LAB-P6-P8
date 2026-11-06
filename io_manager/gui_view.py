import sys
from io_manager.user_interface import UserInterface
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QTextEdit, QLabel
)

class GuiView(QMainWindow, UserInterface):
    def __init__(self, controller=None) -> None:
        super().__init__()
        self._controller  = controller

        self._central_widget = QWidget()
        self._layout = QVBoxLayout(self._central_widget)
        self._status_label = QLabel("Welcome to FoodRescue! Click an action below.")
        self._view_btn = QPushButton("1. View Current Inventory Stock")
        self._log_display = QTextEdit()

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("FoodRescue Enterprise Management Dashboard")
        self.resize(800, 600)
        self.setCentralWidget(self._central_widget)
        
        self._log_display.setReadOnly(True)
        
        self._layout.addWidget(self._status_label)
        self._layout.addWidget(self._view_btn)
        self._layout.addWidget(self._log_display)
        
        # safely handles signal connection internally
        self._view_btn.clicked.connect(self._on_inventory_view_triggered)
        
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

