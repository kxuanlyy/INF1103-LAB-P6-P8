from io_manager.user_interface import UserInterface
from io_manager.colors import Colors
from io_manager.console_view import ConsoleView
from io_manager.input_validator import InputValidator
from io_manager.menu_controller import MenuController
from ai_module.ai_manager import RECIPES_PATH, suggest_recipes
<<<<<<< HEAD
=======

>>>>>>> df9f0b6ae62fa85bd77f9b5b354870b79e198d2f


def main(today=None, client=None):
    import data_manager.data_manager as dm 
    from logic_manager.recipeevaluator import RecipeEvaluator 
    from ai_module.ai_manager import AIManager, GroqProvider

    active_view = ConsoleView()
    active_data_mgr = dm.DataManager()         
    active_results_store = dm.RecipeResultsStore()
    provider = GroqProvider(client) if client is not None else None
    ai_manager = AIManager(provider=provider)
    logic_evaluator = RecipeEvaluator()
    
    controller = MenuController(
        view=active_view, 
        data_manager=active_data_mgr, 
        results_store=active_results_store,
        ai_manager=ai_manager,
        logic_evaluator=logic_evaluator
    )
    controller.run(today=today, client=client)

    
if __name__ == "__main__":
    main()