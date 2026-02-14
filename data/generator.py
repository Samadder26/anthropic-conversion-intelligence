"""
Simulated data generator for ~50 Anthropic customer accounts.

Generates realistic cross-channel usage data including:
- Company profiles with industry and signup dates
- Monthly time series (12 months) across Direct API, Bedrock, Vertex AI
- Seat-based product usage (Claude for Enterprise, Claude Code)
- Behavioral signals (models used, prod/test ratio, error rates, etc.)

All randomness is seeded for reproducibility.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

SEED = 42
fake = Faker()
Faker.seed(SEED)
np.random.seed(SEED)

INDUSTRIES = [
    "Financial Services", "Healthcare", "Technology", "E-commerce",
    "Media & Entertainment", "Education", "Legal", "Manufacturing",
    "Real Estate", "Consulting", "Insurance", "Logistics",
    "Telecommunications", "Government", "Energy",
]

MODELS = [
    "claude-3-opus", "claude-3.5-sonnet", "claude-3-haiku",
    "claude-3.5-haiku", "claude-3.5-opus",
]

# Account archetypes control the distribution of scoring outcomes
ARCHETYPES = {
    "enterprise_ready": {
        "count": 5,
        "spend_range": (30_000, 80_000),
        "growth_range": (0.15, 0.50),
        "prod_ratio_range": (0.85, 0.98),
        "error_rate_range": (0.005, 0.02),
        "models_range": (3, 5),
        "users_range": (8, 25),
        "channels": [2, 3, 4],
        "enterprise_seats_range": (50, 300),
        "code_licenses_range": (10, 100),
        "inactive_days_range": (0, 1),
    },
    "high_velocity": {
        "count": 10,
        "spend_range": (15_000, 45_000),
        "growth_range": (0.20, 0.60),
        "prod_ratio_range": (0.70, 0.92),
        "error_rate_range": (0.01, 0.035),
        "models_range": (2, 4),
        "users_range": (5, 15),
        "channels": [1, 2, 3],
        "enterprise_seats_range": (0, 100),
        "code_licenses_range": (0, 50),
        "inactive_days_range": (0, 3),
    },
    "qualified": {
        "count": 15,
        "spend_range": (5_000, 25_000),
        "growth_range": (0.05, 0.30),
        "prod_ratio_range": (0.50, 0.80),
        "error_rate_range": (0.015, 0.04),
        "models_range": (1, 3),
        "users_range": (3, 10),
        "channels": [1, 2],
        "enterprise_seats_range": (0, 30),
        "code_licenses_range": (0, 20),
        "inactive_days_range": (0, 5),
    },
    "nurture": {
        "count": 12,
        "spend_range": (2_000, 12_000),
        "growth_range": (-0.05, 0.20),
        "prod_ratio_range": (0.40, 0.65),
        "error_rate_range": (0.015, 0.05),
        "models_range": (1, 2),
        "users_range": (2, 6),
        "channels": [1, 1, 2],
        "enterprise_seats_range": (0, 10),
        "code_licenses_range": (0, 5),
        "inactive_days_range": (1, 10),
    },
    "at_risk": {
        "count": 8,
        "spend_range": (500, 5_000),
        "growth_range": (-0.30, 0.0),
        "prod_ratio_range": (0.15, 0.45),
        "error_rate_range": (0.04, 0.10),
        "models_range": (1, 1),
        "users_range": (1, 3),
        "channels": [1],
        "enterprise_seats_range": (0, 0),
        "code_licenses_range": (0, 0),
        "inactive_days_range": (5, 30),
    },
}


def _random_in_range(low, high):
    """Return a random float in [low, high]."""
    return np.random.uniform(low, high)


def _random_int_in_range(low, high):
    """Return a random int in [low, high]."""
    return np.random.randint(low, high + 1)


def _generate_monthly_spend(base_spend: float, growth_rate: float, months: int = 12) -> list[float]:
    """Generate a 12-month spend trajectory with some noise."""
    monthly_growth = (1 + growth_rate) ** (1 / 12) - 1
    spends = []
    current = base_spend / ((1 + monthly_growth) ** (months - 1))  # backdate to get base at end
    current = max(current, 100)  # floor
    for _ in range(months):
        noise = np.random.normal(1.0, 0.08)
        current = max(current * (1 + monthly_growth) * noise, 50)
        spends.append(round(current, 2))
    return spends


def _pick_models(n_models: int) -> list[str]:
    """Pick n_models from available models."""
    n = min(n_models, len(MODELS))
    return list(np.random.choice(MODELS, size=n, replace=False))


def generate_accounts(n_accounts: int = 50) -> dict:
    """
    Generate simulated account data.

    Returns a dict with:
    - accounts_df: DataFrame of account profiles + signals
    - monthly_usage_df: DataFrame of monthly time-series usage per account per channel
    """
    accounts = []
    monthly_records = []
    account_id = 1000

    for archetype_name, config in ARCHETYPES.items():
        for _ in range(config["count"]):
            account_id += 1
            company = fake.company()
            domain = fake.domain_name()

            # Signup date: 3-24 months ago
            signup_days_ago = np.random.randint(90, 730)
            signup_date = datetime.now() - timedelta(days=signup_days_ago)

            industry = np.random.choice(INDUSTRIES)

            # Channel usage
            n_channels = np.random.choice(config["channels"])
            base_spend = _random_in_range(*config["spend_range"])
            growth_rate = _random_in_range(*config["growth_range"])

            # Distribute spend across channels
            has_direct = True  # all accounts have direct API
            has_bedrock = n_channels >= 2
            has_vertex = n_channels >= 3
            has_seats = n_channels >= 4 or config["enterprise_seats_range"][1] > 0

            # Spend split ratios
            if n_channels == 1:
                direct_pct = 1.0
                bedrock_pct = 0.0
                vertex_pct = 0.0
            elif n_channels == 2:
                direct_pct = _random_in_range(0.3, 0.7)
                bedrock_pct = 1.0 - direct_pct
                vertex_pct = 0.0
            elif n_channels == 3:
                direct_pct = _random_in_range(0.2, 0.5)
                bedrock_pct = _random_in_range(0.2, 1.0 - direct_pct)
                vertex_pct = 1.0 - direct_pct - bedrock_pct
            else:
                direct_pct = _random_in_range(0.2, 0.4)
                bedrock_pct = _random_in_range(0.15, 0.35)
                vertex_pct = _random_in_range(0.1, max(0.11, 1.0 - direct_pct - bedrock_pct - 0.1))
                vertex_pct = min(vertex_pct, 1.0 - direct_pct - bedrock_pct)

            # Generate monthly time series
            direct_monthly = _generate_monthly_spend(base_spend * direct_pct, growth_rate)
            bedrock_monthly = (
                _generate_monthly_spend(base_spend * bedrock_pct, growth_rate * _random_in_range(0.7, 1.3))
                if has_bedrock else [0.0] * 12
            )
            vertex_monthly = (
                _generate_monthly_spend(base_spend * vertex_pct, growth_rate * _random_in_range(0.7, 1.3))
                if has_vertex else [0.0] * 12
            )

            # Seat-based products
            enterprise_seats = _random_int_in_range(*config["enterprise_seats_range"])
            code_licenses = _random_int_in_range(*config["code_licenses_range"])
            seat_spend_monthly = enterprise_seats * 30 + code_licenses * 19  # $/seat/mo estimates

            # Behavioral signals
            prod_ratio = round(_random_in_range(*config["prod_ratio_range"]), 3)
            error_rate = round(_random_in_range(*config["error_rate_range"]), 4)
            n_models = _random_int_in_range(*config["models_range"])
            models_used = _pick_models(n_models)
            unique_users = _random_int_in_range(*config["users_range"])
            days_inactive = _random_int_in_range(*config["inactive_days_range"])

            # Requests (roughly proportional to spend, ~$0.01-0.05 per request)
            cost_per_request = _random_in_range(0.01, 0.05)
            latest_total_spend = direct_monthly[-1] + bedrock_monthly[-1] + vertex_monthly[-1]
            daily_requests = int(latest_total_spend / cost_per_request / 30)

            # Marketplace-to-direct ratio (for "hidden account" detection)
            marketplace_spend = bedrock_monthly[-1] + vertex_monthly[-1]
            direct_spend = direct_monthly[-1]
            marketplace_to_direct = (
                round(marketplace_spend / direct_spend, 2) if direct_spend > 0 else 99.0
            )

            total_spend = sum(direct_monthly) + sum(bedrock_monthly) + sum(vertex_monthly) + seat_spend_monthly * 12

            accounts.append({
                "account_id": f"ACC-{account_id}",
                "company": company,
                "domain": domain,
                "industry": industry,
                "signup_date": signup_date.strftime("%Y-%m-%d"),
                "archetype": archetype_name,
                "n_channels": n_channels,
                "has_direct": has_direct,
                "has_bedrock": has_bedrock,
                "has_vertex": has_vertex,
                "enterprise_seats": enterprise_seats,
                "code_licenses": code_licenses,
                "latest_direct_spend": round(direct_monthly[-1], 2),
                "latest_bedrock_spend": round(bedrock_monthly[-1], 2),
                "latest_vertex_spend": round(vertex_monthly[-1], 2),
                "latest_seat_spend": round(seat_spend_monthly, 2),
                "latest_total_spend": round(
                    direct_monthly[-1] + bedrock_monthly[-1] + vertex_monthly[-1] + seat_spend_monthly, 2
                ),
                "total_12mo_spend": round(total_spend, 2),
                "growth_rate": round(growth_rate, 4),
                "prod_ratio": prod_ratio,
                "error_rate": error_rate,
                "models_used": models_used,
                "n_models": n_models,
                "unique_users": unique_users,
                "daily_requests": daily_requests,
                "days_inactive": days_inactive,
                "marketplace_to_direct": marketplace_to_direct,
            })

            # Monthly time series records
            base_date = datetime.now().replace(day=1)
            for month_idx in range(12):
                month_date = base_date - timedelta(days=30 * (11 - month_idx))
                month_str = month_date.strftime("%Y-%m")

                for channel, spend_list in [
                    ("Direct API", direct_monthly),
                    ("AWS Bedrock", bedrock_monthly),
                    ("GCP Vertex AI", vertex_monthly),
                ]:
                    if spend_list[month_idx] > 0:
                        requests = int(spend_list[month_idx] / cost_per_request)
                        monthly_records.append({
                            "account_id": f"ACC-{account_id}",
                            "company": company,
                            "month": month_str,
                            "month_idx": month_idx,
                            "channel": channel,
                            "spend": round(spend_list[month_idx], 2),
                            "requests": requests,
                        })

                # Seat spend as a channel
                if seat_spend_monthly > 0:
                    monthly_records.append({
                        "account_id": f"ACC-{account_id}",
                        "company": company,
                        "month": month_str,
                        "month_idx": month_idx,
                        "channel": "Seat-Based",
                        "spend": round(seat_spend_monthly, 2),
                        "requests": enterprise_seats + code_licenses,
                    })

    accounts_df = pd.DataFrame(accounts)
    monthly_usage_df = pd.DataFrame(monthly_records)

    return {
        "accounts": accounts_df,
        "monthly_usage": monthly_usage_df,
    }
