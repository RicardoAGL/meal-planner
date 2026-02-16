"""Meal Planner — Streamlit dashboard for weekly meal plans and weight tracking."""

import csv
import json
import re
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Meal Planner",
    page_icon="\U0001f37d\ufe0f",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60)
def load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_profile():
    return load_json(DATA_DIR / "profile.json")


@st.cache_data(ttl=300)
def _fetch_weight_from_gsheet(url: str) -> list | None:
    """Fetch weight entries from a published Google Sheet (CSV export)."""
    try:
        response = urllib.request.urlopen(url, timeout=10)  # noqa: S310
        content = response.read().decode("utf-8")
        reader = csv.reader(StringIO(content))
        next(reader)  # skip header row
        entries = []
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                entries.append(
                    {
                        "date": row[0].strip(),
                        "weight_kg": float(row[1].strip()),
                    }
                )
        return sorted(entries, key=lambda e: e["date"]) if entries else None
    except Exception:
        return None


def _secret(key: str) -> str | None:
    """Safely read a Streamlit secret, returning None if missing."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def load_weight():
    url = _secret("WEIGHT_SHEET_URL")
    if url:
        data = _fetch_weight_from_gsheet(url)
        if data:
            return data
    return load_json(DATA_DIR / "weight.json")


def load_manifest():
    return load_json(DATA_DIR / "plans" / "manifest.json")


def load_plan(file: str):
    return load_json(DATA_DIR / "plans" / file)


def load_ingredient_categories() -> dict:
    return load_json(DATA_DIR / "ingredient-categories.json") or {}


def load_products() -> dict:
    return load_json(DATA_DIR / "products.json") or {}


@st.cache_data(ttl=300)
def _fetch_stock_from_gsheet(url: str) -> set | None:
    """Fetch stocked ingredient names from a published Google Sheet (CSV)."""
    try:
        response = urllib.request.urlopen(url, timeout=10)  # noqa: S310
        content = response.read().decode("utf-8")
        reader = csv.reader(StringIO(content))
        next(reader)  # skip header
        stocked = set()
        for row in reader:
            if len(row) >= 2 and row[0].strip():
                checked = row[1].strip().upper()
                if checked in ("TRUE", "SI", "SÍ", "1", "X", "YES"):
                    stocked.add(row[0].strip())
        return stocked
    except Exception:
        return None


def load_stock() -> set:
    url = _secret("STOCK_SHEET_URL")
    if url:
        data = _fetch_stock_from_gsheet(url)
        if data is not None:
            return data
    return set()


def load_spending() -> list:
    url = _secret("SPENDING_SHEET_URL")
    if url:
        data = _fetch_spending_from_gsheet(url)
        if data:
            return data
    return load_json(DATA_DIR / "spending.json") or []


@st.cache_data(ttl=300)
def _fetch_spending_from_gsheet(url: str) -> list | None:
    """Fetch spending data from a published Google Sheet (CSV)."""
    try:
        response = urllib.request.urlopen(url, timeout=10)  # noqa: S310
        content = response.read().decode("utf-8")
        reader = csv.reader(StringIO(content))
        next(reader)  # skip header
        entries = []
        for row in reader:
            if len(row) >= 4 and row[0].strip() and row[1].strip():
                entry = {
                    "year": int(row[0].strip()),
                    "week": int(row[1].strip()),
                    "factor_eur": float(row[2].strip()) if row[2].strip() else None,
                    "grocery_eur": float(row[3].strip()) if row[3].strip() else None,
                }
                entries.append(entry)
        return entries if entries else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MEAL_ICONS = {
    "breakfast": "\u2615",
    "lunch": "\U0001f96a",
    "snack1": "\U0001f34e",
    "snack2": "\U0001f34c",
    "dinner": "\U0001f37d\ufe0f",
}

MEAL_LABELS = {
    "breakfast": "Desayuno",
    "lunch": "Almuerzo",
    "snack1": "Merienda 1",
    "snack2": "Merienda 2",
    "dinner": "Cena",
}

SOURCE_LABELS = {
    "factor": "\U0001f4e6 Factor",
    "free": "\U0001f389 Libre / Social",
    "homemade": "\U0001f373 Casero",
}

WEEKDAY_ES = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Mi\u00e9rcoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "S\u00e1bado",
    "Sunday": "Domingo",
}

OFFICE_DAYS = {"Friday"}

CATEGORY_LABELS = {
    "lacteos": "\U0001f95b L\u00e1cteos",
    "frutas": "\U0001f34e Frutas",
    "verduras": "\U0001f966 Verduras",
    "carnes_proteinas": "\U0001f357 Carnes & Prote\u00ednas",
    "panaderia": "\U0001f35e Panader\u00eda & Cereales",
    "frutos_secos": "\U0001f95c Frutos Secos",
    "despensa": "\U0001f3e0 Despensa",
    "suplementos": "\U0001f4aa Suplementos",
    "otros": "\U0001f4e6 Otros",
}

CATEGORY_ORDER = [
    "carnes_proteinas",
    "lacteos",
    "frutas",
    "verduras",
    "panaderia",
    "frutos_secos",
    "despensa",
    "suplementos",
    "otros",
]


def calorie_status(actual: int, target: int) -> str:
    diff = abs(actual - target)
    if diff <= 50:
        return "on-target"
    if diff <= 100:
        return "near-target"
    return "off-target"


def calorie_indicator(actual: int, target: int) -> str:
    """Return a colored circle emoji for calorie status."""
    status = calorie_status(actual, target)
    if status == "on-target":
        return "\U0001f7e2"
    if status == "near-target":
        return "\U0001f7e1"
    return "\U0001f534"


def _dinner_display_name(day: dict) -> str:
    """Extract the dinner display name from a day object."""
    dinner = day.get("meals", {}).get("dinner", {})
    name = dinner.get("name", "")
    if not name:
        items = dinner.get("items", [])
        name = items[0].get("name", "\u2014") if items else "\u2014"
    return name[:35] + "..." if len(name) > 35 else name


def _meal_display_name(meal: dict) -> str:
    """Get the display name: explicit name field, or first item name as fallback."""
    name = meal.get("name", "")
    if not name:
        items = meal.get("items", [])
        name = items[0].get("name", "") if items else ""
    return name


def _is_office_day(day: dict) -> bool:
    return day.get("office_day", day.get("weekday") in OFFICE_DAYS)


def _weekday_es(weekday: str) -> str:
    return WEEKDAY_ES.get(weekday, weekday)


# ---------------------------------------------------------------------------
# Ingredient aggregation engine
# ---------------------------------------------------------------------------
_FRACTION_MAP = {
    "\u00bd": 0.5,
    "\u00bc": 0.25,
    "\u00be": 0.75,
    "\u2153": 0.333,
    "\u2154": 0.667,
}

_QTY_RE = re.compile(r"^([\d\u00bc\u00bd\u00be\u2153\u2154]+(?:[.,]\d+)?)\s*(.*)$")


def _parse_quantity(qty_str: str) -> tuple[float | None, str]:
    """Parse a quantity string into (amount, unit).

    Examples:
        "250g"         → (250.0, "g")
        "2 rebanadas"  → (2.0, "rebanadas")
        "1 mediano"    → (1.0, "mediano")
        "½ cdta"       → (0.5, "cdta")
        "2"            → (2.0, "unidad")
        "1 lata (120g)"→ (1.0, "lata (120g)")
    """
    s = qty_str.strip()
    if not s:
        return None, qty_str

    # Handle leading fraction character (½, ¼, etc.)
    if s[0] in _FRACTION_MAP:
        amount = _FRACTION_MAP[s[0]]
        rest = s[1:].strip()
        if rest:
            return amount, rest
        return amount, "unidad"

    m = _QTY_RE.match(s)
    if not m:
        return None, qty_str

    num_str = m.group(1).replace(",", ".")
    # Handle fractions embedded in the number part
    for frac_char, frac_val in _FRACTION_MAP.items():
        if frac_char in num_str:
            parts = num_str.split(frac_char)
            whole = float(parts[0]) if parts[0] else 0
            amount = whole + frac_val
            unit = m.group(2).strip() or "unidad"
            return amount, unit

    try:
        amount = float(num_str)
    except ValueError:
        return None, qty_str

    unit = m.group(2).strip() or "unidad"
    return amount, unit


def _aggregate_ingredients(plan: dict) -> dict[str, str]:
    """Aggregate ingredients across a weekly plan, skipping Factor/free dinners.

    Returns dict mapping ingredient name → aggregated quantity string.
    """
    totals: dict[str, list[tuple[float | None, str]]] = defaultdict(list)

    for day in plan.get("days", []):
        for slot_id, meal in day.get("meals", {}).items():
            # Skip Factor and free dinners — those aren't grocery items
            if slot_id == "dinner" and meal.get("source") in ("factor", "free"):
                continue
            for item in meal.get("items", []):
                name = item["name"]
                qty_str = item.get("quantity", "")
                amount, unit = _parse_quantity(qty_str)
                totals[name].append((amount, unit))

    # Sum compatible quantities
    result: dict[str, str] = {}
    for name, entries in sorted(totals.items()):
        by_unit: dict[str, float] = defaultdict(float)
        raw_parts: list[str] = []

        for amount, unit in entries:
            if amount is not None:
                by_unit[unit] += amount
            else:
                raw_parts.append(unit)

        parts: list[str] = []
        for unit, total in sorted(by_unit.items()):
            # Clean up display: show integer if whole number
            if total == int(total):
                parts.append(f"{int(total)} {unit}")
            else:
                parts.append(f"{total:.1f} {unit}")

        parts.extend(raw_parts)
        result[name] = ", ".join(parts) if parts else ""

    return result


# ---------------------------------------------------------------------------
# Week selector (shared across tabs)
# ---------------------------------------------------------------------------
def _render_week_selector():
    """Render the week navigation above tabs. Stores plan in session_state."""
    manifest = load_manifest()

    if not manifest or not manifest.get("plans"):
        st.info("No hay planes disponibles.")
        return None

    plans = sorted(manifest["plans"], key=lambda p: (p["year"], p["week"]))
    # Filter out drafts
    plans = [p for p in plans if not p.get("draft")]
    plan_labels = [f"{p['year']} W{p['week']:02d}" for p in plans]

    if "week_idx" not in st.session_state:
        st.session_state.week_idx = len(plans) - 1

    # Clamp index
    st.session_state.week_idx = max(0, min(st.session_state.week_idx, len(plans) - 1))

    col_prev, col_select, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button(
            "\u25c0",
            disabled=st.session_state.week_idx <= 0,
            use_container_width=True,
            help="Semana anterior",
        ):
            st.session_state.week_idx -= 1
            st.rerun()
    with col_select:
        selected = st.selectbox(
            "Semana",
            options=range(len(plans)),
            index=st.session_state.week_idx,
            format_func=lambda i: plan_labels[i],
            label_visibility="collapsed",
        )
        if selected != st.session_state.week_idx:
            st.session_state.week_idx = selected
            st.rerun()
    with col_next:
        if st.button(
            "\u25b6",
            disabled=st.session_state.week_idx >= len(plans) - 1,
            use_container_width=True,
            help="Semana siguiente",
        ):
            st.session_state.week_idx += 1
            st.rerun()

    entry = plans[st.session_state.week_idx]
    plan = load_plan(entry["file"])
    if not plan:
        st.error(f"No se pudo cargar el plan: {entry['file']}")
        return None

    st.markdown(f"*{entry['start_date']}  \u2192  {entry['end_date']}*")

    st.session_state.current_plan = plan
    st.session_state.current_entry = entry
    return plan


# ---------------------------------------------------------------------------
# Tab: Weekly Menu
# ---------------------------------------------------------------------------
def render_menu_tab():
    plan = st.session_state.get("current_plan")
    if not plan:
        return

    profile = load_profile()
    target = profile["daily_target_kcal"] if profile else 1800

    _render_week_summary(plan, target)
    st.divider()
    for day in plan["days"]:
        _render_day_card(day, target)


def _render_week_summary(plan: dict, target: int):
    """Compact overview: one row per day showing dinner + kcal."""
    rows = []
    for day in plan["days"]:
        dinner = day["meals"].get("dinner", {})
        indicator = calorie_indicator(day["total_kcal"], target)
        is_today = day["date"] == date.today().isoformat()
        weekday = _weekday_es(day["weekday"])[:3]
        if is_today:
            weekday = f"**{weekday}**"

        flags = []
        if _is_office_day(day):
            flags.append("\U0001f3e2")
        source = dinner.get("source")
        if source == "factor":
            flags.append("\U0001f4e6")
        elif source == "free":
            flags.append("\U0001f389")
        elif source == "homemade":
            flags.append("\U0001f373")

        rows.append(
            f"| {weekday} | {_dinner_display_name(day)} "
            f"| {''.join(flags)} "
            f"| {indicator} {day['total_kcal']} |"
        )

    header = "| D\u00eda | Cena | | Kcal |\n|-----|--------|---|------|\n"
    table = header + "\n".join(rows)
    st.markdown(table)
    st.caption(
        "\U0001f3e2 Oficina  \u00b7  "
        "\U0001f4e6 Factor  \u00b7  "
        "\U0001f389 Libre  \u00b7  "
        "\U0001f373 Casero"
    )


def _render_day_card(day: dict, target: int):
    indicator = calorie_indicator(day["total_kcal"], target)
    is_today = day["date"] == date.today().isoformat()
    today_tag = " \u2014 **Hoy**" if is_today else ""
    weekday_es = _weekday_es(day["weekday"])

    flags = []
    if _is_office_day(day):
        flags.append("\U0001f3e2 Oficina")
    if day.get("notes"):
        flags.append(f"\U0001f4dd {day['notes']}")
    sep = "  \u00b7  "
    flag_str = f"  \u00b7  {sep.join(flags)}" if flags else ""

    header = (
        f"{weekday_es}  \u00b7  {day['date']}{today_tag}"
        f"  \u00b7  {indicator} {day['total_kcal']} kcal{flag_str}"
    )

    with st.expander(header, expanded=is_today):
        dinner = day["meals"].get("dinner")
        if dinner:
            _render_dinner_hero(dinner)

        st.divider()

        for slot_id in ["breakfast", "lunch", "snack1", "snack2"]:
            meal = day["meals"].get(slot_id)
            if meal:
                _render_meal_compact(slot_id, meal)


def _render_dinner_hero(meal: dict):
    """Render dinner prominently — it drives the rest of the day's calories."""
    name = _meal_display_name(meal)
    if not name:
        name = "Cena"
    source = meal.get("source", "")
    badge = SOURCE_LABELS.get(source, "")

    st.markdown(f"### \U0001f37d\ufe0f {name}")

    col_info, col_kcal = st.columns([3, 1])
    with col_info:
        parts = [f"**{badge}**"] if badge else []
        parts.append(meal["time"])
        st.markdown("  \u00b7  ".join(parts))
    with col_kcal:
        st.markdown(f"### {meal['total_kcal']}")
        st.caption("kcal")

    items = meal.get("items", [])
    if source != "factor" and len(items) > 1:
        with st.expander("Ingredientes", expanded=False):
            for item in items:
                st.caption(
                    f"\u2022 {item['name']}  \u00b7  "
                    f"{item['quantity']}  \u00b7  "
                    f"{item['kcal']} kcal"
                )


def _render_meal_compact(slot_id: str, meal: dict):
    """Render breakfast/lunch/snacks: meal name visible, ingredients expandable."""
    icon = MEAL_ICONS.get(slot_id, "")
    label = MEAL_LABELS.get(slot_id, slot_id)
    portable = "  \U0001f4bc" if meal.get("portable") else ""
    meal_name = _meal_display_name(meal)

    col_meal, col_kcal = st.columns([5, 1])
    with col_meal:
        if meal_name:
            st.markdown(f"{icon} **{label}**  \u2014  {meal_name}{portable}")
        else:
            st.markdown(f"{icon} **{label}**{portable}")
    with col_kcal:
        st.markdown(f"**{meal['total_kcal']}** kcal")

    items = meal.get("items", [])
    if len(items) > 1:
        with st.expander("Ingredientes", expanded=False):
            for item in items:
                st.caption(
                    f"\u2022 {item['name']}  \u00b7  "
                    f"{item['quantity']}  \u00b7  "
                    f"{item['kcal']} kcal"
                )
    elif len(items) == 1:
        st.caption(f"  {items[0]['quantity']}  \u00b7  {items[0]['kcal']} kcal")


# ---------------------------------------------------------------------------
# Tab: Grocery List
# ---------------------------------------------------------------------------
def render_grocery_tab():
    plan = st.session_state.get("current_plan")
    if not plan:
        return

    ingredients = _aggregate_ingredients(plan)
    if not ingredients:
        st.info("No hay ingredientes para esta semana.")
        return

    categories_map = load_ingredient_categories()
    products = load_products()
    stock = load_stock()
    has_stock = bool(stock)

    # Group by category
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for name, qty in ingredients.items():
        cat = categories_map.get(name, "otros")
        grouped[cat].append((name, qty))

    # Stock filter toggle
    if has_stock:
        total_items = len(ingredients)
        in_stock_count = sum(1 for name in ingredients if name in stock)
        missing_count = total_items - in_stock_count
        st.markdown(
            f"**{in_stock_count}** de **{total_items}** ingredientes en casa. "
            f"Faltan **{missing_count}**."
        )
        show_all = st.toggle("Mostrar todo", value=False)
    else:
        show_all = True

    st.markdown(f"**{len(ingredients)}** ingredientes para esta semana")

    # Render by category
    for cat in CATEGORY_ORDER:
        items = grouped.get(cat)
        if not items:
            continue

        # Filter out stocked items if toggle is off
        if has_stock and not show_all:
            items = [(n, q) for n, q in items if n not in stock]
            if not items:
                continue

        cat_label = CATEGORY_LABELS.get(cat, cat)
        st.markdown(f"#### {cat_label}")

        for name, qty in sorted(items):
            in_stock = has_stock and name in stock
            product = products.get(name)

            # Build display line
            line = f"\u2705 ~~{name}~~" if in_stock else f"\u2b1c {name}"

            if qty:
                line += f"  \u00b7  {qty}"

            if product:
                ah_name = product.get("ah_product", "")
                ah_url = product.get("ah_url", "")
                price = product.get("price_eur")
                extras = []
                if ah_url and ah_name:
                    extras.append(f"[{ah_name}]({ah_url})")
                elif ah_name:
                    extras.append(ah_name)
                if price is not None:
                    extras.append(f"\u20ac{price:.2f}")
                if extras:
                    sep = " \u00b7 ".join(extras)
                    line += f"  \u00b7  {sep}"

            st.markdown(line)


# ---------------------------------------------------------------------------
# Tab: Weight Progress
# ---------------------------------------------------------------------------
def render_weight_tab():
    profile = load_profile()
    weight_data = load_weight()

    if not weight_data:
        st.info("No hay datos de peso.")
        return

    if not profile:
        st.warning("Perfil no encontrado.")
        return

    _render_weight_stats(weight_data, profile)
    _render_weight_chart(weight_data, profile)


def _render_weight_stats(weight_data: list, profile: dict):
    start_w = weight_data[0]["weight_kg"]
    current_w = weight_data[-1]["weight_kg"]
    goal = profile["goal_weight_kg"]
    lost = start_w - current_w
    remaining = current_w - goal
    total_to_lose = start_w - goal
    pct = (lost / total_to_lose * 100) if total_to_lose > 0 else 0

    start_date = datetime.fromisoformat(weight_data[0]["date"])
    current_date = datetime.fromisoformat(weight_data[-1]["date"])
    weeks_elapsed = max(1, (current_date - start_date).days / 7)
    weekly_rate = lost / weeks_elapsed

    if weekly_rate > 0 and remaining > 0:
        weeks_remaining = remaining / weekly_rate
        eta_date = current_date + timedelta(weeks=weeks_remaining)
        eta_text = eta_date.strftime("%B %Y")
    else:
        eta_text = "N/A"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Inicio", f"{start_w:.1f} kg")
    col2.metric("Actual", f"{current_w:.1f} kg", f"{-lost:.1f} kg")
    col3.metric("Meta", f"{goal} kg")
    col4.metric("Restante", f"{remaining:.1f} kg")

    st.progress(min(pct / 100, 1.0), text=f"{pct:.0f}% completado")
    st.caption(f"Promedio: **{weekly_rate:.2f} kg/semana**  \u00b7  Meta estimada: **{eta_text}**")


def _render_weight_chart(weight_data: list, profile: dict):
    dates = [e["date"] for e in weight_data]
    weights = [e["weight_kg"] for e in weight_data]
    goal = profile["goal_weight_kg"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=weights,
            mode="lines+markers",
            name="Peso",
            line={"color": "#818cf8", "width": 2.5},
            marker={"size": 7},
            fill="tozeroy",
            fillcolor="rgba(129, 140, 248, 0.12)",
        )
    )
    fig.add_hline(
        y=goal,
        line_dash="dash",
        line_color="#10b981",
        annotation_text=f"Meta: {goal} kg",
        annotation_position="top left",
    )
    fig.update_layout(
        yaxis_title="kg",
        xaxis_title="",
        height=350,
        margin={"t": 20, "b": 40, "l": 50, "r": 20},
        yaxis={
            "range": [goal - 3, max(weights) + 2],
            "gridcolor": "#334155",
            "color": "#94a3b8",
        },
        xaxis={"gridcolor": "#334155", "color": "#94a3b8"},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "font": {"color": "#94a3b8"},
        },
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab: Budget
# ---------------------------------------------------------------------------
def render_budget_tab():
    profile = load_profile()
    spending = load_spending()
    weight_data = load_weight()

    if not spending:
        st.info(
            "No hay datos de gasto a\u00fan. "
            "A\u00f1ade datos en `data/spending.json` o configura `SPENDING_SHEET_URL`."
        )
        return

    factor_weekly = profile.get("factor_weekly_eur", 62.93) if profile else 62.93
    budget_weekly = profile.get("budget_weekly_eur", 120) if profile else 120

    # Compute totals
    total_factor = sum(e.get("factor_eur") or 0 for e in spending)
    total_grocery = sum(e.get("grocery_eur") or 0 for e in spending)
    total_spent = total_factor + total_grocery
    weeks_with_data = len(spending)
    avg_weekly = total_spent / weeks_with_data if weeks_with_data else 0

    # Cost per kg lost
    cost_per_kg = None
    if weight_data and len(weight_data) >= 2:
        lost = weight_data[0]["weight_kg"] - weight_data[-1]["weight_kg"]
        if lost > 0:
            cost_per_kg = total_spent / lost

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total gastado", f"\u20ac{total_spent:.0f}")
    col2.metric("Promedio semanal", f"\u20ac{avg_weekly:.0f}")

    # Current week spending
    current_entry = spending[-1] if spending else None
    if current_entry:
        week_total = (current_entry.get("factor_eur") or 0) + (
            current_entry.get("grocery_eur") or 0
        )
        col3.metric("Esta semana", f"\u20ac{week_total:.0f}")
    else:
        col3.metric("Esta semana", "\u2014")

    if cost_per_kg is not None:
        col4.metric("Costo / kg perdido", f"\u20ac{cost_per_kg:.0f}")
    else:
        col4.metric("Costo / kg perdido", "\u2014")

    # Stacked bar chart
    weeks_labels = [f"W{e['week']:02d}" for e in spending]
    factor_vals = [e.get("factor_eur") or 0 for e in spending]
    grocery_vals = [e.get("grocery_eur") or 0 for e in spending]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=weeks_labels,
            y=factor_vals,
            name="Factor",
            marker_color="#818cf8",
        )
    )
    fig.add_trace(
        go.Bar(
            x=weeks_labels,
            y=grocery_vals,
            name="Supermercado",
            marker_color="#34d399",
        )
    )
    fig.add_hline(
        y=budget_weekly,
        line_dash="dash",
        line_color="#f59e0b",
        annotation_text=f"Presupuesto: \u20ac{budget_weekly}",
        annotation_position="top left",
    )
    fig.update_layout(
        barmode="stack",
        yaxis_title="\u20ac",
        xaxis_title="",
        height=350,
        margin={"t": 20, "b": 40, "l": 50, "r": 20},
        yaxis={"gridcolor": "#334155", "color": "#94a3b8"},
        xaxis={"color": "#94a3b8"},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "font": {"color": "#94a3b8"},
        },
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
    )

    st.plotly_chart(fig, use_container_width=True)

    # Factor breakdown
    st.markdown("#### \U0001f4e6 Factor")
    factor_meals_week = 6
    cost_per_meal = factor_weekly / factor_meals_week
    st.caption(
        f"**{factor_meals_week} comidas/semana**  \u00b7  "
        f"\u20ac{cost_per_meal:.2f}/comida  \u00b7  "
        f"\u20ac{factor_weekly:.2f}/semana  \u00b7  "
        f"Total: \u20ac{total_factor:.0f}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.markdown("## \U0001f37d\ufe0f Planificador de Comidas")
    st.caption("1,800 kcal  \u00b7  5 comidas/d\u00eda")

    # Week selector — shared across tabs
    plan = _render_week_selector()
    if not plan:
        return

    tab_menu, tab_grocery, tab_weight, tab_budget = st.tabs(
        [
            "\U0001f4cb Men\u00fa Semanal",
            "\U0001f6d2 Lista de Compras",
            "\u2696\ufe0f Peso",
            "\U0001f4b0 Presupuesto",
        ]
    )

    with tab_menu:
        render_menu_tab()

    with tab_grocery:
        render_grocery_tab()

    with tab_weight:
        render_weight_tab()

    with tab_budget:
        render_budget_tab()


if __name__ == "__main__":
    main()
