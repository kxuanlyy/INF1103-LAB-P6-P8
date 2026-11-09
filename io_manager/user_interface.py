from abc import ABC, abstractmethod

class UserInterface(ABC):
    @abstractmethod
    def display_main_menu(self) -> None: pass

    @abstractmethod
    def display_edit_menu(self) -> None: pass

    @abstractmethod
    def display_inventory_search_menu(self) -> None: pass

    @abstractmethod
    def display_recipe_search_menu(self) -> None: pass

    @abstractmethod
    def print_current_inventory(self, extracted_items: list, ids: list = None) -> bool: pass

    @abstractmethod
    def print_recipes(self, recipe_list: list, ids: list = None) -> bool: pass
