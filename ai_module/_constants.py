from pathlib import Path


LEVELS = ("low", "medium", "high")
TEXT_FIELDS = ("item_id", "category", "reason")
LEVEL_FIELDS = ("demand_level", "expiry_urgency", "spoilage_risk")
SCORE_LIMITS = {"suitability_score": 100, "confidence": 1}
FLAG_FIELDS = ("allergen_uncertain", "storage_uncertain")
MAX_RECIPES = 5
DEFAULT_MODEL = "openai/gpt-oss-120b"
REQUEST_TIMEOUT = 30.0
API_RETRIES = 1
RESPONSE_ATTEMPTS = 2
INVALID_INPUT_ERROR = "Invalid assessment input. Check the stock records, inventory IDs, and date."
INVALID_RESPONSE_ERROR = "AI returned an invalid response. Staff review and reassessment required."
SERVICE_ERROR = "AI service unavailable. Check configuration or connection and retry."
RECIPES_PATH = Path(__file__).resolve().parent.parent / "data_manager" / "recipes.json"
SAVE_ERROR = "Could not save recipes.json. Check folder permissions and retry."

RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "ingredient_ids": {
            "type": "array", "minItems": 1, "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "additional_ingredients": {
            "type": "array", "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "how_to_make": {
            "type": "array", "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
    },
    "required": ["name", "ingredient_ids", "how_to_make"],
    "additionalProperties": False,
}
ANALYSIS_PROPERTIES = {
    **{field: {"type": "string", "minLength": 1} for field in TEXT_FIELDS},
    **{field: {"type": "string", "enum": list(LEVELS)} for field in LEVEL_FIELDS},
    **{field: {"type": "number", "minimum": 0, "maximum": maximum}
       for field, maximum in SCORE_LIMITS.items()},
    **{field: {"type": "boolean"} for field in FLAG_FIELDS},
    "recipe_suggestions": {
        "type": "array", "maxItems": MAX_RECIPES, "items": RECIPE_SCHEMA,
    },
}
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": ANALYSIS_PROPERTIES,
    "required": list(ANALYSIS_PROPERTIES),
    "additionalProperties": False,
}
