# FoodRescue AI for Supermarkets

## Project Checkpoint Outline

**Main target audience (TA):** Supermarket staff

**Project purpose:** Help supermarket staff reduce food waste by identifying soon-to-expire or low-demand ingredients and recommending the most suitable next action.

The system can recommend:

- Using an ingredient in an in-store recipe
- Marking an item down for sale
- Sending suitable food for donation
- Flagging an item for staff review
- Rejecting an item when it is unsafe or unsuitable

## 1. Problem Statement and Target Users

### Problem statement

Supermarkets regularly hold ingredients that are approaching their use-by date or have lower-than-expected customer demand. If staff do not act quickly, these products may become food waste. Staff need a fast and consistent way to assess inventory and decide whether an item should be discounted, used in a prepared recipe, donated, or rejected.

FoodRescue AI analyses supermarket inventory records and recommends a practical next action. For ingredients that are soon to expire or have low demand, the system can also suggest recipes that use the available stock.

### Target user

The main target audience (TA) is **supermarket staff**. This includes staff who manage:

- Inventory
- Stock rotation
- Waste reduction
- Product markdowns
- In-store food preparation

The minimum viable product does not require separate customer, charity, restaurant, or cafeteria accounts.

### Project objectives

1. Reduce avoidable supermarket food waste.
2. Help staff identify low-demand and soon-to-expire ingredients.
3. Recommend recipes that use available ingredients before they expire.
4. Provide transparent decisions through structured AI output and business rules.
5. Store processed records so staff can review previous decisions.

## 2. User Inputs

Supermarket staff enter the following information through the terminal:

| Input | Example |
|---|---|
| Product or ingredient name | Tomatoes |
| Category | Fresh produce |
| Quantity and unit | 12 kilograms |
| Use-by date | Two days from now |
| Demand level | Low demand this week |
| Storage condition | Refrigerated |
| Allergen information | Known or uncertain |
| Available ingredients | Tomatoes, onions, herbs, pasta |
| Staff notes | Slightly soft but suitable for cooking |

The I/O manager must validate all input. It should reject invalid quantities, missing item names, invalid dates, and unsupported demand levels, then re-prompt the user.

## 3. Use of AI

Every inventory record passes through the AI manager. The AI is responsible for interpreting the record and returning structured JSON.

### AI responsibilities

The AI should:

- Classify the item or ingredient
- Estimate spoilage risk
- Estimate expiry urgency
- Interpret the demand level
- Identify possible allergen or storage uncertainty
- Calculate or recommend a suitability score
- Suggest recipes using available ingredients
- Explain the reason for its recommendations

The AI manager must not contain supermarket business rules. It is responsible for building the prompt, calling the API, parsing the response, validating the JSON schema, and handling API failures.

### Suitability score

The **suitability score** measures how appropriate an ingredient is for a proposed action. It can use a scale from 0 to 100.

For example, tomatoes may receive a score of 85 for tomato soup because they are stored correctly, have low spoilage risk, have low demand, and are suitable for the recipe.

The score is not a food safety guarantee. It indicates how suitable the item appears for the proposed action.

### Confidence

The **confidence value** measures how certain the AI is about its interpretation.

- `0.90` means the AI is highly confident in its classification and recommendation.
- `0.45` means the input is unclear and staff review is required.

Confidence should depend on the quality and completeness of the input. A high confidence score does not replace staff verification of food safety, storage, or use-by dates.

### Example AI response

```json
{
  "item": "tomatoes",
  "category": "fresh produce",
  "demand_level": "low",
  "expiry_urgency": "high",
  "spoilage_risk": "low",
  "suitability_score": 85,
  "confidence": 0.92,
  "recipe_suggestions": [
    "tomato soup",
    "pasta sauce",
    "fresh salsa"
  ],
  "reason": "The tomatoes are low-demand, suitable for cooking, and nearing their use-by date."
}
```

## 4. Business Rules

The logic manager combines the user inputs and AI output to make the final decision.

| Condition | System action |
|---|---|
| Use-by date has passed | Reject the item and display the reason. |
| Spoilage risk is high | Reject the item or flag it for staff review. |
| Item expires within two days and demand is low | Generate recipe suggestions and recommend staff review. |
| Several compatible ingredients expire soon | Suggest a combined recipe using the available stock. |
| Allergen or storage information is uncertain | Require staff verification before recipe use or sale. |
| Item is safe, suitable, and demand is low | Recommend a markdown or in-store recipe use. |
| Item is safe and suitable for donation | Recommend donation routing as an alternative to disposal. |
| Suitability score is at least 70 and confidence is at least 0.80 | Display the recommendation as high priority. |
| Suitability score is below 50 or confidence is below 0.80 | Place the record under staff review. |

### Recipe safety rule

Recipe suggestions must use ingredients that are within their use-by date and stored correctly. The AI must never recommend using an item that has already expired or has high spoilage risk.

### Example scenario

A supermarket reports 12 kilograms of tomatoes. The tomatoes are refrigerated, have two days remaining before the use-by date, and have low sales demand.

The AI identifies:

- Low demand
- High use urgency
- Low spoilage risk
- Suitability score of 85
- Confidence of 0.92
- Possible recipes: tomato soup, pasta sauce, and fresh salsa

The logic manager recommends recipe use and staff review instead of automatic disposal. Staff must confirm the quality and allergen information before preparing the recipe.

## 5. Team Repository Details

### Repository information

| Repository item | Planned detail |
|---|---|
| GitHub repository URL | [INF1103-LAB-P6-P8](https://github.com/kxuanlyy/INF1103-LAB-P6-P8) |
| Main branch | `main` |
| Feature branches | `feature/io-manager`, `feature/ai-manager`, `feature/logic-manager`, `feature/data-manager` |
| Programming style | 100% procedural Python, with no class definitions |
| Data storage | JSON or CSV |
| Containerization | Docker |

### Suggested team responsibilities

- **I/O manager:** Input validation and terminal output
- **AI manager:** Prompt creation, API calls, JSON parsing, and schema validation
- **Logic manager:** Suitability decisions, recipe rules, and review conditions
- **Data manager:** Saving, loading, filtering, and error handling
- **Testing and documentation:** Test cases, report writing, and demonstration script
- **DevOps and Git:** Docker setup, branch management, and repository verification

### Git and Docker expectations

- Start from an up-to-date `main` branch.
- Use descriptive, short-lived feature branches.
- Commit early and often with meaningful messages.
- Keep the main branch stable.
- Test Docker on every team member's laptop.

Example commands:

```bash
docker build -t foodrescue-ai .
docker run --rm foodrescue-ai
```

## Definition of Done

- Supermarket staff can enter and review an inventory record.
- Every record is processed through the AI API.
- The AI response is structured JSON and is validated before use.
- The logic manager produces a transparent action or recipe recommendation.
- Soon-to-expire and low-demand ingredients trigger useful recipe suggestions.
- Records persist in JSON or CSV and can be filtered.
- Invalid input, API failure, and file errors do not crash the program.
- The project runs in Docker and the Git history shows clear team contributions.
