from PySide6.QtCore import QThread, Signal


# Run AI requests off the UI thread and report results through Qt signals.
class AIWorker(QThread):
    # Custom signals to safely send results or errors back to the main UI thread
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, ai_manager, payload: dict) -> None:
        super().__init__()
        self.ai_manager = ai_manager
        self.payload = payload

    def run(self) -> None:
        # Executes the blocking API network request on a separate thread
        try:
            res, err = self.ai_manager.suggest_recipes(self.payload)
            if err:
                self.error_occurred.emit(err)
            else:
                self.result_ready.emit(res)
        except Exception as e:
            self.error_occurred.emit(str(e))
