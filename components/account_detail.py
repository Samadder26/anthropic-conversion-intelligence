"""Account Intelligence — individual account deep-dive with score breakdown and trends."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from components.styles import (
    metric_card, action_card, section_header, score_pill, stage_tag,
    get_signal_health, STAGE_COLORS, CHANNEL_COLORS, PLOTLY_LAYOUT,
)
from analytics.scoring import get_recommended_action, get_action_explanation


def render(scored_df: pd.DataFrame, monthly_df: pd.DataFrame):

    st.markdown(
        section_header("Account Intelligence", "Deep-dive into individual account signals and readiness"),
        unsafe_allow_html=True,
    )

    # ── Account Selector ──
    account_options = scored_df.sort_values("conversion_score", ascending=False)
    display_map = {
        f"{row['company']}  |  Score: {row['conversion_score']}  ({row['stage']})": row["account_id"]
        for _, row in account_options.iterrows()
    }
    selected_label = st.selectbox("Select Account", options=list(display_map.keys()), label_visibility="collapsed")
    selected_id = display_map[selected_label]
    acct = scored_df[scored_df["account_id"] == selected_id].iloc[0]

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # ── Score + Stage Header ──
    stage_color = STAGE_COLORS.get(acct["stage"], "#64748B")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <div style="font-size:24px;font-weight:700;color:#1E293B;">{acct['company']}</div>
        <div>{score_pill(acct['conversion_score'])}</div>
        <div>{stage_tag(acct['stage'])}</div>
        <div style="margin-left:auto;font-size:13px;color:#94A3B8;">
            {acct['industry']}  &middot;  Signed up {acct['signup_date']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Unified Footprint Cards ──
    st.markdown(section_header("Unified Footprint", "Spend across all Anthropic channels"), unsafe_allow_html=True)

    fc = st.columns(5, gap="medium")
    with fc[0]:
        st.markdown(
            metric_card("Total Monthly", f"${acct['latest_total_spend']:,.0f}", top_border_color="#1E293B"),
            unsafe_allow_html=True,
        )
    with fc[1]:
        st.markdown(
            metric_card("Direct API", f"${acct['latest_direct_spend']:,.0f}", top_border_color="#D97706"),
            unsafe_allow_html=True,
        )
    with fc[2]:
        st.markdown(
            metric_card("AWS Bedrock", f"${acct['latest_bedrock_spend']:,.0f}", top_border_color="#F59E0B"),
            unsafe_allow_html=True,
        )
    with fc[3]:
        st.markdown(
            metric_card("GCP Vertex AI", f"${acct['latest_vertex_spend']:,.0f}", top_border_color="#2563EB"),
            unsafe_allow_html=True,
        )
    with fc[4]:
        st.markdown(
            metric_card("Seat-Based", f"${acct['latest_seat_spend']:,.0f}", top_border_color="#7C3AED"),
            unsafe_allow_html=True,
        )

    # Secondary info row
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    ic = st.columns(4, gap="medium")
    with ic[0]:
        st.markdown(metric_card("Enterprise Seats", str(int(acct["enterprise_seats"]))), unsafe_allow_html=True)
    with ic[1]:
        st.markdown(metric_card("Code Licenses", str(int(acct["code_licenses"]))), unsafe_allow_html=True)
    with ic[2]:
        models_list = ", ".join(acct["models_used"])
        st.markdown(metric_card("Models Used", f"{acct['n_models']} models", health_color=None, health_label=models_list), unsafe_allow_html=True)
    with ic[3]:
        ch_count = acct.get("n_active_channels", acct["n_channels"])
        ch_color, ch_label = get_signal_health("channels", ch_count)
        st.markdown(metric_card("Active Channels", str(ch_count), ch_color, ch_label), unsafe_allow_html=True)

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Score Breakdown + Trend ──
    col_radar, col_trend = st.columns([1, 1], gap="large")

    with col_radar:
        st.markdown(section_header("Score Breakdown"), unsafe_allow_html=True)

        categories = ["Usage Intensity", "Production Maturity", "Team Adoption", "Cross-Channel", "Risk (inverted)"]
        values = [
            acct["usage_intensity_score"],
            acct["production_maturity_score"],
            acct["team_adoption_score"],
            acct["cross_channel_score"],
            max(0, 100 - acct["risk_penalty"] * 10),
        ]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(37,99,235,0.12)",
            line=dict(color="#2563EB", width=2),
            marker=dict(size=6, color="#2563EB"),
            hovertemplate="%{theta}<br>Score: %{r:.0f}/100<extra></extra>",
        ))
        fig_radar.update_layout(
            **PLOTLY_LAYOUT,
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10, color="#94A3B8"),
                                gridcolor="#E2E8F0"),
                angularaxis=dict(tickfont=dict(size=11, color="#475569"), gridcolor="#E2E8F0"),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=340,
            margin=dict(l=60, r=60, t=30, b=30),
            showlegend=False,
        )
        st.plotly_chart(fig_radar, width="stretch")

    with col_trend:
        st.markdown(section_header("12-Month Usage Trend"), unsafe_allow_html=True)

        acct_monthly = monthly_df[monthly_df["account_id"] == selected_id].sort_values("month")
        if not acct_monthly.empty:
            channels_order = ["Direct API", "AWS Bedrock", "GCP Vertex AI", "Seat-Based"]
            fig_trend = go.Figure()
            for ch in channels_order:
                ch_data = acct_monthly[acct_monthly["channel"] == ch]
                if not ch_data.empty:
                    fig_trend.add_trace(go.Scatter(
                        x=ch_data["month"],
                        y=ch_data["spend"],
                        name=ch,
                        mode="lines",
                        fill="tonexty" if ch != channels_order[0] else "tozeroy",
                        line=dict(color=CHANNEL_COLORS.get(ch, "#94A3B8"), width=2),
                        hovertemplate=f"<b>{ch}</b><br>%{{x}}<br>${{y:,.0f}}<extra></extra>",
                    ))
            fig_trend.update_layout(
                **PLOTLY_LAYOUT,
                height=340,
                margin=dict(l=10, r=10, t=10, b=30),
                xaxis_title="",
                yaxis=dict(gridcolor="#E2E8F0", tickformat="$,.0f", zerolinecolor="#E2E8F0"),
                xaxis=dict(gridcolor="#E2E8F0", zerolinecolor="#E2E8F0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
            )
            st.plotly_chart(fig_trend, width="stretch")
        else:
            st.info("No monthly data available for this account.")

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Signal Details ──
    st.markdown(section_header("Signal Details", "Key behavioral indicators with health assessment"),
                unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3, gap="medium")

    growth = acct.get("computed_growth_rate", acct.get("growth_rate", 0))

    with s1:
        gc, gl = get_signal_health("growth_rate", growth)
        st.markdown(metric_card("MoM Growth Rate", f"{growth:+.1%}", gc, gl), unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

        rc, rl = get_signal_health("daily_requests", acct["daily_requests"])
        st.markdown(metric_card("Daily Requests", f"{acct['daily_requests']:,}", rc, rl), unsafe_allow_html=True)

    with s2:
        pc, pl = get_signal_health("prod_ratio", acct["prod_ratio"])
        st.markdown(metric_card("Production Traffic", f"{acct['prod_ratio']:.0%}", pc, pl), unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

        ec, el = get_signal_health("error_rate_inv", acct["error_rate"])
        st.markdown(metric_card("Error Rate", f"{acct['error_rate']:.2%}", ec, el), unsafe_allow_html=True)

    with s3:
        uc, ul = get_signal_health("unique_users", acct["unique_users"])
        st.markdown(metric_card("Unique Domain Users", str(acct["unique_users"]), uc, ul), unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

        dc, dl = get_signal_health("days_inactive", acct["days_inactive"])
        st.markdown(metric_card("Days Since Last Activity", str(acct["days_inactive"]), dc, dl), unsafe_allow_html=True)

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Recommended Action ──
    action_text = get_recommended_action(acct)
    explanation = get_action_explanation(acct)
    st.markdown(action_card(action_text, explanation, acct["stage"]), unsafe_allow_html=True)
