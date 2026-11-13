
class IngredientMatcher:
    

    def __init__(self, minimum_match_ratio=0.6): # compare ingredients or recipes in recipe.json to recipes in accepted_recipe.json.
        # Minimum fraction of template ingredients that must match - 60%, subject to change.
        self.minimum_match_ratio = minimum_match_ratio

    @staticmethod
    def normalize_items(items):
        # Trim whitespace and lowercase items for consistent comparison.
        return {item.strip().lower() for item in items}


    def compare(self, expected_ingredients, actual_ingredients):
        expected = self.normalize_items(expected_ingredients)
        actual = self.normalize_items(actual_ingredients)

        matched = []
        unmatched = []

        for expected_item in sorted(expected):
            expected_words = set(expected_item.split())

            if any(
                expected_words.intersection(actual_item.split())
                for actual_item in actual
            ):
                matched.append(expected_item)
            else:
                unmatched.append(expected_item)

        ratio = len(matched) / len(expected) if expected else 0.0

        return {
            "matches": bool(expected and actual)
            and ratio >= self.minimum_match_ratio,
            "matched": matched,
            "unmatched": unmatched,
            "match_ratio": ratio,
            "required_ratio": self.minimum_match_ratio,
        }

    def matches(self, expected_ingredients, actual_ingredients):
        return self.compare(expected_ingredients, actual_ingredients)["matches"]