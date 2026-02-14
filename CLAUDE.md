# API-to-Enterprise Conversion Intelligence Dashboard

A Streamlit web app that simulates a unified view of customer footprint across Anthropic's
sales channels, surfacing enterprise conversion opportunities through composite scoring.

## Business Context

Anthropic sells through 4+ channels (direct API, AWS Bedrock, GCP Vertex AI, seat-based
products) but has no unified view of a customer's total footprint. This dashboard solves
that by aggregating cross-channel usage data and scoring accounts for enterprise readiness.

## Architecture

```
app.py                        # Streamlit entry point + Anthropic-themed CSS
data/generator.py             # Simulated data generation (~50 accounts, seeded)
analytics/signals.py          # Signal computation (growth, prod ratio, etc.)
analytics/scoring.py          # Weighted composite scoring (0-100)
components/overview.py        # Executive dashboard tab
components/conversion_pipeline.py  # Ranked conversion pipeline tab
components/account_detail.py  # Individual account deep-dive tab
components/cross_channel.py   # Cross-channel footprint tab
```

## Scoring Model

Weighted composite score (0-100):
- Usage Intensity & Growth: 30%
- Production Maturity: 25%
- Team Adoption: 20%
- Cross-Channel Footprint: 15%
- Risk Adjustment: -10% max penalty

Stages: Enterprise Ready (78-100), High Velocity (63-77), Qualified (48-62),
Nurture (33-47), At Risk (<33)

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tech Stack

- Python 3.10+
- Streamlit (web framework)
- Pandas (data manipulation)
- Plotly (interactive charts)
- Faker (realistic company data)
- NumPy (numerical computation)
