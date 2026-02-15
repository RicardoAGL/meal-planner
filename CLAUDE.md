# Meal Planner — Claude Code Workflow

## Overview

Streamlit-based meal planner dashboard. Data lives in JSON files, UI is a single `app.py`.

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

## Generating a Weekly Meal Plan

### Input

The user provides:
1. The Factor meals for the week (name + kcal for each)
2. Which days get which Factor meal
3. Any overrides (e.g., restaurant dinner on Saturday)

### Rules

- **Daily target**: 1,800 kcal (aim for 1,730–1,800 range)
- **5 meal slots**: breakfast (09:00), lunch (12:00), snack1 (14:30), snack2 (17:30), dinner (20:00)
- **Dinner calories are fixed** — adjust the other 4 meals to hit the daily target
- **Higher-calorie dinner (>500 kcal)**: lighter breakfast/snacks
- **Lower-calorie dinner (<450 kcal)**: slightly more generous rest of day
- **Lunches must be portable** (sandwiches, wraps, salads in containers)
- **Friday**: office day — snacks must also be portable
- **Sunday dinner**: free/social, budget 600–700 kcal
- **Vary breakfasts** across the week (don't repeat the same one daily)
- **Ingredients from Albert Heijn** (Netherlands supermarket)
- **Prefer simple meals** with overlapping ingredients to reduce waste
- **CRITICAL**: item-level kcal MUST sum exactly to meal total_kcal, and meal totals MUST sum to day total_kcal. CI checks this.

### Output Schema

Create `data/plans/{YEAR}/W{WEEK}.json`:

```json
{
  "year": 2026,
  "week": 7,
  "start_date": "2026-02-09",
  "end_date": "2026-02-15",
  "daily_target_kcal": 1800,
  "days": [
    {
      "date": "2026-02-09",
      "weekday": "Monday",
      "total_kcal": 1789,
      "meals": {
        "breakfast": {
          "time": "09:00",
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
          "total_kcal": 424,
          "source": "factor",
          "factor_meal_id": "kip-aubergine-mozzarella",
          "items": [
            { "name": "Kip & aubergine in mozzarella-pomodorosaus", "quantity": "1 meal", "kcal": 424 }
          ]
        }
      }
    }
  ]
}
```

### After generating the plan

1. Write the plan JSON file
2. Add new Factor meals to `data/factor-catalog.json` if not already present
3. Update `data/plans/manifest.json` — add the new entry to the `plans` array

## Adding a Weight Entry

Append to `data/weight.json`:

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
- Plotly for charts (interactive, responsive)
- `uv run ruff check .` and `uv run ruff format .` for linting
- Pre-commit hooks: ruff + json validation
- CI validates lint + calorie consistency on every push/PR
