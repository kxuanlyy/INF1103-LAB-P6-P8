import json
import os
import tempfile
from pathlib import Path

from ai_module._constants import RECIPES_PATH


class RecipeStore:
    # Save the recipe list atomically, keeping file handling out of AI assessment.

    def __init__(self, path=None):
        self._path = RECIPES_PATH if path is None else Path(path)

    @property
    def path(self):
        return self._path

    def save(self, recipes):
        # Atomically save a JSON list of recipe names, ingredients, and instructions.
        content = json.dumps(recipes, indent=2, ensure_ascii=False, allow_nan=False)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                             dir=self._path.parent, prefix=".recipes-",
                                             suffix=".tmp", delete=False) as file:
                temporary_path = Path(file.name)
                file.write(content + "\n")
            os.replace(temporary_path, self._path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

