"""Executive Dashboard — KPIs, conversion funnel, revenue breakdown, top accounts, trend."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from components.styles import (
    kpi_card, score_pill, stage_tag, section_header,
    STAGE_COLORS, CHANNEL_COLORS, PLOTLY_LAYOUT,
)


def render(scored_df: pd.DataFrame, monthly_df: pd.DataFrame):
    # ── Compute KPI values ──
    total_accounts = len(scored_df)
    total_mrr = scored_df["latest_total_spend"].sum()
    enterprise_pipeline = scored_df[
        scored_df["stage"].isin(["Enterprise Ready", "High Velocity"])
    ]["latest_total_spend"].sum() * 12
    avg_score = scored_df["conversion_score"].mean()

    # Compute MoM revenue delta
    monthly_totals = monthly_df.groupby("month_idx")["spend"].sum().sort_index()
    if len(monthly_totals) >= 2:
        current = monthly_totals.iloc[-1]
        previous = monthly_totals.iloc[-2]
        mrr_delta_pct = (current - previous) / previous * 100 if previous > 0 else 0
    else:
        mrr_delta_pct = 0

    enterprise_ready_count = len(scored_df[scored_df["stage"] == "Enterprise Ready"])

    # ── KPI Cards ──
    cols = st.columns(4, gap="medium")
    with cols[0]:
        st.markdown(
            kpi_card("Total Accounts", str(total_accounts), border_color="#2563EB"),
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            kpi_card(
                "Monthly Revenue",
                f"${total_mrr:,.0f}",
                border_color="#D97706",
                delta=f"{mrr_delta_pct:+.1f}% MoM",
                delta_positive=mrr_delta_pct >= 0,
            ),
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            kpi_card(
                "Enterprise Pipeline",
                f"${enterprise_pipeline:,.0f}/yr",
                border_color="#059669",
                delta=f"{enterprise_ready_count} accounts ready",
                delta_positive=True,
            ),
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            kpi_card("Avg Conversion Score", f"{avg_score:.1f}", border_color="#7C3AED"),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Funnel + Revenue Row ──
    col_funnel, col_rev = st.columns([1, 1], gap="large")

    # ── Conversion Funnel (horizontal bars) ──
    with col_funnel:
        st.markdown(section_header("Conversion Funnel"), unsafe_allow_html=True)

        stage_order = ["Enterprise Ready", "High Velocity", "Qualified", "Nurture", "At Risk"]
        stage_counts = scored_df["stage"].value_counts().reindex(stage_order, fill_value=0)

        # Render each funnel row as separate markdown to avoid large HTML blocks
        for stage_name in stage_order:
            count = int(stage_counts[stage_name])
            pct = count / total_accounts * 100
            max_count = int(stage_counts.max())
            bar_width = max(4, count / max_count * 100) if max_count > 0 else 4
            color = STAGE_COLORS[stage_name]

            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
                f'<div style="width:130px;font-size:13px;font-weight:500;color:#475569;'
                f'text-align:right;white-space:nowrap;">{stage_name}</div>'
                f'<div style="flex:1;background:#F1F5F9;border-radius:4px;height:28px;overflow:hidden;">'
                f'<div style="width:{bar_width:.0f}%;background:{color};height:100%;'
                f'border-radius:4px;min-width:4px;"></div></div>'
                f'<div style="width:120px;font-size:13px;color:#64748B;'
                f'font-variant-numeric:tabular-nums;white-space:nowrap;">'
                f'{count} accounts ({pct:.0f}%)</div></div>',
                unsafe_allow_html=True,
            )

    # ── Revenue by Channel (donut) ──
    with col_rev:
        st.markdown(section_header("Revenue by Channel", "Monthly"), unsafe_allow_html=True)

        channel_data = {
            "Direct API": scored_df["latest_direct_spend"].sum(),
            "AWS Bedrock": scored_df["latest_bedrock_spend"].sum(),
            "GCP Vertex AI": scored_df["latest_vertex_spend"].sum(),
            "Seat-Based": scored_df["latest_seat_spend"].sum(),
        }
        channel_data = {k: v for k, v in channel_data.items() if v > 0}

        fig_donut = go.Figure(go.Pie(
            labels=list(channel_data.keys()),
            values=list(channel_data.values()),
            hole=0.55,
            marker=dict(
                colors=[CHANNEL_COLORS.get(c, "#94A3B8") for c in channel_data],
                line=dict(color="#FFFFFF", width=2),
            ),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            **PLOTLY_LAYOUT,
            height=300,
            margin=dict(l=20, r=20, t=10, b=40),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.05,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color="#475569"),
            ),
            annotations=[dict(
                text=f"${total_mrr:,.0f}",
                x=0.5, y=0.5,
                font=dict(size=18, color="#1E293B", family="Plus Jakarta Sans, DM Sans, sans-serif"),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

    # ── Top 10 + Trend Row ──
    col_table, col_trend = st.columns([1, 1], gap="large")

    # ── Top 10 Accounts Table ──
    with col_table:
        st.markdown(section_header("Top 10 Accounts", "By total monthly footprint"), unsafe_allow_html=True)

        top10 = scored_df.nlargest(10, "latest_total_spend")

        table_html = '<div class="table-wrapper"><table class="data-table"><thead><tr>'
        table_html += '<th>Company</th><th style="text-align:right">Monthly Spend</th>'
        table_html += '<th>Score</th><th>Stage</th><th style="text-align:right">Channels</th>'
        table_html += '</tr></thead><tbody>'
        for _, row in top10.iterrows():
            table_html += (
                f'<tr><td class="company-name">{row["company"]}</td>'
                f'<td class="num">${row["latest_total_spend"]:,.0f}</td>'
                f'<td>{score_pill(row["conversion_score"])}</td>'
                f'<td>{stage_tag(row["stage"])}</td>'
                f'<td class="num">{row["n_channels"]}</td></tr>'
            )
        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)

    # ── Revenue Trend ──
    with col_trend:
        st.markdown(section_header("Revenue Trend", "12-month view by channel"), unsafe_allow_html=True)

        monthly_by_channel = (
            monthly_df.groupby(["month", "channel"])["spend"]
            .sum()
            .reset_index()
            .sort_values("month")
        )
        channels = ["Direct API", "AWS Bedrock", "GCP Vertex AI", "Seat-Based"]

        fig_trend = go.Figure()
        for ch in channels:
            ch_data = monthly_by_channel[monthly_by_channel["channel"] == ch]
            if not ch_data.empty:
                fig_trend.add_trace(go.Scatter(
                    x=ch_data["month"],
                    y=ch_data["spend"],
                    name=ch,
                    mode="lines",
                    fill="tonexty" if ch != channels[0] else "tozeroy",
                    line=dict(color=CHANNEL_COLORS.get(ch, "#94A3B8"), width=2),
                    hovertemplate=f"<b>{ch}</b><br>%{{x}}<br>${{y:,.0f}}<extra></extra>",
                ))

        fig_trend.update_layout(
            **PLOTLY_LAYOUT,
            height=370,
            margin=dict(l=10, r=10, t=10, b=30),
            xaxis_title="",
            yaxis_title="",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(size=11),
            ),
            yaxis=dict(
                gridcolor="#E2E8F0",
                tickformat="$,.0f",
                zerolinecolor="#E2E8F0",
            ),
            xaxis=dict(gridcolor="#E2E8F0", zerolinecolor="#E2E8F0"),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
