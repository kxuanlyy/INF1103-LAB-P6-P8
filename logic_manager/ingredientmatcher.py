import re
from collections import Counter


class IngredientMatcher:
    # Put only unambiguous preparation descriptions here.
   
    PREPARATION_WORDS = {
        "chopped",
        "cubed",
        "diced",
        "finely",
        "julienned",
        "minced",
        "peeled",
        "roughly",
        "shredded",
        "sliced",
        "thinly",
        }
    

    # Units are removed only when they follow a leading quantity.
    UNIT_WORDS = {
        "cup", "cups",
        "gram", "grams", "g",
        "kilogram", "kilograms", "kg",
        "milliliter", "milliliters", "ml",
        "liter", "liters", "l",
        "ounce", "ounces", "oz",
        "pound", "pounds", "lb", "lbs",
        "teaspoon", "teaspoons", "tsp",
        "tablespoon", "tablespoons", "tbsp",
        "clove", "cloves",
        "can", "cans",
        "package", "packages",
        "piece", "pieces",
    }

    # Explicit aliases prevent fuzzy or shared-word matches.
    PHRASE_ALIASES = {
        "capsicum": "bell pepper",
        "scallion": "green onion",
        "spring onion": "green onion",
        "garlic clove": "garlic",
        "garlic cloves": "garlic",
    }

    # Only these plural forms are changed. Avoids unsafe general stemming.
    WORD_ALIASES = {
        "apples": "apple",
        "beans": "bean",
        "carrots": "carrot",
        "eggs": "egg",
        "mushrooms": "mushroom",
        "onions": "onion",
        "peppers": "pepper",
        "potatoes": "potato",
        "tomatoes": "tomato",
    }

    def __init__(self, minimum_match_ratio=0.6):
        if not 0 <= minimum_match_ratio <= 1:
            raise ValueError("minimum_match_ratio must be between 0 and 1.")

        self.minimum_match_ratio = minimum_match_ratio

    def compare(self, expected_ingredients, actual_ingredients):
        expected = self._normalize_items(expected_ingredients)
        actual = self._normalize_items(actual_ingredients)

        expected_counts = Counter(
            item["normalized"] for item in expected
        )
        actual_counts = Counter(
            item["normalized"] for item in actual
        )

        # Match occurrences one-to-one, so duplicates count correctly.
        remaining_actual = actual_counts.copy()
        matched = []
        unmatched = []

        for item in expected:
            normalized = item["normalized"]

            if remaining_actual[normalized] > 0:
                matched.append(item["original"])
                remaining_actual[normalized] -= 1
            else:
                unmatched.append(item["original"])

        match_ratio = len(matched) / len(expected) if expected else 0.0

        # Ingredient names must match completely; no shared-word matching.
        matches = (
            bool(expected)
            and bool(actual)
            and match_ratio >= self.minimum_match_ratio
        )

        return {
            "matches": matches,
            "matched": matched,
            "unmatched": unmatched,
            "match_ratio": match_ratio,
            "required_ratio": self.minimum_match_ratio,
        }

    def matches(self, expected_ingredients, actual_ingredients):
        return self.compare(
            expected_ingredients,
            actual_ingredients,
        )["matches"]

    def _normalize_items(self, items):
        if isinstance(items, str):
            items = [
                item.strip()
                for item in items.split(",")
                if item.strip()
            ]

        normalized_items = []

        for item in items or []:
            if not isinstance(item, str) or not item.strip():
                continue

            normalized = self._normalize_ingredient(item)

            if normalized:
                normalized_items.append({
                    "original": item.strip(),
                    "normalized": normalized,
                })

        return normalized_items

    @classmethod
    def _normalize_ingredient(cls, ingredient):
        text = ingredient.casefold().strip()

        # Remove a quantity only at the beginning, e.g. 2, 1/2, or 0.5.
        quantity_pattern = (
            r"^\s*\d+(?:\s*/\s*\d+)?(?:\.\d+)?\s*"
        )
        text = re.sub(quantity_pattern, "", text)

        # Punctuation becomes spaces, so "bell-pepper" becomes "bell pepper".
        text = re.sub(r"[^\w\s]", " ", text)
        words = text.split()

        # Remove one recognized unit after the quantity.
        if words and words[0] in cls.UNIT_WORDS:
            words.pop(0)

        # Remove known preparation terms, wherever they appear.
        words = [
            word for word in words
            if word not in cls.PREPARATION_WORDS
        ]

        # Apply explicit single-word aliases.
        words = [
            cls.WORD_ALIASES.get(word, word)
            for word in words
        ]

        phrase = " ".join(words)

        # Apply aliases to the complete ingredient phrase.
        return cls.PHRASE_ALIASES.get(phrase, phrase)

    @classmethod
    def normalize_items(cls, items):
        matcher = cls()
        return {
            item["normalized"]
            for item in matcher._normalize_items(items)
        }