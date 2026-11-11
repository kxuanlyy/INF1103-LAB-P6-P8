"""Read-only recipe cards; data loading and recipe operations stay in the controller."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from io_manager.main_window_style import RECIPE_CARDS_QSS, style_surface


def _text_label(text, object_name):
    label = QLabel(str(text))
    label.setObjectName(object_name)
    # Recipe content is text, including any literal <, > or & characters.
    label.setTextFormat(Qt.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
    label.setMinimumWidth(0)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return label


class RecipeCardsView(QScrollArea):
    """One naturally sized card per recipe, with one scroll bar for the library."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RecipeLibrary")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        style_surface(self, RECIPE_CARDS_QSS)
        self.set_recipes([])

    def set_recipes(self, recipes):
        contents = QWidget()
        contents.setObjectName("RecipeCardContents")
        layout = QVBoxLayout(contents)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(18)
        for number, recipe in enumerate(recipes, start=1):
            card = QFrame()
            card.setObjectName("RecipeCard")
            card.setProperty("tone", ("sage", "slate", "plum")[(number - 1) % 3])
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 22, 24, 24)
            card_layout.setSpacing(10)
            card_layout.addWidget(_text_label(f"RECIPE {number:02d}", "RecipeNumber"))
            card_layout.addWidget(_text_label(recipe.get("name", "Unknown Recipe"), "RecipeTitle"))
            divider = QFrame()
            divider.setObjectName("RecipeDivider")
            divider.setFixedHeight(1)
            card_layout.addWidget(divider)
            card_layout.addSpacing(2)
            card_layout.addWidget(_text_label("Ingredients", "RecipeSection"))
            card_layout.addWidget(_text_label(recipe.get("ingredients", "None listed"), "RecipeIngredients"))
            card_layout.addSpacing(6)
            card_layout.addWidget(_text_label("Preparation steps", "RecipeSection"))

            instructions = recipe.get("instructions", "No execution steps provided.")
            # Keep the existing library's numbering convention without editing records.
            if "Step " in instructions or "1. " in instructions:
                card_layout.addWidget(_text_label(instructions, "RecipeInstructions"))
            else:
                steps = [step.strip() for step in instructions.split(". ") if step.strip()]
                for index, step in enumerate(steps, start=1):
                    ending = "" if step.endswith(".") else "."
                    card_layout.addWidget(_text_label(f"{index}. {step}{ending}", "RecipeInstructions"))
            layout.addWidget(card)

        if not recipes:
            empty = QFrame()
            empty.setObjectName("RecipeCard")
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(28, 28, 28, 28)
            empty_layout.setSpacing(12)
            empty_layout.addWidget(_text_label("No saved recipes yet", "RecipeTitle"))
            empty_layout.addWidget(_text_label(
                "Run an assessment with the AI assistant or process recipes to build your library.",
                "RecipeIngredients",
            ))
            layout.addWidget(empty)
        layout.addStretch()
        # QScrollArea owns and deletes the previous contents on replacement.
        self.setWidget(contents)
        self.verticalScrollBar().setValue(0)
