"""Meal Planner — Streamlit dashboard for weekly meal plans and weight tracking."""

import json
from datetime import date, datetime, timedelta
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


@st.cache_data
def load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_profile():
    return load_json(DATA_DIR / "profile.json")


def load_weight():
    return load_json(DATA_DIR / "weight.json")


def load_manifest():
    return load_json(DATA_DIR / "plans" / "manifest.json")


def load_plan(file: str):
    return load_json(DATA_DIR / "plans" / file)


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
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "snack1": "Snack 1",
    "snack2": "Snack 2",
    "dinner": "Dinner",
}

SOURCE_LABELS = {
    "factor": "\U0001f4e6 Factor Meal",
    "free": "\U0001f389 Free / Social",
    "homemade": "\U0001f373 Homemade",
}

OFFICE_DAYS = {"Friday"}


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


def _dinner_name(day: dict) -> str:
    """Extract the dinner name from a day object."""
    dinner = day.get("meals", {}).get("dinner", {})
    items = dinner.get("items", [])
    if items:
        name = items[0].get("name", "\u2014")
        return name[:35] + "..." if len(name) > 35 else name
    return "\u2014"


def _is_office_day(day: dict) -> bool:
    return day.get("office_day", day.get("weekday") in OFFICE_DAYS)


# ---------------------------------------------------------------------------
# Tab: Weekly Menu
# ---------------------------------------------------------------------------
def render_menu_tab():
    profile = load_profile()
    manifest = load_manifest()

    if not manifest or not manifest.get("plans"):
        st.info("No meal plans available yet.")
        return

    plans = sorted(manifest["plans"], key=lambda p: (p["year"], p["week"]))
    plan_labels = [f"{p['year']} W{p['week']:02d}" for p in plans]

    if "week_idx" not in st.session_state:
        st.session_state.week_idx = len(plans) - 1

    # Week navigation
    col_prev, col_select, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button(
            "\u25c0",
            disabled=st.session_state.week_idx <= 0,
            use_container_width=True,
            help="Previous week",
        ):
            st.session_state.week_idx -= 1
            st.rerun()
    with col_select:
        selected = st.selectbox(
            "Week",
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
            help="Next week",
        ):
            st.session_state.week_idx += 1
            st.rerun()

    # Load plan
    entry = plans[st.session_state.week_idx]
    plan = load_plan(entry["file"])
    if not plan:
        st.error(f"Could not load plan file: {entry['file']}")
        return

    target = profile["daily_target_kcal"] if profile else 1800

    st.markdown(f"*{entry['start_date']}  \u2192  {entry['end_date']}*")

    # Week-at-a-glance
    _render_week_summary(plan, target)

    st.divider()

    # Day cards
    for day in plan["days"]:
        _render_day_card(day, target)


def _render_week_summary(plan: dict, target: int):
    """Compact overview: one row per day showing dinner + kcal."""
    rows = []
    for day in plan["days"]:
        dinner = day["meals"].get("dinner", {})
        indicator = calorie_indicator(day["total_kcal"], target)
        is_today = day["date"] == date.today().isoformat()
        weekday = day["weekday"][:3]
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
            f"| {weekday} | {_dinner_name(day)} "
            f"| {''.join(flags)} "
            f"| {indicator} {day['total_kcal']} |"
        )

    table = "| Day | Dinner | | Kcal |\n|-----|--------|---|------|\n" + "\n".join(rows)
    st.markdown(table)
    st.caption(
        "\U0001f3e2 Office  \u00b7  "
        "\U0001f4e6 Factor  \u00b7  "
        "\U0001f389 Free  \u00b7  "
        "\U0001f373 Homemade"
    )


def _render_day_card(day: dict, target: int):
    indicator = calorie_indicator(day["total_kcal"], target)
    is_today = day["date"] == date.today().isoformat()
    today_tag = " \u2014 **Today**" if is_today else ""

    flags = []
    if _is_office_day(day):
        flags.append("\U0001f3e2 Office")
    if day.get("notes"):
        flags.append(f"\U0001f4dd {day['notes']}")
    sep = "  \u00b7  "
    flag_str = f"  \u00b7  {sep.join(flags)}" if flags else ""

    header = (
        f"{day['weekday']}  \u00b7  {day['date']}{today_tag}"
        f"  \u00b7  {indicator} {day['total_kcal']} kcal{flag_str}"
    )

    with st.expander(header, expanded=is_today):
        # Dinner first — it's the anchor of the day
        dinner = day["meals"].get("dinner")
        if dinner:
            _render_dinner_hero(dinner)

        st.divider()

        # Other meals — compact, items collapsed
        for slot_id in ["breakfast", "lunch", "snack1", "snack2"]:
            meal = day["meals"].get(slot_id)
            if meal:
                _render_meal_compact(slot_id, meal)


def _render_dinner_hero(meal: dict):
    """Render dinner prominently — it drives the rest of the day's calories."""
    items = meal.get("items", [])
    name = items[0]["name"] if items else "Dinner"
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

    # Show ingredients only for non-Factor meals with multiple items
    if source != "factor" and len(items) > 1:
        with st.expander("Ingredients", expanded=False):
            for item in items:
                st.caption(
                    f"\u2022 {item['name']}  \u00b7  "
                    f"{item['quantity']}  \u00b7  "
                    f"{item['kcal']} kcal"
                )


def _render_meal_compact(slot_id: str, meal: dict):
    """Render breakfast/lunch/snacks: one-line header, items collapsed."""
    icon = MEAL_ICONS.get(slot_id, "")
    label = MEAL_LABELS.get(slot_id, slot_id)
    portable = "  \U0001f4bc" if meal.get("portable") else ""

    col_meal, col_kcal = st.columns([5, 1])
    with col_meal:
        st.markdown(f"{icon} **{label}**{portable}  \u2014  {meal['time']}")
    with col_kcal:
        st.markdown(f"**{meal['total_kcal']}** kcal")

    with st.expander("Items", expanded=False):
        for item in meal["items"]:
            st.caption(
                f"\u2022 {item['name']}  \u00b7  {item['quantity']}  \u00b7  {item['kcal']} kcal"
            )


# ---------------------------------------------------------------------------
# Tab: Weight Progress
# ---------------------------------------------------------------------------
def render_weight_tab():
    profile = load_profile()
    weight_data = load_weight()

    if not weight_data:
        st.info("No weight data yet.")
        return

    if not profile:
        st.warning("Profile not found.")
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
    col1.metric("Start", f"{start_w:.1f} kg")
    col2.metric("Current", f"{current_w:.1f} kg", f"{-lost:.1f} kg")
    col3.metric("Goal", f"{goal} kg")
    col4.metric("Remaining", f"{remaining:.1f} kg")

    st.progress(min(pct / 100, 1.0), text=f"{pct:.0f}% complete")
    st.caption(f"Avg loss: **{weekly_rate:.2f} kg/week**  \u00b7  Est. goal: **{eta_text}**")


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
            name="Weight",
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
        annotation_text=f"Goal: {goal} kg",
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
# Main
# ---------------------------------------------------------------------------
def main():
    st.markdown("## \U0001f37d\ufe0f Meal Planner")
    st.caption("1,800 kcal  \u00b7  5 meals/day")

    tab_menu, tab_weight = st.tabs(["\U0001f4cb This Week", "\u2696\ufe0f Weight"])

    with tab_menu:
        render_menu_tab()

    with tab_weight:
        render_weight_tab()


if __name__ == "__main__":
    main()
