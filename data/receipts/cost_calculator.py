"""
Calculate weekly grocery cost from meal plan ingredients × products.json prices.
Only counts what's explicitly in the plan — excludes Factor and free dinners.
"""

import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent

products = json.loads((DATA / "products.json").read_text())

# English → Spanish mapping for W07 (which used English names)
EN_TO_ES = {
    "Skyr natural": "Skyr natural",
    "Skyr": "Skyr",
    "Oats": "Avena",
    "Apple": "Manzana",
    "Whole wheat bread": "Pan integral",
    "Turkey breast": "Pechuga de pavo",
    "Light cheese": "Queso light",
    "Butter": "Mantequilla",
    "Mustard": "Mostaza",
    "Protein yogurt": "Yogur proteico",
    "Banana": "Plátano",
    "Almonds": "Almendras",
    "Rice cake": "Tortitas de arroz",
    "Rice cakes": "Tortitas de arroz",
    "Peanut butter": "Mantequilla de maní",
    "Scrambled eggs": "Huevos revueltos",
    "Whole wheat wrap": "Wrap integral",
    "Grilled chicken": "Pollo a la plancha",
    "Feta cheese": "Queso feta",
    "Walnuts": "Nueces",
    "Cottage cheese": "Requesón",
    "Honey": "Miel",
    "Honey drizzle": "Miel",
    "Blueberries": "Arándanos",
    "Dark chocolate": "Chocolate negro",
    "Mixed berries": "Frutos rojos",
    "Granola": "Granola",
    "Granola (measured)": "Granola",
    "Tuna in water": "Atún en agua",
    "Light mayo": "Mayonesa light",
    "Greek yogurt light": "Yogur griego light",
    "Hummus": "Hummus",
    "Protein powder": "Proteína en polvo",
    "Milk (semi-skimmed)": "Leche semidesnatada",
    "Quinoa (cooked)": "Quinoa cocida",
    "Olive oil dressing": "Aderezo de aceite de oliva",
    "Protein bar": "Barra de proteína",
    "Homemade popcorn": "Palomitas caseras",
    "Soy sauce": "Salsa de soja",
    "Sesame seeds": "Semillas de sésamo",
    "Parmesan": "Parmesano",
    "Coffee with milk": "Café con leche",
    "Tea with honey": "Té con miel",
    "Avocado": "Aguacate",
    "Carrots": "Zanahorias",
    "Cherry tomatoes": "Tomates cherry",
    "Cucumber": "Pepino",
    "Lettuce": "Lechuga",
    "Lettuce & tomato": "Lechuga y tomate",
    "Mixed fruit": "Frutas mixtas",
    "Mixed greens": "Mix de hojas verdes",
    "Mixed vegetables": "Verduras mixtas",
    "Tangerine": "Mandarinas",
    "Tomato": "Tomate",
}

# Fresh produce not in products.json — prices from receipt analysis
FRESH_PRICES = {
    "Manzana": {"price_eur": 2.35, "size_g": 800, "note": "AH Elstar ~4 apples"},
    "Plátano": {"price_eur": 1.45, "size_g": 1000, "note": "AH Bananen ~5 bananas"},
    "Arándanos": {"price_eur": 3.39, "size_g": 250, "note": "AH blauwe bessen 250g"},
    "Frutos rojos": {"price_eur": 3.39, "size_g": 250, "note": "AH blauwe bessen/mix"},
    "Frutas mixtas": {"price_eur": 2.50, "size_g": 400, "note": "Mixed fruit estimate"},
    "Mandarinas": {"price_eur": 2.79, "size_g": 800, "note": "AH mandarijnen net"},
    "Aguacate": {"price_eur": 1.35, "size_g": 170, "note": "AH avocado (1 piece)"},
    "Tomate": {"price_eur": 0.99, "size_g": 500, "note": "AH trostomaat"},
    "Tomates cherry": {"price_eur": 1.09, "size_g": 250, "note": "AH cherrytomaat"},
    "Pepino": {"price_eur": 0.99, "size_g": 400, "note": "AH komkommer"},
    "Lechuga": {"price_eur": 0.85, "size_g": 200, "note": "AH kropsla"},
    "Lechuga y tomate": {"price_eur": 1.50, "size_g": 500, "note": "Combo estimate"},
    "Mix de hojas verdes": {"price_eur": 1.29, "size_g": 150, "note": "AH rucola/slamix"},
    "Zanahorias": {"price_eur": 1.69, "size_g": 500, "note": "AH wortelen"},
    "Verduras mixtas": {"price_eur": 1.99, "size_g": 400, "note": "AH snoepgroente"},
    "Brócoli al vapor": {"price_eur": 1.49, "size_g": 400, "note": "AH broccoli"},
    "Espinacas": {"price_eur": 1.69, "size_g": 250, "note": "AH spinazie"},
}

# Items that are essentially free or immeasurable
SKIP_ITEMS = {
    "Café con leche",
    "Té con miel",
    "Té",
    "Coffee with milk",
    "Tea with honey",
    "Canela",
    "Cinnamon",
    "Salsa de yogur",
    "Yogurt sauce",
    "Free dinner (social/restaurant)",
    "Cena XKE en oficina",
}

FRACTION_MAP = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 0.333}

# Grams per single unit for count-based items
GRAMS_PER_UNIT = {
    "Huevos revueltos": 60,  # per egg
    "Plátano": 120,  # 1 medium banana
    "Manzana": 180,  # 1 medium apple
    "Mandarinas": 70,  # 1 tangerine
    "Aguacate": 170,  # 1 avocado
    "Tomate": 150,  # 1 medium tomato
    "Yogur proteico": 200,  # 1 pot
    "Barra de proteína": 55,  # 1 bar
    "Tortitas de arroz": 9,  # 1 cake
    "Tortita de arroz": 9,
    "Pan integral": 50,  # 1 slice
    "Wrap integral": 62,  # 1 wrap
    "Atún en agua": 160,  # 1 can
    "Pechuga de pavo": 21,  # 1 slice deli meat (but usually specified in g)
}


def parse_qty(qty_str: str) -> tuple[float, str]:
    """Parse quantity string → (amount, unit).
    unit is 'g', 'ml', or 'count'.
    """
    q = qty_str.strip()

    # "250g", "40g", "70g seca", "30g granos"
    m = re.match(r"([\d.]+)\s*g\b", q)
    if m:
        return float(m.group(1)), "g"

    # "150ml"
    m = re.match(r"([\d.]+)\s*ml", q)
    if m:
        return float(m.group(1)), "ml"

    # "1 can (120g)", "1 lata (120g)"
    m = re.search(r"\((\d+)g\)", q)
    if m:
        return float(m.group(1)), "g"

    # Spoon measures → grams
    for frac, val in FRACTION_MAP.items():
        if frac in q:
            if "cdta" in q or "tsp" in q:
                return val * 5, "g"
            if "cda" in q or "tbsp" in q:
                return val * 15, "g"
            # fraction of a unit (e.g., "½ mediano", "¼ mediano")
            return val, "count"

    m = re.match(r"([\d.]+)\s*cdtas?", q)
    if m:
        return float(m.group(1)) * 5, "g"
    m = re.match(r"([\d.]+)\s*cdas?", q)
    if m:
        return float(m.group(1)) * 15, "g"
    m = re.match(r"([\d.]+)\s*tsp", q)
    if m:
        return float(m.group(1)) * 5, "g"
    m = re.match(r"([\d.]+)\s*tbsp", q)
    if m:
        return float(m.group(1)) * 15, "g"

    # Count-based: "2 rebanadas", "1 grande", "2 grandes", "1 mediano", etc.
    m = re.match(
        r"([\d.]+)\s*(rebanadas?|grandes?|medianos?|medianas?|medium|large|pot|vasitos?|cups?|tazas?|latas?|unidad|slices?)",
        q,
    )
    if m:
        return float(m.group(1)), "count"

    # Bare number
    m = re.match(r"^([\d.]+)$", q)
    if m:
        return float(m.group(1)), "count"

    # "pinch"
    if "pinch" in q or "pizca" in q:
        return 0.5, "g"

    return 0, "unknown"


def parse_pkg_size(size_str: str) -> tuple[float, str]:
    """Parse products.json size → (amount, unit: 'g'|'ml'|'stuks')."""
    s = size_str.lower().strip()
    m = re.match(r"(\d+)\s*g", s)
    if m:
        return float(m.group(1)), "g"
    m = re.match(r"(\d+)\s*ml", s)
    if m:
        return float(m.group(1)), "ml"
    m = re.match(r"([\d.]+)\s*l$", s)
    if m:
        return float(m.group(1)) * 1000, "ml"
    m = re.match(r"(\d+)\s*stuks?", s)
    if m:
        return float(m.group(1)), "stuks"
    # "370g (6 stuks)" → grams
    m = re.match(r"(\d+)\s*g\s*\(", s)
    if m:
        return float(m.group(1)), "g"
    return 0, "unknown"


def compute_weekly_cost(plan_file: Path) -> dict:
    """Compute grocery cost from a plan file."""
    plan = json.loads(plan_file.read_text())
    week = plan["week"]
    year = plan["year"]

    # Collect (ingredient_es, amount_g) for each usage
    # We normalize everything to grams for comparison with product packages.
    # For stuks-based products (eggs), we keep count separately.
    ingredient_totals = {}  # name → {"grams": float, "count": float}

    for day in plan["days"]:
        for _slot, meal in day["meals"].items():
            source = meal.get("source", "")
            if source in ("factor", "free"):
                continue

            for item in meal["items"]:
                name = item["name"]
                qty = item["quantity"]

                if name in SKIP_ITEMS:
                    continue

                es_name = EN_TO_ES.get(name, name)

                amount, unit = parse_qty(qty)

                if es_name not in ingredient_totals:
                    ingredient_totals[es_name] = {"grams": 0, "count": 0}

                if unit in ("g", "ml"):
                    ingredient_totals[es_name]["grams"] += amount
                elif unit == "count":
                    ingredient_totals[es_name]["count"] += amount

    # Calculate costs
    results = []
    total_cost = 0
    unpriced = []

    for ingredient, usage in sorted(ingredient_totals.items()):
        total_g = usage["grams"]
        total_count = usage["count"]

        # Find product info
        product = products.get(ingredient)
        fresh = FRESH_PRICES.get(ingredient)

        price_source = None
        price_eur = 0
        pkg_size = 0
        pkg_unit = ""
        product_name = ""

        if product:
            price_eur = product["price_eur"]
            pkg_size, pkg_unit = parse_pkg_size(product["size"])
            product_name = product["ah_product"]
            price_source = "products.json"
        elif fresh:
            price_eur = fresh["price_eur"]
            pkg_size = fresh["size_g"]
            pkg_unit = "g"
            product_name = f"[Fresh] {fresh['note']}"
            price_source = "receipt estimate"

        if not price_source:
            if total_g > 0 or total_count > 0:
                unpriced.append({"ingredient": ingredient, "grams": total_g, "count": total_count})
            continue

        # Convert everything to comparable units
        if pkg_unit == "stuks":
            # Package is count-based (eggs). Compare count to count.
            # If we have grams from the plan, convert to count using GRAMS_PER_UNIT
            effective_count = total_count
            if total_g > 0 and ingredient in GRAMS_PER_UNIT:
                effective_count += total_g / GRAMS_PER_UNIT[ingredient]
            elif total_g > 0:
                effective_count += total_g  # fallback: assume g = count (shouldn't happen)

            packages = effective_count / pkg_size if pkg_size else 0
            usage_str = f"{effective_count:.0f} units"
            pkg_str = f"{pkg_size:.0f} stuks"
        else:
            # Package is gram/ml-based. Convert count to grams if needed.
            effective_g = total_g
            if total_count > 0:
                grams_per = GRAMS_PER_UNIT.get(ingredient, 0)
                if grams_per:
                    effective_g += total_count * grams_per
                else:
                    # For items without GRAMS_PER_UNIT, assume 1 count = 1 package
                    # (e.g., "1 pot" of yogurt, "1 bar" of protein)
                    effective_g += total_count * pkg_size

            packages = effective_g / pkg_size if pkg_size else 0
            usage_str = f"{effective_g:.0f}g"
            pkg_str = product["size"] if product else f"{pkg_size:.0f}g"

        cost = packages * price_eur
        total_cost += cost
        results.append(
            {
                "ingredient": ingredient,
                "weekly_usage": usage_str,
                "product": product_name,
                "package": pkg_str,
                "price_eur": price_eur,
                "packages": round(packages, 2),
                "cost_eur": round(cost, 2),
            }
        )

    return {
        "year": year,
        "week": week,
        "items": results,
        "total_grocery_eur": round(total_cost, 2),
        "unpriced": unpriced,
    }


def main():
    plans_dir = DATA / "plans" / "2026"

    print("=" * 70)
    print("WEEKLY GROCERY COST FROM MEAL PLANS")
    print("(Only ingredients explicitly in the plan, excludes Factor/free)")
    print("=" * 70)

    for plan_file in sorted(plans_dir.glob("W*.json")):
        if "draft" in plan_file.name:
            continue

        result = compute_weekly_cost(plan_file)
        w = f"W{result['week']:02d}"
        print(f"\n### {w} (Year {result['year']})")
        print(
            f"{'Ingredient':<28} {'Usage':<12} {'Product':<32} "
            f"{'Pkg':<14} {'€/pkg':>6} {'Pkgs':>5} {'€ Cost':>7}"
        )
        print("-" * 110)

        for item in sorted(result["items"], key=lambda x: -x["cost_eur"]):
            print(
                f"{item['ingredient']:<28} {item['weekly_usage']:<12} "
                f"{item['product'][:31]:<32} {item['package']:<14} "
                f"{item['price_eur']:>6.2f} {item['packages']:>5.2f} "
                f"{item['cost_eur']:>7.2f}"
            )

        print("-" * 110)
        print(
            f"{'TOTAL GROCERY':<28} {'':12} {'':32} {'':14} "
            f"{'':>6} {'':>5} {result['total_grocery_eur']:>7.2f}"
        )
        print(f"{'+ Factor (4 meals)':<28} {'':12} {'':32} {'':14} {'':>6} {'':>5} {'62.93':>7}")
        print(
            f"{'= TOTAL DIET COST':<28} {'':12} {'':32} {'':14} "
            f"{'':>6} {'':>5} {result['total_grocery_eur'] + 62.93:>7.2f}"
        )

        if result["unpriced"]:
            print(f"\nUnpriced ({len(result['unpriced'])}):")
            for item in result["unpriced"]:
                print(f"  - {item['ingredient']}: {item['grams']:.0f}g + {item['count']:.0f} count")

    # JSON output for spending.json
    print("\n\n" + "=" * 70)
    print("SPENDING.JSON DATA (plan-based grocery costs)")
    print("=" * 70)

    spending = []
    for plan_file in sorted(plans_dir.glob("W*.json")):
        if "draft" in plan_file.name:
            continue
        result = compute_weekly_cost(plan_file)
        spending.append(
            {
                "year": result["year"],
                "week": result["week"],
                "factor_eur": 62.93,
                "grocery_eur": result["total_grocery_eur"],
            }
        )
    print(json.dumps(spending, indent=2))


if __name__ == "__main__":
    main()
