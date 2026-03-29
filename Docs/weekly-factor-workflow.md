# Weekly Factor Meal Plan Workflow

## Overview
Step-by-step process for generating the weekly meal plan. Run every Sunday.

## Prerequisites
- Google Sheet weight data: spreadsheet `1KCKg9JHOlDAK3kBAW09jHe5T6_HRJh4ri87wiYbQyzI`
  - **Peso tab** (gid=101593019): Ricardo inputs weight data
  - **Dashboard tab** (gid=36037005): feeds the Streamlit app (WEIGHT_SHEET_URL)
- Factor account at factormeals.nl (NOT factor.nl)
- `gws` CLI for Google Sheets access

## Step 1: Update Weight Data

```bash
# Fetch latest weight from Google Sheet
gws sheets spreadsheets values get \
  --params '{"spreadsheetId": "1KCKg9JHOlDAK3kBAW09jHe5T6_HRJh4ri87wiYbQyzI", "range": "Peso!A1:E15"}'
```

Compare with `data/weight.json` and append any new entries.
Keep weight.json as fallback — the app reads from Google Sheets first.

## Step 2: Browse Factor Weekly Menu

### Public menu (no login needed)
Navigate to: `https://www.factormeals.nl/weekly-menu`
- Shows 4 weeks ahead (W14-W17 style tabs at the top)
- Click "Toon meer maaltijden" to see all 18 meals
- Each meal shows: name, description, tags (Caloriebewust, Eiwitrijk, Keto, etc.)

### Nutrition per meal
Click any meal to see full recipe page with:
- kcal, kJ per portie and per 100g
- Fat (total + saturated), Carbs (total + sugars), Fiber, Protein, Salt
- Full ingredient list with allergens

### Login limitation
Factor's bot detection blocks Playwright login (as of 2026-03-29).
**Workaround**: Ricardo checks current selection in Factor app/browser, then shares which 4 meals are selected. We use the public pages for nutrition data.

### Recipe URL pattern
```
https://www.factormeals.nl/recipes/{slug}?week=2026-W{N}
```
Slugs are visible in the weekly menu page links.

## Step 3: Select 4 Factor Meals

### Variety rules
- **Never all chicken** — Factor's default selection skews heavily toward chicken (8/18 meals)
- Aim for: 1 chicken + 1 beef/pork + 1 pork/beef + 1 fish (or vegetarian)
- Cross-reference with previous week to avoid repeats

### Lent constraint (until Easter April 5, 2026)
- Every Friday: no red meat. Pick fish or vegetarian for Friday Factor.
- Friday is also fasting day: plan starts at 17:00, ~1500 kcal target.

### Calorie impact
- "Caloriebewust" meals: ~400-500 kcal (easier to fit in 1800 daily target)
- "Keto" / "Eiwitrijk" meals: often 550-650 kcal (need lighter rest-of-day)
- Always check actual kcal on the recipe page — labels are guidelines

## Step 4: Generate the Plan JSON

Follow `CLAUDE.md` plan generation rules:
- Daily target: 1,800 kcal (1,730-1,800 range)
- 5 meal slots: breakfast, lunch, snack1, snack2, dinner
- Dinner kcal is fixed (Factor); adjust other 4 meals to hit target
- Lunches always portable; office-day snacks also portable
- Item kcal must sum exactly to meal total; meal totals must sum to day total

## Step 5: Update Catalog, Manifest, Commit

1. Add new Factor meals to `data/factor-catalog.json`
2. Update `data/plans/manifest.json`
3. Ask Ricardo about the week (journey diary entry if anything notable)
4. Commit and push (triggers Streamlit Cloud redeploy)

## Step 6: Notion Status (if applicable)
Update any meal-related Notion entries if tracked there.

## Learnings Log

### 2026-03-29 (W14 planning)
- **factormeals.nl** is the correct domain (not factor.nl — SSL errors)
- Playwright can browse public menu pages but **cannot log in** (bot detection)
- Factor menu has 18 meals/week; typically 8 chicken, 3 beef, 3 pork, 2 fish, 2 vegetarian
- Google Sheet weight URL needed gid parameter: `&gid=36037005` for Dashboard tab
- The secrets.toml had placeholder ID since project start — now fixed
- `gws sheets spreadsheets values get` is the correct command structure (not `spreadsheets.values`)
