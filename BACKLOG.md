# Meal Planner Backlog

> **Source of Truth**: Vibe Kanban board (tag: `meal-planner`)
> This file is a fallback when the kanban is unavailable.

## Active (April 2026)

- **[DONE]** Generate missing W13 meal plan (week of Mar 23-29) — committed 2026-03-30
- **[DONE]** W14 plan generation (week Mar 30–Apr 5) — committed 2026-03-29
- **[DONE]** W15 plan (Apr 6–12) — generated 2026-04-07

## Open Items (no urgency)

- **[LOW]** Set up Stock Sheet: create Google Sheet with `ingrediente | en_casa` columns, publish as CSV, add URL to Streamlit secrets as `STOCK_SHEET_URL`
- W03-W06 spending: estimated only (€40-46/week), can be refined
- Factor meals W01-W06: only W01 + W02 known, rest lost with ChatGPT history
- 3 catalog meals without nutrition: Cajun kip, Rode chili pulled pork, Moussaka — no screenshots
- Gember knoflook kip: in catalog from W02 but no nutrition (not on current Factor menu)

## Found by pr-review on PR #5 (W24, 2026-06-09)

- **F-1 [LOW]** Ingredient name drift "Tortita de arroz" (singular) vs "Tortitas de arroz" (plural) across the week. Grammatically Spanish-correct (matches `quantity` 1 vs 2) but the grocery aggregator groups by name, creating two buckets for the same product. Pre-existing pattern across W17-W23. Fix: standardize on plural form repo-wide, OR teach aggregator to normalize singular/plural. Affects: all weekly plans.
- **F-2 [LOW]** New Factor catalog entries `baja-stijl-zalm` and `indiase-stijl-curry-met-kip` lack a `description` field. Most other entries (including the kipfilet update in this PR) have it. Pull descriptions from Factor box labels next time those meals are in rotation.
- **F-3 [LOW]** Factor dinner objects in weekly plans don't have a top-level `name` field (only `factor_meal_id` + item-level name). Free-source dinners (Cena libre, Cena en casa) do have `name`. CLAUDE.md schema example shows `name` on every meal. Inconsistent but not CI-enforced. Pre-existing across W17-W23. Fix: add `name` on Factor dinners, dashboard parity.
- **F-4 [LOW]** Spanish accent stripping in meal/item names: "Platano", "Atun", "Proteina", "Sandwich" should be "Plátano", "Atún", "Proteína", "Sándwich" per RAE and per CLAUDE.md schema example. Pre-existing across all weekly plans. Fix: one-pass sweep with `sed` across `data/plans/`.
