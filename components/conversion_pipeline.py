"""Conversion Pipeline — ranked table with scores, stages, filters, and recommended actions."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from components.styles import (
    score_pill, stage_tag, section_header, alert_card,
    STAGE_COLORS, PLOTLY_LAYOUT,
)
from analytics.scoring import get_recommended_action


def render(scored_df: pd.DataFrame):

    # ── Filters ──
    st.markdown(section_header("Conversion Pipeline", "Filter and rank accounts by enterprise readiness"),
                unsafe_allow_html=True)

    all_stages = ["Enterprise Ready", "High Velocity", "Qualified", "Nurture", "At Risk"]
    industries = sorted(scored_df["industry"].unique())

    f1, f2, f3 = st.columns([1, 1, 1], gap="medium")
    with f1:
        stage_filter = st.multiselect(
            "Stage",
            options=all_stages,
            default=[],
            placeholder="Filter by stage...",
        )
    with f2:
        industry_filter = st.multiselect(
            "Industry",
            options=industries,
            default=[],
            placeholder="Filter by industry...",
        )
    with f3:
        min_score, max_score = st.slider("Score Range", 0, 100, (0, 100))

    # Empty selection = show all
    active_stages = stage_filter if stage_filter else all_stages
    active_industries = industry_filter if industry_filter else list(industries)

    filtered = scored_df[
        (scored_df["stage"].isin(active_stages))
        & (scored_df["industry"].isin(active_industries))
        & (scored_df["conversion_score"] >= min_score)
        & (scored_df["conversion_score"] <= max_score)
    ].copy()

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # ── Score Distribution Histogram ──
    st.markdown(section_header(f"Score Distribution", f"{len(filtered)} accounts"),
                unsafe_allow_html=True)

    stage_order = ["Enterprise Ready", "High Velocity", "Qualified", "Nurture", "At Risk"]
    fig_hist = go.Figure()
    for stage_name in stage_order:
        stage_data = filtered[filtered["stage"] == stage_name]
        if not stage_data.empty:
            fig_hist.add_trace(go.Histogram(
                x=stage_data["conversion_score"],
                name=stage_name,
                marker=dict(
                    color=STAGE_COLORS[stage_name],
                    line=dict(color="#FFFFFF", width=1),
                ),
                xbins=dict(start=0, end=100, size=5),
                hovertemplate=f"<b>{stage_name}</b><br>Score: %{{x}}<br>Count: %{{y}}<extra></extra>",
            ))

    fig_hist.update_layout(
        **PLOTLY_LAYOUT,
        height=200,
        margin=dict(l=10, r=10, t=10, b=30),
        barmode="stack",
        bargap=0.15,
        xaxis=dict(
            title="Conversion Score",
            gridcolor="#E2E8F0",
            range=[0, 100],
            dtick=10,
        ),
        yaxis=dict(title="", gridcolor="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, font=dict(size=11)),
        showlegend=True,
    )
    st.plotly_chart(fig_hist, width="stretch")

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # ── Hidden Accounts Alert ──
    hidden_accounts = filtered[filtered["marketplace_to_direct"] > 3.0]
    if len(hidden_accounts) > 0:
        total_hidden_rev = (hidden_accounts["latest_bedrock_spend"] + hidden_accounts["latest_vertex_spend"]).sum()
        st.markdown(
            alert_card(
                f"{len(hidden_accounts)} Hidden Account(s) Detected",
                f"These accounts have 3x+ marketplace spend vs. direct API, representing "
                f"<strong>${total_hidden_rev:,.0f}/mo</strong> in marketplace revenue. "
                f"They may be significant untapped enterprise opportunities.",
            ),
            unsafe_allow_html=True,
        )

        with st.expander("View hidden account details"):
            hidden_html = _build_hidden_table(hidden_accounts)
            st.markdown(hidden_html, unsafe_allow_html=True)

    # ── Pipeline Table ──
    st.markdown(section_header("All Accounts", "Ranked by conversion score"), unsafe_allow_html=True)

    filtered["recommended_action"] = filtered.apply(get_recommended_action, axis=1)
    display = filtered.sort_values("conversion_score", ascending=False).reset_index(drop=True)

    table_html = '<div class="table-wrapper"><table class="data-table"><thead><tr>'
    table_html += '<th>Company</th><th>Industry</th><th style="text-align:right">Score</th>'
    table_html += '<th>Stage</th><th style="text-align:right">Monthly Spend</th>'
    table_html += '<th style="text-align:right">Growth</th><th style="text-align:right">Models</th>'
    table_html += '<th style="text-align:right">Prod %</th><th style="text-align:right">Users</th>'
    table_html += '<th>Recommended Action</th>'
    table_html += '</tr></thead><tbody>'
    for _, row in display.iterrows():
        growth = row.get("computed_growth_rate", row.get("growth_rate", 0))
        growth_class = "positive" if growth >= 0 else "negative"
        growth_str = f"{growth:+.0%}"
        table_html += (
            f'<tr><td class="company-name">{row["company"]}</td>'
            f'<td class="industry-cell">{row["industry"]}</td>'
            f'<td class="num">{score_pill(row["conversion_score"])}</td>'
            f'<td>{stage_tag(row["stage"])}</td>'
            f'<td class="num">${row["latest_total_spend"]:,.0f}</td>'
            f'<td class="num {growth_class}">{growth_str}</td>'
            f'<td class="num">{row["n_models"]}</td>'
            f'<td class="num">{row["prod_ratio"]:.0%}</td>'
            f'<td class="num">{row["unique_users"]}</td>'
            f'<td class="action-text">{row["recommended_action"]}</td></tr>'
        )
    table_html += '</tbody></table></div>'
    st.markdown(table_html, unsafe_allow_html=True)


def _build_hidden_table(df: pd.DataFrame) -> str:
    html = '<div class="table-wrapper"><table class="data-table"><thead><tr>'
    html += '<th>Company</th><th style="text-align:right">Direct Spend</th>'
    html += '<th style="text-align:right">Bedrock Spend</th><th style="text-align:right">Vertex Spend</th>'
    html += '<th style="text-align:right">Ratio</th><th>Score</th><th>Stage</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.sort_values("marketplace_to_direct", ascending=False).iterrows():
        html += (
            f'<tr><td class="company-name">{row["company"]}</td>'
            f'<td class="num">${row["latest_direct_spend"]:,.0f}</td>'
            f'<td class="num">${row["latest_bedrock_spend"]:,.0f}</td>'
            f'<td class="num">${row["latest_vertex_spend"]:,.0f}</td>'
            f'<td class="num" style="color:#D97706;font-weight:600;">{row["marketplace_to_direct"]:.1f}x</td>'
            f'<td>{score_pill(row["conversion_score"])}</td>'
            f'<td>{stage_tag(row["stage"])}</td></tr>'
        )
    html += '</tbody></table></div>'
    return html
