# Meal Planner — Claude Code Workflow

## Overview

Streamlit-based meal planner dashboard. Data lives in JSON files, UI is a single `app.py`.

Live: https://meal-planner-ragl.streamlit.app/

## Repository Structure

```
app.py                        # Streamlit dashboard
data/
  profile.json                # User config, targets, rules
  weight.json                 # Weight entries (append-only)
  factor-catalog.json         # Factor meal catalog
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

## Adding a Weight Entry

Ricardo weighs himself **every Monday**. Append to `data/weight.json`:

```json
{ "date": "YYYY-MM-DD", "weight_kg": XX.X }
```

Keep entries sorted by date.

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

## Tech Notes

- Python + Streamlit, managed with `uv`
- Dark theme (indigo/slate palette)
- Plotly for charts (interactive, responsive)
- Deployed on Streamlit Community Cloud (auto-redeploy on push to main)
- `uv run ruff check .` and `uv run ruff format .` for linting
- Pre-commit hooks: ruff + json/yaml/toml validation
- CI validates lint + calorie consistency on every push/PR
