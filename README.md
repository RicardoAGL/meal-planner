# Meal Planner

Streamlit dashboard for tracking weekly meal plans and weight progress. Built for a structured 1,800 kcal/day plan with [Factor](https://www.hellofactor.nl/) meal delivery for dinners.

## Features

- **Weekly menu view** — Expandable day cards with meals, calorie totals, and color-coded status
- **Weight progress chart** — Interactive Plotly chart with goal line, stats, and estimated completion
- **Mobile-friendly** — Works on phone browsers, shareable URL
- **CLI-driven** — Weekly plans generated as JSON via Claude Code

## Setup

```bash
uv sync
uv run streamlit run app.py
```

## Development

```bash
# Install pre-commit hooks
uv run pre-commit install

# Lint
uv run ruff check .
uv run ruff format .
```

## Generate a New Weekly Plan

Use Claude Code in this repository:

```
"Here are my Factor meals for next week: [list meals with calories].
Generate the W08 plan."
```

Claude Code follows the rules in `CLAUDE.md` to generate the JSON plan file.

## Add a Weight Entry

```
"Add weight entry: 2026-02-15, 101.0 kg"
```

## Deployment

Hosted on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select this repo → branch `main` → file `app.py`
4. Deploy — the app gets a public URL (e.g. `https://meal-planner.streamlit.app`)

Auto-redeploys on every push to `main`.
