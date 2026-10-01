# AI manager implementation and commit timeline

The AI manager assesses supermarket stock through Groq and returns validated data to the application. It builds prompts, calls the API, parses JSON, checks the response, and reports failures. The logic manager remains responsible for final supermarket decisions.

This implementation follows the seven supplied programming principles and uses procedural Python with no class definitions. The app continues to use Groq; the request to use Astra concerned the coding assistant.

## Function responsibilities

| Principle | How the implementation applies it |
| --- | --- |
| Single responsibility | Separate functions validate stock, build messages, create the client, request a completion, parse JSON, and validate assessments. The entry point coordinates these steps. |
| DRY | Shared field groups and score limits drive both the response schema and validation. Text and recipe checks are reusable functions. |
| KISS | Plain functions, dictionaries, lists, and a bounded retry loop keep the flow explicit. No custom classes or validation framework are required. |
| Input Process Output | `analyse_item` accepts a stock item, inventory, and assessment date; processes them through the API and validators; returns an assessment/error pair. |
| Modular programming | The AI manager handles model interaction independently from terminal I/O, persistence, and business decisions. Work is recorded in incremental commits. |
| Validate | Check stock inputs before API use, then validate completion status, JSON structure, values, target ID, and recipe references. Handle missing configuration and service failures. |
| Meaningful naming | Names such as `validate_recipes`, `request_completion`, and `inventory_ids` describe their purpose. |

## Integration contract

```python
analysis, error = analyse_item(item, inventory, today, client=None)
```

`today` is a `datetime.date`. `inventory` is a nonempty list with unique string IDs and contains an entry equal to `item`. Each stock item supplies `id`, `name`, `quantity`, `unit`, `use_by`, `demand_level`, `storage_condition`, `storage_status`, `allergens`, and `allergen_status`, matching the existing I/O manager. Quantities must be finite positive numbers and dates must use `YYYY-MM-DD`. An expired date is accepted as input so the item can still be assessed and handled by the logic manager.

On success the result is `(assessment_dict, None)`. On failure it is `(None, error_message)`. Failures never produce invented scores or recommendations, and provider exception details are not displayed.

The assessment has exactly these fields:

| Field | Accepted value |
| --- | --- |
| `item_id` | Exact target ID |
| `category`, `reason` | Nonempty text |
| `demand_level`, `expiry_urgency`, `spoilage_risk` | `low`, `medium`, or `high` |
| `suitability_score` | Finite number from 0 through 100; booleans rejected |
| `confidence` | Finite number from 0 through 1; booleans rejected |
| `allergen_uncertain`, `storage_uncertain` | Boolean |
| `recipe_suggestions` | Zero to five objects, each with a nonempty `name` and unique `ingredient_ids` |

Every recipe must include the target ID and refer only to supplied inventory. The prompt asks for appropriate ingredients; the logic manager enforces date, storage, allergen, and spoilage rules before displaying usable recipes. Schema validation alone does not verify the truth of an AI assessment.

`validate_analysis(value, item_id)` remains compatible with the existing data manager. Its optional third argument supplies inventory IDs for reference checking; `analyse_item` always supplies them.

## Configuration and retry behaviour

Install dependencies with `python -m pip install -r requirements.txt`. Set `GROQ_API_KEY` in the environment or in `apikey.env` beside `ai_manager.py`. Existing environment values take precedence. The environment file is optional when the key is already set. Keep real keys out of Git.

`GROQ_MODEL` can override the default `openai/gpt-oss-120b`. A missing or blank model setting uses that default. Imports do not create clients or send requests.

The internally created Groq client uses a 30-second request timeout and one SDK retry for transient API failures. Invalid, truncated, or malformed model output gets one corrective request. These are separate limits: up to two model-response attempts, each potentially making two HTTP attempts. This is not a single 30-second deadline for the whole operation. Injected clients keep their caller-provided transport settings and are not closed by the manager.

The parser accepts a JSON object with optional enclosing Markdown fences. It rejects prose around JSON, multiple JSON values, duplicate keys, and `NaN` or `Infinity`. Invalid schema values and unknown recipe ingredients trigger the corrective attempt. If it also fails, the caller receives a staff-review error.

## Verification

Run the tests from the repository root:

```text
python -m unittest discover -s tests -v
```

All 35 tests passed on Python 3.14. Tests use standard-library `unittest` function cases, without defining classes. Four transport tests exercise the installed Groq SDK through simulated HTTP responses; they are skipped if production dependencies are absent. No live API requests or real credentials are used.

Coverage includes input rejection before API use, schema boundaries, malformed JSON, duplicate keys, unknown ingredients, corrective retry success and exhaustion, missing keys and dependencies, client cleanup, model configuration, authentication failures, rate limits, timeouts, and server failures.

A separate local integration smoke check confirmed that the existing application can build an assessment record, save and reload it, and pass it to the logic manager. All application modules passed a syntax check. Live Groq output and Docker execution were not tested in this rewrite.

## Commit timeline

These are the actual new commits on `ai_manager`, in chronological order:

| Commit | Milestone |
| --- | --- |
| `cc8b4fc` | Define AI response schema and prompt builder |
| `f18087c` | Add resilient Groq API and JSON parsing |
| `357c8de` | Validate and retry structured AI responses |
| `0df52a5` | Add AI manager unit test coverage |

The fifth milestone, `Document incremental AI manager commit timeline`, adds this document. The first milestone incorporates the existing uncommitted AI manager scaffold; later milestones build on it. `requirements.txt` is included with the API milestone. Other pre-existing local application and Docker work remains outside these commits.

Inspect the history with `git log --oneline -5`. To publish this branch when ready, run:

```text
git push -u origin ai_manager
```

Pushing once publishes all five commits separately. To retain separate milestones in the destination branch when merging, choose a merge commit or rebase merge instead of a squash merge. Rebase merging may change commit hashes. These commits record the work performed in this session; no historical dates were manufactured.
