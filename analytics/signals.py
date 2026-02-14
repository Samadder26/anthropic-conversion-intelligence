"""
Signal computation functions for enterprise conversion scoring.

Each function takes account-level data and returns a normalized signal value.
"""

import numpy as np
import pandas as pd


def compute_growth_rate(monthly_usage_df: pd.DataFrame, account_id: str) -> float:
    """
    Compute month-over-month spend growth rate for an account.
    Returns the average MoM growth over the last 3 months.
    """
    account_data = monthly_usage_df[monthly_usage_df["account_id"] == account_id]
    if account_data.empty:
        return 0.0

    monthly_totals = (
        account_data.groupby("month_idx")["spend"]
        .sum()
        .sort_index()
    )

    if len(monthly_totals) < 2:
        return 0.0

    # Use last 3 months for recent growth signal
    recent = monthly_totals.tail(4)
    growth_rates = recent.pct_change().dropna()

    if growth_rates.empty:
        return 0.0

    # Annualize the MoM growth rate so scoring thresholds work correctly
    avg_mom = float(growth_rates.mean())
    annualized = (1 + avg_mom) ** 12 - 1
    return annualized


def compute_production_ratio(accounts_df: pd.DataFrame, account_id: str) -> float:
    """Return the production traffic ratio for an account."""
    row = accounts_df[accounts_df["account_id"] == account_id]
    if row.empty:
        return 0.0
    return float(row.iloc[0]["prod_ratio"])


def compute_model_diversity(accounts_df: pd.DataFrame, account_id: str) -> int:
    """Return the number of distinct models used by an account."""
    row = accounts_df[accounts_df["account_id"] == account_id]
    if row.empty:
        return 0
    return int(row.iloc[0]["n_models"])


def compute_domain_users(accounts_df: pd.DataFrame, account_id: str) -> int:
    """Return the number of unique users from the same domain."""
    row = accounts_df[accounts_df["account_id"] == account_id]
    if row.empty:
        return 0
    return int(row.iloc[0]["unique_users"])


def compute_cross_channel_spend(accounts_df: pd.DataFrame, account_id: str) -> dict:
    """
    Return a breakdown of spend across channels for an account.
    """
    row = accounts_df[accounts_df["account_id"] == account_id]
    if row.empty:
        return {"direct": 0, "bedrock": 0, "vertex": 0, "seats": 0, "total": 0}

    r = row.iloc[0]
    return {
        "direct": float(r["latest_direct_spend"]),
        "bedrock": float(r["latest_bedrock_spend"]),
        "vertex": float(r["latest_vertex_spend"]),
        "seats": float(r["latest_seat_spend"]),
        "total": float(r["latest_total_spend"]),
    }


def compute_days_inactive(accounts_df: pd.DataFrame, account_id: str) -> int:
    """Return the number of days since last API activity."""
    row = accounts_df[accounts_df["account_id"] == account_id]
    if row.empty:
        return 999
    return int(row.iloc[0]["days_inactive"])


def compute_all_signals(accounts_df: pd.DataFrame, monthly_usage_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all signals for all accounts and return as a DataFrame
    merged with the accounts data.
    """
    signals = []
    for _, row in accounts_df.iterrows():
        aid = row["account_id"]
        growth = compute_growth_rate(monthly_usage_df, aid)
        channel_spend = compute_cross_channel_spend(accounts_df, aid)

        n_active_channels = sum([
            channel_spend["direct"] > 0,
            channel_spend["bedrock"] > 0,
            channel_spend["vertex"] > 0,
            channel_spend["seats"] > 0,
        ])

        # Blend computed growth with stored growth_rate (70/30 stored/computed)
        # to reduce noise from monthly time series while keeping it data-driven
        stored_growth = float(row["growth_rate"])
        blended_growth = stored_growth * 0.7 + growth * 0.3

        signals.append({
            "account_id": aid,
            "computed_growth_rate": round(blended_growth, 4),
            "n_active_channels": n_active_channels,
            "channel_direct": channel_spend["direct"],
            "channel_bedrock": channel_spend["bedrock"],
            "channel_vertex": channel_spend["vertex"],
            "channel_seats": channel_spend["seats"],
        })

    signals_df = pd.DataFrame(signals)
    return accounts_df.merge(signals_df, on="account_id", how="left")
