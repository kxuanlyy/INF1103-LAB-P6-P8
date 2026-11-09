# Build prompts, call Groq, and validate AI output; no business decisions.
# SOLID design notes:
# SRP: prompt building, validation, API access and saving have separate classes.
# OCP: another AIProvider subclass can be used without changing AIManager.
# LSP: GroqProvider and the offline test provider honour the same completion and
# cleanup contract; AIManager uses them without checking their concrete types.

import json
import os
import runpy
from datetime import date, datetime
from pathlib import Path

from ai_module._constants import (
    LEVELS, TEXT_FIELDS, LEVEL_FIELDS, SCORE_LIMITS, FLAG_FIELDS, MAX_RECIPES,
    DEFAULT_MODEL, REQUEST_TIMEOUT, API_RETRIES, RESPONSE_ATTEMPTS,
    INVALID_INPUT_ERROR, INVALID_RESPONSE_ERROR, SERVICE_ERROR,
    RECIPES_PATH, SAVE_ERROR, RECIPE_SCHEMA, ANALYSIS_PROPERTIES, ANALYSIS_SCHEMA,
)
from ai_module.ai_provider import AIProvider
from ai_module.groq_provider import GroqProvider
from ai_module.assessment_prompt import AssessmentPrompt
from ai_module.assessment_validator import AssessmentValidator
from ai_module.recipe_store import RecipeStore


class AIManager:
    # Coordinate assessment and recipes; final business decisions stay in Logic Manager.
    # The injected provider is shared (aggregation); prompt, validator and store are
    # created and owned here (composition). All providers use the same interface.

    def __init__(self, provider=None):
        self._provider = provider
        self._prompt = AssessmentPrompt()
        self._validator = AssessmentValidator()
        self._recipe_store = RecipeStore()

    def prepare_io_inputs(self, ai_payload, records):
        # Convert I/O records without modifying the payload or source inventory.
        #
        # The CSV has no IDs or units. IDs identify rows within this assessment;
        # units and verification statuses remain explicitly unknown.
        #
        if not isinstance(records, list) or not records:
            raise ValueError("Inventory must be a nonempty list.")
        selected = dict(ai_payload)
        if "file_storage_condition" in selected:
            selected["storage_condition"] = selected.pop("file_storage_condition")
        fields = ("item", "category", "use_by_date", "storage_condition",
                  "days_to_expiry", "waste_risk_level", "allergen_info",
                  "demand_level", "quantity")
        matches = []
        inventory = []
        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                raise ValueError("Stock item must be an object.")
            if all(record[field] == selected[field] for field in fields):
                matches.append(index - 1)
            use_by = record["use_by_date"]
            try:
                use_by = date.fromisoformat(use_by).isoformat()
            except ValueError:
                # The I/O manager and CSV use day/month/year, including ambiguous dates.
                use_by = datetime.strptime(use_by, "%d/%m/%Y").date().isoformat()
            quantity = record["quantity"]
            if isinstance(quantity, str):
                quantity = float(quantity)
            self._validator.validate_text(record["demand_level"], "demand_level")
            inventory.append({
                "id": f"inventory-{index:04d}",
                "name": record["item"],
                "category": record["category"],
                "quantity": quantity,
                "unit": "unknown",
                "use_by": use_by,
                "days_to_expiry": record["days_to_expiry"],
                "waste_risk_level": record["waste_risk_level"],
                "demand_level": record["demand_level"].strip().lower(),
                "storage_condition": record["storage_condition"],
                "storage_status": "unknown",
                "allergens": record["allergen_info"],
                "allergen_status": "unknown",
            })
        if len(matches) != 1:
            raise ValueError("Selected item must match exactly one inventory row.")
        item = inventory[matches[0]]
        if "staff_observations" in selected:
            item["staff_observations"] = selected["staff_observations"]
        return item, inventory

    def _assess_with_provider(self, provider, messages, item_id, inventory_ids, require_steps=False):
        # Retry invalid model output once; API failures remain the SDK's responsibility.
        for attempt in range(RESPONSE_ATTEMPTS):
            try:
                completion = provider.complete(messages)
            except Exception as error:
                # Provider exceptions may include credentials or stock data.
                if getattr(error, "status_code", None) == 413:
                    return None, "AI request is too large. Reduce the inventory payload and retry."
                if getattr(error, "status_code", None) == 429:
                    return None, "AI rate limit reached. Wait before retrying or check your Groq limits."
                return None, SERVICE_ERROR
            try:
                analysis = self._validator.parse_response(self._validator.extract_response(completion))
                return self._validator.validate_analysis(analysis, item_id, inventory_ids, require_steps), None
            except ValueError:
                if attempt + 1 < RESPONSE_ATTEMPTS:
                    messages = messages + [{"role": "user", "content": (
                        "The previous response was incomplete or invalid. Return one complete "
                        "JSON object matching the schema, with the exact target ID and only "
                        "supplied inventory IDs. Do not include commentary or Markdown."
                    )}]
        return None, INVALID_RESPONSE_ERROR

    def analyse_item(self, item, inventory, today, require_steps=False):
        # Input -> prompt/API/validation -> (assessment, error), with no terminal I/O.
        #
        # An injected provider belongs to the caller. Internally created clients are closed.
        # No assessment is fabricated when input, configuration, or model output fails.
        # Accepts either the stock contract or an io_manager payload and its raw records.
        #
        try:
            if isinstance(item, dict) and "item" in item and "id" not in item:
                item, inventory = self.prepare_io_inputs(item, inventory)
            inventory_ids = self._validator.validate_inputs(item, inventory, today)
            messages = self._prompt.build_messages(item, inventory, today)
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            return None, INVALID_INPUT_ERROR

        provider = self._provider
        try:
            if provider is None:
                client, error = create_client()
                if error:
                    return None, error
                provider = GroqProvider(client, owns_client=True)
            return self._assess_with_provider(provider, messages, item["id"],
                                               inventory_ids, require_steps)
        except Exception:
            # API errors may contain request data; keep credentials and payloads off screen.
            return None, SERVICE_ERROR
        finally:
            if self._provider is None and provider is not None:
                try:
                    provider.close()
                except Exception:
                    pass  # A cleanup failure must not discard the assessment or its error.

    def suggest_recipes(self, final_ai_ready_dict, today=None):
        # Save recipes.json and return (logic_ready_dict, error) without opening a menu.
        #
        # Only the item in final_ai_ready_dict is sent to the AI. Unselected inventory
        # records are not included, and recipe ingredient IDs must reference this item.
        #
        # On success, the dictionary contains validated AI assessment fields and recipes:
        # [{"name": str, "ingredients": [str], "instructions": [str]}].
        # Ingredient names include the selected stock and any additional ingredients
        # needed to prepare the popular dish; additional ingredients are not stock records.
        # It also contains assessment_date (ISO text), stock_item (the normalized target),
        # and inventory_by_id (ID -> normalized stock record) so logic_manager can check
        # the selected stock. Quantities and days_to_expiry are numeric; the CSV's
        # original expiry estimate is retained as reported_days_to_expiry. IDs are local
        # to this result, so pass the whole dictionary to logic_manager.
        #
        # Only the recipes list is saved to recipes.json in the project folder, replacing
        # the previous successful result. Assessment metadata stays in the returned
        # dictionary for logic_manager. An empty recipe list is a valid assessment.
        # API or validation failures leave the previous file untouched. Errors return
        # (None, error), never a partial result. Final business decisions belong to
        # logic_manager. The caller's input dictionaries are not changed.
        #
        today = date.today() if today is None else today
        try:
            if not isinstance(final_ai_ready_dict, dict) or type(today) is not date:
                raise ValueError("Invalid payload or assessment date.")
            record = dict(final_ai_ready_dict)
            if "file_storage_condition" in record:
                record["storage_condition"] = record.pop("file_storage_condition")
            item, stock = self.prepare_io_inputs(final_ai_ready_dict, [record])
            for record in stock:
                record["reported_days_to_expiry"] = record["days_to_expiry"]
                record["days_to_expiry"] = (date.fromisoformat(record["use_by"]) - today).days
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            return None, INVALID_INPUT_ERROR

        assessment, error = self.analyse_item(item, stock, today, require_steps=True)
        if error:
            return None, error
        inventory_by_id = {record["id"]: record for record in stock}
        logic_ready_dict = {
            **{key: value for key, value in assessment.items() if key != "recipe_suggestions"},
            "recipes": [{
                "name": recipe["name"],
                "ingredients": [inventory_by_id[ingredient_id]["name"]
                                for ingredient_id in recipe["ingredient_ids"]]
                               + recipe.get("additional_ingredients", []),
                "instructions": recipe["how_to_make"],
            } for recipe in assessment["recipe_suggestions"]],
            "assessment_date": today.isoformat(),
            "stock_item": item,
            "inventory_by_id": inventory_by_id,
        }
        try:
            self._recipe_store.save(logic_ready_dict["recipes"])
        except (OSError, ValueError, TypeError):
            return None, SAVE_ERROR
        return logic_ready_dict, None


def create_client():
    # Load optional local configuration and create a client with bounded API retries.
    try:
        from dotenv import load_dotenv
        from groq import Groq
    except ImportError:
        return None, "AI dependencies are missing. Install requirements.txt and retry."

    load_dotenv(Path(__file__).resolve().parent.parent / "apikey.env", override=False)
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None, "GROQ_API_KEY is missing. Configure apikey.env and retry."
    return Groq(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=API_RETRIES), None


# Compatibility functions keep existing callers in the other managers unchanged.


def validate_text(value, field):
    return AssessmentValidator().validate_text(value, field)


def validate_number(value, field, maximum):
    return AssessmentValidator().validate_number(value, field, maximum)


def validate_recipes(recipes, item_id, inventory_ids=None, require_steps=False):
    return AssessmentValidator().validate_recipes(recipes, item_id, inventory_ids, require_steps)


def validate_analysis(value, item_id, inventory_ids=None, require_steps=False):
    return AssessmentValidator().validate_analysis(value, item_id, inventory_ids, require_steps)


def validate_stock_item(item):
    return AssessmentValidator().validate_stock_item(item)


def validate_inputs(item, inventory, today):
    return AssessmentValidator().validate_inputs(item, inventory, today)


def extract_response(completion):
    return AssessmentValidator().extract_response(completion)


def unique_object(pairs):
    return AssessmentValidator().unique_object(pairs)


def reject_constant(value):
    return AssessmentValidator().reject_constant(value)


def parse_response(content):
    return AssessmentValidator().parse_response(content)


def prepare_io_inputs(ai_payload, records):
    return AIManager().prepare_io_inputs(ai_payload, records)


def build_messages(item, inventory, today):
    return AssessmentPrompt().build_messages(item, inventory, today)


def request_completion(client, messages):
    return GroqProvider(client).complete(messages)


def assess_with_client(client, messages, item_id, inventory_ids, require_steps=False):
    return AIManager()._assess_with_provider(
        GroqProvider(client), messages, item_id, inventory_ids, require_steps)


def analyse_item(item, inventory, today, client=None, require_steps=False):
    return AIManager(GroqProvider(client) if client is not None else None).analyse_item(
        item, inventory, today, require_steps)


def save_recipes(recipes):
    return RecipeStore().save(recipes)


def suggest_recipes(final_ai_ready_dict, today=None, client=None):
    return AIManager(GroqProvider(client) if client is not None else None).suggest_recipes(
        final_ai_ready_dict, today)


def analyse_from_io(today=None, client=None):
    # Run the I/O menu and return suggestions and stock data for logic_manager.
    project_dir = Path(__file__).resolve().parent.parent
    try:
        io_data = runpy.run_path(str(project_dir / "io_manager.py"))
        return io_data["main"](today=today, client=client)
    except (OSError, EOFError):
        return None, "Inventory input unavailable. Check food_inventory.csv and retry."
