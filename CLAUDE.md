# Meal Planner — Claude Code Workflow

## Overview

Streamlit-based meal planner dashboard. Data lives in JSON files, UI is a single `app.py`.

Live: https://meal-planner-ragl.streamlit.app/

## Repository Structure

```
app.py                        # Streamlit dashboard (4 tabs)
data/
  profile.json                # User config, targets, rules, budget
  weight.json                 # Weight entries (append-only)
  factor-catalog.json         # Factor meal catalog
  ingredient-categories.json  # Ingredient → category mapping
  products.json               # AH product database (ingredient → product details)
  spending.json               # Weekly spending data (Factor + grocery)
  journey.json                # Weight loss journey milestones & decisions
  plans/
    manifest.json             # Index of all weekly plans
    2026/W07.json             # One file per week
.streamlit/config.toml        # Streamlit theme & settings
pyproject.toml                # UV project config
uv.lock                       # Lockfile
```

## Running Locally

```bash
uv run streamlit run app.py
```

---

## Quick Start: Planning a Week

Ricardo provides input in **any** of these formats (simplest first):

### Option 1: Screenshot (fastest)

Share a screenshot of the Factor order confirmation (email, app, or website).
Claude Code reads the image, extracts meal names + calories, and generates the plan.

### Option 2: Paste raw text

Copy-paste text from the Factor email/app. No formatting needed:

```
My Factor meals this week:
Kip tikka masala 485
Zalm met groenten 420
Beef stroganoff 510
Pasta bolognese 530
```

### Option 3: Reference the catalog

If meals are already in `data/factor-catalog.json`, use short names:

```
Same 4 as last week, but swap the risotto for the zalm.
Office days: Tuesday and Friday.
Thursday I have a dinner event, skip Factor.
```

### What Claude Code does with this

1. Parse the Factor meals (from image, text, or catalog lookup)
2. Check `data/factor-catalog.json` — add any new meals
3. Load the previous week's plan for meal rotation reference
4. Generate the new week's JSON following all rules below
5. Update `data/plans/manifest.json`
6. Commit and push (triggers Streamlit Cloud redeploy)

---

## Plan Generation Rules

### Calories
- **Daily target**: 1,800 kcal (aim for 1,730–1,800 range)
- **5 meal slots**: breakfast (09:00), lunch (12:00), snack1 (14:30), snack2 (17:30), dinner (20:00)
- **Dinner calories are fixed** — adjust the other 4 meals to hit the daily target
- **Higher-calorie dinner (>500 kcal)**: lighter breakfast/snacks
- **Lower-calorie dinner (<450 kcal)**: slightly more generous rest of day
- **CRITICAL**: item-level kcal MUST sum exactly to meal total_kcal, and meal totals MUST sum to day total_kcal. CI checks this.

### Factor Dinners
- **4 Factor meals per week** (Mon–Thu or as specified)
- Remaining dinner days: free/social (Sun, budget 600–700 kcal) or homemade
- If the user has leftovers or events, they'll specify which days to skip Factor

### Recurring Events
- **XKE day**: Every 2 weeks on Tuesday — dinner is provided at the office (free, ~600 kcal). Skip Factor that day and redistribute.

### Portability
- **Lunches are always portable** (sandwiches, wraps, salads in containers)
- **Office days** (default: Friday, user may specify others): snacks must also be portable
- Set `"portable": true` on any portable meal
- Set `"office_day": true` on the day object for non-default office days

### Language
- **Meal names and item names in Spanish** (wife uses the dashboard for shopping/planning)
- Each meal has a `"name"` field: short Spanish description (e.g., "Sándwich de pavo")
- Item names in Spanish (e.g., "Pan integral", "Pechuga de pavo", "Mantequilla de maní")
- Factor dinner names stay in **Dutch** (branded product names from the label)
- Quantities use metric: g, ml, cdta (cucharadita), cda (cucharada), mediano/a, rebanada

### Meal Rotation
- **Reference the previous week's plan** when generating a new one
- Keep ~60% of breakfasts/lunches similar (low overhead for shopping/prep)
- Vary ~40% to avoid monotony (rotate 2-3 items per week)
- **Prefer overlapping ingredients** across the week to reduce waste
- **Ingredients from Albert Heijn** (Netherlands supermarket)

### Day-Level Notes
- Days can have a `"notes"` field for context: `"notes": "Dinner event, skip Factor"`
- The dashboard renders these as annotations on the day card

### Output Schema

Create `data/plans/{YEAR}/W{WEEK}.json`:

```json
{
  "year": 2026,
  "week": 8,
  "start_date": "2026-02-16",
  "end_date": "2026-02-22",
  "daily_target_kcal": 1800,
  "days": [
    {
      "date": "2026-02-16",
      "weekday": "Monday",
      "total_kcal": 1789,
      "meals": {
        "breakfast": {
          "time": "09:00",
          "name": "Skyr con avena y plátano",
          "total_kcal": 400,
          "items": [
            { "name": "Skyr natural", "quantity": "250g", "kcal": 165 }
          ]
        },
        "lunch": {
          "time": "12:00",
          "total_kcal": 450,
          "portable": true,
          "items": [...]
        },
        "snack1": { "time": "14:30", "total_kcal": 150, "items": [...] },
        "snack2": { "time": "17:30", "total_kcal": 365, "items": [...] },
        "dinner": {
          "time": "20:00",
          "total_kcal": 485,
          "source": "factor",
          "factor_meal_id": "kip-tikka-masala",
          "items": [
            { "name": "Kip tikka masala", "quantity": "1 meal", "kcal": 485 }
          ]
        }
      }
    }
  ]
}
```

Days with events or non-default office days:

```json
{
  "date": "2026-02-20",
  "weekday": "Thursday",
  "office_day": true,
  "notes": "Office day + team dinner",
  "total_kcal": 1780,
  "meals": { ... }
}
```

### After generating the plan

1. Write the plan JSON file
2. Add new Factor meals to `data/factor-catalog.json` if not already present
3. Update `data/plans/manifest.json` — add the new entry to the `plans` array
4. Commit and push

---

## Weight Tracking

Ricardo weighs himself **every Monday**.

### Primary: Google Sheet (live data)

The app reads weight data from a Google Sheet via published CSV export.
The URL is stored in Streamlit secrets (`WEIGHT_SHEET_URL`), not in the repo.

**Sheet format** — two columns, any header names (parsed by position):

| date | weight_kg |
|------|-----------|
| 2026-01-12 | 111.8 |

The app caches the sheet data for 5 minutes (`ttl=300`).

### Fallback: `data/weight.json`

If no sheet URL is configured or the fetch fails, the app falls back to `data/weight.json`.
This file serves as seed data and a safety net. Keep it sorted by date:

```json
{ "date": "YYYY-MM-DD", "weight_kg": XX.X }
```

## Factor Catalog

When the user provides new Factor meals, add them to `data/factor-catalog.json`:

```json
{
  "id": "kebab-style-slug",
  "name": "Full Dutch name from label",
  "kcal": 450,
  "first_seen": "YYYY-MM-DD"
}
```

The `id` is a URL-safe kebab-case slug of the meal name.

## Grocery List & Ingredient Naming

The grocery list tab aggregates ingredients from the weekly plan, skipping Factor and free dinners.

### Ingredient naming conventions
- Use the **exact same name** consistently across plans — the grocery list groups by name
- Spanish names (e.g., "Pan integral", "Mantequilla de maní")
- When adding a new ingredient, also add it to `data/ingredient-categories.json`
- Categories: `lacteos`, `frutas`, `verduras`, `carnes_proteinas`, `panaderia`, `frutos_secos`, `despensa`, `suplementos`, `otros`
- Unknown ingredients default to "otros"

### Quantity format
- Use consistent units: `g`, `ml`, `cdta`, `cda`, `mediano/a`, `rebanada/s`, `grande/s`, `vasito`, `taza`, `lata`, `unidad`
- Prefer singular when possible with a number: `"1 mediano"`, `"2 rebanadas"`
- The aggregation engine sums matching units across the week

### Stock tracking (Google Sheet)
- Published CSV at `STOCK_SHEET_URL` in Streamlit secrets
- Columns: `ingrediente | en_casa` (TRUE/FALSE checkbox)
- Wife checks off what's available; app shows what's missing

### AH Products (`data/products.json`)
```json
{
  "Skyr natural": {
    "ah_product": "Arla Skyr Naturel",
    "ah_url": "https://www.ah.nl/producten/product/...",
    "brand": "Arla",
    "size": "450g",
    "price_eur": 1.99
  }
}
```

## Budget & Spending

### Spending data (`data/spending.json` or `SPENDING_SHEET_URL`)
```json
[{"year": 2026, "week": 2, "factor_eur": 62.93, "grocery_eur": 45.00}]
```

### Budget settings (in `profile.json`)
- `budget_weekly_eur`: soft weekly budget (default 120)
- `factor_weekly_eur`: Factor subscription cost per week (62.93)

## Journey Diary (`data/journey.json`)

A weight loss diary that captures the human story behind the numbers. Each entry:

```json
{
  "date": "2026-02-07",
  "type": "challenge",
  "title": "Boda — buffet de carne y pastel",
  "body": "Full story in Ricardo's words...",
  "weight_kg": null,
  "week": 5,
  "tags": ["social", "self-control", "win"],
  "photo": null
}
```

**Entry types**: `milestone`, `decision`, `challenge`, `reflection`

**When to add entries**:
- During weekly plan updates, ask Ricardo: "Anything special this week? Challenges, wins, social events?"
- When making significant dashboard/tool changes
- When Ricardo shares a personal story or achievement
- Weight records that mark a new low or a plateau

**Tags** are free-form but prefer reusing: `start`, `commitment`, `factor`, `strategy`, `nutrition`, `social`, `self-control`, `win`, `tech`, `tools`, `grocery`, `budget`, `plateau`, `new-low`

## Tech Notes

- Python + Streamlit, managed with `uv`
- Dark theme (indigo/slate palette)
- Plotly for charts (interactive, responsive)
- Deployed on Streamlit Community Cloud (auto-redeploy on push to main)
- `uv run ruff check .` and `uv run ruff format .` for linting
- Pre-commit hooks: ruff + json/yaml/toml validation
- CI validates lint + calorie consistency on every push/PR
