# Weekly Grocery Cost Estimates (W01-W08)

## Sources
- **W01-W02**: Google Sheet meal plan + products.json prices
- **W03-W06**: Estimated from pattern (similar meals, unknown Factor lineup)
- **W07-W08**: Calculated from JSON plan files (`cost_calculator.py`)

---

## W01 (Jan 12-18) — 6 Factor meals, Sun libre

From Google Sheet. Simple plan, first week of diet.

| Meal slot | Ingredients (5 working days + Sat) | Est. cost |
|-----------|-------------------------------------|-----------|
| Breakfast | Skyr/Yogur 3×200g, Smoothie 2× (store), Avena 2×40g, Granola 1×35g, Chía 3×10g, Fruta 3× | ~€10 |
| Lunch | Pan integral 5×2 slices, Pavo 2×100g, Pollo 2×100g, Atún 1×120g, Queso/Mostaza/Mantequilla | ~€14 |
| Snacks | Manzana 2×, Plátano 1×, Almendras 2×15g, Yogur/Skyr 3×, Huevo 1×, Fruta 2× | ~€8 |
| Sat/Sun | Familiar/Libre — minimal diet grocery | ~€3 |
| **W01 grocery total** | | **~€35** |

Notes:
- First week used pantry items from the €213 Jan 10 stock-up (granola, oats, almonds, peanut butter, etc.)
- Smoothies were likely store-bought AH Smoothie (~€1.99 each)
- Saturday "Desayuno familiar / Comida familiar" = family cooking, not counted
- Factor had 6 meals this week (not 4 like later weeks)

## W02 (Jan 19-25) — 5 Factor meals, Mon=work dinner, Tue=XKE

Very similar pattern to W01. Two free dinners (work + XKE office event).

| Meal slot | Ingredients (5 working days + weekend) | Est. cost |
|-----------|----------------------------------------|-----------|
| Breakfast | Same pattern as W01 | ~€10 |
| Lunch | Same sandwiches (jamón replaces pavo 2×), pollo 2×, atún 1× | ~€13 |
| Snacks | Barras cereal 2×, Almendras, Plátano 2×, Yogur 3×, Huevo 1× | ~€10 |
| Sat/Sun | Familiar + Factor Sunday | ~€3 |
| **W02 grocery total** | | **~€36** |

Notes:
- Added barras cereal/proteica (2×) — ~€3-4 for protein bars
- Factor had 5 meals (Wed-Sun), Mon=work dinner, Tue=XKE
- Still using pantry from the big stock-up

## W03-W06 (Jan 26 - Feb 8) — Estimated

Ricardo's description: "The weekly planning was quite similar. Sandwiches with different
protein each day, snacks were always protein (skyr, Lindahl's), fiber with fruits
(nuts, granola bars, apples, bananas)."

As weeks progressed, the plan likely became slightly more varied (more ingredient types,
better proportioning) based on what the receipts show — more Lindahls, avocados, and
fresh vegetables appearing.

| Week | Est. grocery | Reasoning |
|------|-------------|-----------|
| W03 | ~€40 | Pantry stock-up starting to deplete, buying more fresh items |
| W04 | ~€42 | Similar pattern, receipts show more variety |
| W05 | ~€44 | Growing variety, Lindahls appears frequently on receipts |
| W06 | ~€46 | Approaching W07 complexity |

## W07-W08 — Calculated from plans

| Week | Grocery (calculated) | Method |
|------|---------------------|--------|
| W07 | €53.24 | `cost_calculator.py` from W07.json |
| W08 | €59.78 | `cost_calculator.py` from W08.json |

W08 is higher because it has 2 homemade dinners (Thursday/Friday) instead of Factor,
adding chicken, rice, pasta, and more ingredients.

---

## Summary: spending.json data

| Week | Factor € | Grocery € | Total € | Source |
|------|----------|-----------|---------|--------|
| W01 | 62.93 | 35.00 | 97.93 | Sheet + estimate |
| W02 | 62.93 | 36.00 | 98.93 | Sheet + estimate |
| W03 | 62.93 | 40.00 | 102.93 | Estimate |
| W04 | 62.93 | 42.00 | 104.93 | Estimate |
| W05 | 62.93 | 44.00 | 106.93 | Estimate |
| W06 | 62.93 | 46.00 | 108.93 | Estimate |
| W07 | 62.93 | 53.24 | 116.17 | Calculated |
| W08 | 62.93 | 59.78 | 122.71 | Calculated |

**Average weekly diet cost: ~€107.30**
**Average grocery-only: ~€44.50/week**
**All weeks within €120 budget** (except W08 at €122.71, just slightly over)
