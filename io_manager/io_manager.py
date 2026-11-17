from data_manager.recipe_results_store import RecipeResultsStore
from io_manager.menu_controller import MenuController


def main(today=None, client=None):
    import data_manager.data_manager as dm 
    from logic_manager.recipeevaluator import RecipeEvaluator 
    from ai_module.ai_manager import AIManager, GroqProvider
    active_data_mgr = dm.DataManager()         
    active_results_store = RecipeResultsStore()
    provider = GroqProvider(client) if client is not None else None
    ai_manager = AIManager(provider=provider)
    logic_evaluator = RecipeEvaluator()

    from PySide6.QtWidgets import QApplication
    from io_manager.gui_view import GuiView

    # The graphical interface is the application's default and only launcher.
    app = QApplication.instance() or QApplication([])

    active_view = GuiView()
    controller = MenuController(
        view=active_view,
        data_manager=active_data_mgr,
        results_store=active_results_store,
        ai_manager=ai_manager,
        logic_evaluator=logic_evaluator,
    )

    active_view.set_controller(controller)
    active_view.display_main_menu()
    return app.exec()

    
if __name__ == "__main__":
    main()
