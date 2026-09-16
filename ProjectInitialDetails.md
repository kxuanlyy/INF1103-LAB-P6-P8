# FoodRescue AI: Supermarket Food Waste Reduction

## Project Initial Details Submission

**Primary target audience (TA):** Supermarkets, especially staff who manage inventory and food preparation

**Project purpose:** Help supermarkets assess soon-to-expire or low-demand stock and recommend a practical next action.

The system can recommend:

- Using an ingredient in an in-store recipe
- Marking an item down for sale
- Flagging an item for staff review
- Rejecting an item when it is unsafe or unsuitable

Donation routing may be considered as a future extension after the core supermarket workflow is complete.

## 1. Problem Statement and Target Users

### Problem statement

Supermarkets regularly hold ingredients that are approaching their use-by date or have lower-than-expected demand. If staff do not act quickly, these products may become food waste. Staff need a fast way to assess stock and decide whether it should be discounted, used in an in-store recipe, donated, or rejected.

FoodRescue AI analyses supermarket inventory records and recommends a practical next action. For ingredients that are soon to expire or have low demand, the system can also suggest recipes that use the available stock.

### Target audience

The main target audience is **supermarkets**, particularly supermarket staff who manage:

- Inventory
- Stock rotation
- Waste reduction
- Product markdowns
- In-store food preparation

The initial project focuses on supermarket operations. Other users, such as charities or customers, may be considered in future extensions but are not needed for the initial scope.

### Project objectives

1. Reduce avoidable supermarket food waste.
2. Turn low-demand ingredients into practical recipe options.
3. Make recommendations transparent through structured AI output and business rules.

## 2. User Inputs

Supermarket staff enter the following information through the terminal:

| Input | Example |
|---|---|
| Product or ingredient name | Tomatoes |
| Quantity and unit | 12 kilograms |
| Use-by date | Two days from now |
| Demand level | Low demand this week |
| Storage condition | Refrigerated |
| Allergen information | Known or uncertain |
| Available ingredients | Tomatoes, onions, herbs, pasta |

The I/O manager must validate all input. It should reject invalid quantities, missing item names, invalid dates, and unsupported demand levels, then re-prompt the user.

## 3. Use of AI

Every stock record passes through the AI manager. The AI interprets the item description, estimates expiry urgency and spoilage risk, detects uncertainty, and recommends recipes that use soon-to-expire or low-demand ingredients. The AI returns structured JSON. The logic manager then applies the business rules and produces the final decision.

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
  "demand_level": "low",
  "expiry_urgency": "high",
  "spoilage_risk": "low",
  "suitability_score": 85,
  "confidence": 0.92,
  "recipe_suggestions": [
    "tomato soup",
    "pasta sauce"
  ],
  "reason": "The tomatoes are low-demand, suitable for cooking, and nearing their use-by date."
}
```

## 4. Business Rules

The logic manager combines user inputs and AI-generated outputs. Recipe suggestions are recommendations, not automatic food safety decisions. Staff must confirm quality, storage, allergens, and use-by requirements before acting.

| Condition | System action |
|---|---|
| Use-by date has passed or spoilage risk is high | Reject the item and explain why. |
| Item expires within two days and demand is low | Generate recipe suggestions and recommend staff review. |
| Several compatible ingredients expire soon | Suggest a combined recipe using the available stock. |
| Allergen or storage information is uncertain | Require staff verification before recipe use or sale. |
| Item is safe, suitable, and demand is low | Recommend a markdown or in-store recipe use. |
| Suitability score is at least 70 and confidence is at least 0.80 | Display the recommendation as high priority. |
| Suitability score is below 50 or confidence is below 0.80 | Place the record under staff review. |

### Scope decision

The initial version is deliberately focused on supermarket operations. Recipe recommendations, markdown decisions, staff review, and rejection form the core scope. Donation routing can remain a future extension if the core workflow is completed early.

### Recipe safety rule

Recipe suggestions must use ingredients that are within their use-by date and stored correctly. The AI must never recommend using an item that has already expired or has high spoilage risk.

### Example scenario

A supermarket reports 12 kilograms of tomatoes. The tomatoes are refrigerated, have two days remaining before the use-by date, and have low sales demand. The AI suggests tomato soup and pasta sauce. The logic manager recommends recipe use and staff review instead of automatic disposal.

The AI identifies:

- Low demand
- High use urgency
- Low spoilage risk
- Suitability score of 85
- Confidence of 0.92
- Possible recipes: tomato soup and pasta sauce

Staff must confirm the quality and allergen information before preparing the recipe.

## 5. Repository Information

The team repository requirements are:

| Requirement | Project detail |
|---|---|
| GitHub repository URL | [INF1103-LAB-P6-P8](https://github.com/kxuanlyy/INF1103-LAB-P6-P8) |
| Repository setup | One team member creates the repository and adds all team members and lab-in-charges as collaborators. |
| Team access | All team members clone the shared repository. |
| Initial details file | Create `ProjectInitialDetails.md`, then commit and push it to the repository. |
| Branch practice | Use `main` for stable work and descriptive feature branches for development. |

### Implementation details

- Programming style: 100% procedural Python, with no class definitions
- Data storage: JSON or CSV
- Containerization: Docker

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

Example Docker commands:

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
