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

