"""
Enterprise Conversion Readiness Scoring Engine.

Weighted composite score (0-100) with 5 categories:
- Usage Intensity & Growth: 30%
- Production Maturity: 25%
- Team Adoption: 20%
- Cross-Channel Footprint: 15%
- Risk Adjustment: -10% max penalty

Stage mapping:
- 85-100: Enterprise Ready
- 70-84:  High Velocity
- 55-69:  Qualified
- 40-54:  Nurture
- <40:    At Risk
"""

import numpy as np
import pandas as pd


STAGE_THRESHOLDS = [
    (78, "Enterprise Ready"),
    (63, "High Velocity"),
    (48, "Qualified"),
    (33, "Nurture"),
    (0, "At Risk"),
]

STAGE_COLORS = {
    "Enterprise Ready": "#2E7D32",
    "High Velocity": "#1565C0",
    "Qualified": "#F57F17",
    "Nurture": "#8E24AA",
    "At Risk": "#C62828",
}


def _normalize_spend_log(spend: float, max_spend: float = 80_000) -> float:
    """Normalize spend on log scale to 0-100."""
    if spend <= 0:
        return 0.0
    log_val = np.log10(max(spend, 1))
    log_max = np.log10(max_spend)
    log_min = np.log10(500)  # floor
    return min(100, max(0, (log_val - log_min) / (log_max - log_min) * 100))


def _score_growth(growth_rate: float) -> float:
    """Score growth rate: 50%+ = 100, 20-50% = partial, negative = penalty."""
    if growth_rate >= 0.50:
        return 100.0
    elif growth_rate >= 0.20:
        return 40 + (growth_rate - 0.20) / 0.30 * 60
    elif growth_rate >= 0.0:
        return growth_rate / 0.20 * 40
    else:
        return max(0, 20 + growth_rate * 100)  # penalty for negative growth


def _score_daily_requests(daily_requests: int) -> float:
    """Normalize daily requests on log scale."""
    if daily_requests <= 0:
        return 0.0
    log_val = np.log10(max(daily_requests, 1))
    return min(100, max(0, log_val / np.log10(100_000) * 100))


def _score_prod_ratio(prod_ratio: float) -> float:
    """Linear scale: 95% = 100, below 40% = near zero."""
    if prod_ratio >= 0.95:
        return 100.0
    elif prod_ratio >= 0.40:
        return (prod_ratio - 0.40) / 0.55 * 100
    else:
        return prod_ratio / 0.40 * 10  # near zero


def _score_error_rate(error_rate: float) -> float:
    """Sweet spot scoring: 0.5-2% = full points, too low or too high = less."""
    if 0.005 <= error_rate <= 0.02:
        return 100.0
    elif error_rate < 0.005:
        # Too low might mean small scale
        return 50 + error_rate / 0.005 * 50
    elif error_rate <= 0.05:
        # Getting high
        return max(0, 100 - (error_rate - 0.02) / 0.03 * 80)
    else:
        return max(0, 20 - (error_rate - 0.05) / 0.05 * 20)


def _score_model_diversity(n_models: int) -> float:
    """3+ models = 100, 2 = 60, 1 = 20."""
    if n_models >= 3:
        return 100.0
    elif n_models == 2:
        return 60.0
    elif n_models == 1:
        return 20.0
    return 0.0


def _score_domain_users(unique_users: int) -> float:
    """10+ = 100, linear below that."""
    if unique_users >= 10:
        return 100.0
    return unique_users / 10.0 * 100


def _score_enterprise_seats(seats: int) -> float:
    """Bonus multiplier for existing seats."""
    if seats >= 100:
        return 100.0
    elif seats > 0:
        return min(100, seats / 100 * 100)
    return 0.0


def _score_cross_channel(n_channels: int, marketplace_to_direct: float) -> float:
    """Score based on channel diversity and marketplace ratio."""
    channel_score = min(100, (n_channels - 1) * 40)  # 1=0, 2=40, 3=80, 4=100

    # High marketplace-to-direct ratio gets a bonus (hidden account signal)
    if marketplace_to_direct > 3.0:
        channel_score = min(100, channel_score + 20)

    return channel_score


def _compute_risk_penalty(days_inactive: int, growth_rate: float, n_models: int) -> float:
    """
    Risk adjustment: returns a penalty value between 0 and 10.
    """
    penalty = 0.0

    # Days inactive penalty
    if days_inactive > 14:
        penalty += 4.0
    elif days_inactive > 7:
        penalty += (days_inactive - 7) / 7.0 * 4.0

    # Negative growth penalty
    if growth_rate < 0:
        penalty += min(4.0, abs(growth_rate) * 20)

    # Single model penalty
    if n_models <= 1:
        penalty += 2.0

    return min(10.0, penalty)


def score_account(row: pd.Series) -> dict:
    """
    Score a single account and return category breakdowns.

    Args:
        row: A pandas Series with account data + computed signals.

    Returns:
        Dict with total score, stage, and category breakdowns.
    """
    # 1. Usage Intensity & Growth (30%)
    spend_score = _normalize_spend_log(row["latest_total_spend"])
    growth_score = _score_growth(row.get("computed_growth_rate", row.get("growth_rate", 0)))
    request_score = _score_daily_requests(row["daily_requests"])
    usage_intensity = (spend_score * 0.4 + growth_score * 0.4 + request_score * 0.2)

    # 2. Production Maturity (25%)
    prod_score = _score_prod_ratio(row["prod_ratio"])
    error_score = _score_error_rate(row["error_rate"])
    model_score = _score_model_diversity(row["n_models"])
    production_maturity = (prod_score * 0.4 + error_score * 0.3 + model_score * 0.3)

    # 3. Team Adoption (20%)
    users_score = _score_domain_users(row["unique_users"])
    seats_score = _score_enterprise_seats(row["enterprise_seats"])
    team_adoption = (users_score * 0.6 + seats_score * 0.4)

    # 4. Cross-Channel Footprint (15%)
    n_channels = row.get("n_active_channels", row.get("n_channels", 1))
    cross_channel = _score_cross_channel(n_channels, row["marketplace_to_direct"])

    # 5. Risk Adjustment (-10% max)
    risk_penalty = _compute_risk_penalty(
        row["days_inactive"],
        row.get("computed_growth_rate", row.get("growth_rate", 0)),
        row["n_models"],
    )

    # Composite score
    raw_score = (
        usage_intensity * 0.30
        + production_maturity * 0.25
        + team_adoption * 0.20
        + cross_channel * 0.15
    )
    total_score = max(0, min(100, raw_score - risk_penalty))

    # Stage assignment
    stage = "At Risk"
    for threshold, stage_name in STAGE_THRESHOLDS:
        if total_score >= threshold:
            stage = stage_name
            break

    return {
        "conversion_score": round(total_score, 1),
        "stage": stage,
        "usage_intensity_score": round(usage_intensity, 1),
        "production_maturity_score": round(production_maturity, 1),
        "team_adoption_score": round(team_adoption, 1),
        "cross_channel_score": round(cross_channel, 1),
        "risk_penalty": round(risk_penalty, 1),
    }


def score_all_accounts(enriched_df: pd.DataFrame) -> pd.DataFrame:
    """
    Score all accounts and merge scores back into the DataFrame.
    """
    score_records = []
    for _, row in enriched_df.iterrows():
        scores = score_account(row)
        scores["account_id"] = row["account_id"]
        score_records.append(scores)

    scores_df = pd.DataFrame(score_records)
    return enriched_df.merge(scores_df, on="account_id", how="left")


def get_recommended_action(row: pd.Series) -> str:
    """Return a recommended next action based on account stage and signals."""
    stage = row["stage"]
    if stage == "Enterprise Ready":
        return "Route to AE for enterprise contract discussion"
    elif stage == "High Velocity":
        if row["enterprise_seats"] == 0:
            return "Introduce Claude for Enterprise; schedule product demo"
        return "Monitor for trigger event; prepare custom pricing proposal"
    elif stage == "Qualified":
        if row["n_models"] <= 1:
            return "Share multi-model use case guide; suggest Sonnet for cost optimization"
        if row["prod_ratio"] < 0.6:
            return "Offer production deployment support; share best practices"
        return "Assign SDR for discovery call; share enterprise case studies"
    elif stage == "Nurture":
        if row.get("computed_growth_rate", row.get("growth_rate", 0)) < 0:
            return "Trigger re-engagement campaign; offer office hours"
        return "Add to nurture sequence; share relevant content"
    else:  # At Risk
        if row["days_inactive"] > 14:
            return "CSM outreach: check-in call to understand blockers"
        return "CSM intervention: identify churn risk factors"


def get_action_explanation(row: pd.Series) -> str:
    """Return a brief WHY explanation based on the score breakdown."""
    parts = []
    stage = row["stage"]

    # Identify strongest and weakest scoring categories
    categories = {
        "Usage Intensity": row["usage_intensity_score"],
        "Production Maturity": row["production_maturity_score"],
        "Team Adoption": row["team_adoption_score"],
        "Cross-Channel": row["cross_channel_score"],
    }
    strongest = max(categories, key=categories.get)
    weakest = min(categories, key=categories.get)

    if stage == "Enterprise Ready":
        parts.append(f"Strong across all dimensions (strongest: {strongest} at {categories[strongest]:.0f}/100).")
        parts.append("High spend, multi-channel presence, and strong team adoption signal enterprise buying intent.")
    elif stage == "High Velocity":
        parts.append(f"Strongest signal: {strongest} ({categories[strongest]:.0f}/100).")
        if categories[weakest] < 50:
            parts.append(f"Opportunity: {weakest} is at {categories[weakest]:.0f}/100 \u2014 addressing this could accelerate conversion.")
        else:
            parts.append("Approaching enterprise threshold across multiple dimensions.")
    elif stage == "Qualified":
        parts.append(f"{strongest} leads at {categories[strongest]:.0f}/100.")
        parts.append(f"Focus on improving {weakest} ({categories[weakest]:.0f}/100) to move this account up-funnel.")
    elif stage == "Nurture":
        growth = row.get("computed_growth_rate", row.get("growth_rate", 0))
        if growth > 0:
            parts.append(f"Positive growth trajectory ({growth:+.0%}) but early-stage across most signals.")
        else:
            parts.append(f"Flat or declining usage ({growth:+.0%}). Needs re-engagement to prevent churn.")
        parts.append(f"Best signal: {strongest} at {categories[strongest]:.0f}/100.")
    else:
        risk = row["risk_penalty"]
        if row["days_inactive"] > 7:
            parts.append(f"Inactive for {row['days_inactive']} days \u2014 potential churn risk.")
        if row.get("computed_growth_rate", row.get("growth_rate", 0)) < -0.1:
            parts.append("Usage is declining significantly.")
        parts.append(f"All scoring categories are below threshold (best: {strongest} at {categories[strongest]:.0f}/100).")

    return " ".join(parts)
