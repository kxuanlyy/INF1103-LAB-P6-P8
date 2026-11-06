
class IngredientMatcher:
    """Compare recipe ingredients with a standard ingredient template."""

    def __init__(self, minimum_match_ratio=0.6):
        # Minimum fraction of template ingredients that must match.
        self.minimum_match_ratio = minimum_match_ratio

    @staticmethod
    def normalize_items(items):
        # Trim whitespace and lowercase items for consistent comparison.
        return {item.strip().lower() for item in items}

    def matches(self, expected_ingredients, actual_ingredients):
        # Normalize both lists before comparing them.
        expected = self.normalize_items(expected_ingredients)
        actual = self.normalize_items(actual_ingredients)

        # Empty ingredient lists cannot meet the matching requirement.
        if not expected or not actual:
            return False

        matched_count = 0
        for expected_item in expected:
            expected_words = set(expected_item.split())

            # One shared word is enough to count this ingredient as a match.
            if any(
                expected_words.intersection(actual_item.split())
                for actual_item in actual
            ):
                matched_count += 1

        # Compare the matching fraction with the configured threshold.
        return matched_count / len(expected) >= self.minimum_match_ratio
