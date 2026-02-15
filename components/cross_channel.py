"""Cross-Channel View — stacked bar, hidden revenue opportunities, scatter, comparison card."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from components.styles import (
    kpi_card, section_header, score_pill, stage_tag, comparison_card,
    STAGE_COLORS, CHANNEL_COLORS, PLOTLY_LAYOUT,
)


def render(scored_df: pd.DataFrame, monthly_df: pd.DataFrame):

    st.markdown(
        section_header("Cross-Channel Intelligence", "Understand how customers engage across Anthropic's sales channels"),
        unsafe_allow_html=True,
    )

    # ── Top 15 Accounts — Horizontal Stacked Bar ──
    col_bar, col_dist = st.columns([3, 2], gap="large")

    with col_bar:
        st.markdown(section_header("Revenue by Channel", "Top 15 accounts by total monthly spend"),
                    unsafe_allow_html=True)

        top15 = scored_df.nlargest(15, "latest_total_spend").sort_values("latest_total_spend", ascending=True)

        fig_bar = go.Figure()
        for channel, spend_col, color in [
            ("Direct API", "latest_direct_spend", CHANNEL_COLORS["Direct API"]),
            ("AWS Bedrock", "latest_bedrock_spend", CHANNEL_COLORS["AWS Bedrock"]),
            ("GCP Vertex AI", "latest_vertex_spend", CHANNEL_COLORS["GCP Vertex AI"]),
            ("Seat-Based", "latest_seat_spend", CHANNEL_COLORS["Seat-Based"]),
        ]:
            fig_bar.add_trace(go.Bar(
                y=top15["company"],
                x=top15[spend_col],
                name=channel,
                orientation="h",
                marker_color=color,
                hovertemplate=f"<b>{channel}</b><br>%{{y}}<br>${{x:,.0f}}<extra></extra>",
            ))

        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            barmode="stack",
            height=480,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title="Monthly Spend ($)", tickformat="$,.0f", gridcolor="#E2E8F0"),
            yaxis=dict(automargin=True, tickfont=dict(size=12)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
        )
        st.plotly_chart(fig_bar, width="stretch")

    # ── Channel Distribution + Multi-channel Comparison ──
    with col_dist:
        st.markdown(section_header("Channel Distribution"), unsafe_allow_html=True)

        channel_dist = scored_df["n_channels"].value_counts().sort_index()
        labels = [f"{n} channel{'s' if n > 1 else ''}" for n in channel_dist.index]
        colors = ["#FDE68A", "#F59E0B", "#D97706", "#92400E"][:len(labels)]

        fig_dist = go.Figure(go.Bar(
            x=labels,
            y=channel_dist.values,
            marker=dict(color=colors[:len(labels)], line=dict(width=0)),
            hovertemplate="%{x}<br>%{y} accounts<extra></extra>",
        ))
        fig_dist.update_layout(
            **PLOTLY_LAYOUT,
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="#E2E8F0", title=""),
            showlegend=False,
        )
        st.plotly_chart(fig_dist, width="stretch")

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        # Multi-channel comparison card
        multi = scored_df[scored_df["n_channels"] >= 2]
        single = scored_df[scored_df["n_channels"] == 1]
        multi_avg = multi["conversion_score"].mean() if len(multi) > 0 else 0
        single_avg = single["conversion_score"].mean() if len(single) > 0 else 0
        delta = multi_avg - single_avg

        st.markdown(
            comparison_card(
                "Multi-Channel Avg Score",
                f"{multi_avg:.1f}",
                f"+{delta:.1f} vs single-channel",
                delta_positive=delta > 0,
            ),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)

    # ── Hidden Revenue Opportunities ──
    st.markdown(
        section_header(
            "Hidden Revenue Opportunities",
            "Accounts with significant marketplace spend invisible to your direct sales team",
        ),
        unsafe_allow_html=True,
    )

    dark_matter = scored_df[
        ((scored_df["latest_bedrock_spend"] + scored_df["latest_vertex_spend"]) > scored_df["latest_direct_spend"] * 2)
        & ((scored_df["latest_bedrock_spend"] + scored_df["latest_vertex_spend"]) > 1000)
    ].copy()

    if len(dark_matter) > 0:
        dark_matter["marketplace_spend"] = dark_matter["latest_bedrock_spend"] + dark_matter["latest_vertex_spend"]
        total_hidden = dark_matter["marketplace_spend"].sum()

        # KPI row
        hk = st.columns(3, gap="medium")
        with hk[0]:
            st.markdown(
                kpi_card("Hidden Revenue", f"${total_hidden:,.0f}/mo", border_color="#D97706"),
                unsafe_allow_html=True,
            )
        with hk[1]:
            st.markdown(
                kpi_card("Hidden Accounts", str(len(dark_matter)), border_color="#D97706"),
                unsafe_allow_html=True,
            )
        with hk[2]:
            avg_ratio = dark_matter["marketplace_to_direct"].mean()
            st.markdown(
                kpi_card("Avg Marketplace:Direct", f"{avg_ratio:.1f}x", border_color="#D97706"),
                unsafe_allow_html=True,
            )

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        # Table
        table_html = '<div class="table-wrapper"><table class="data-table"><thead><tr>'
        table_html += '<th>Company</th><th style="text-align:right">Direct Spend</th>'
        table_html += '<th style="text-align:right">Marketplace Spend</th>'
        table_html += '<th style="text-align:right">Ratio</th><th>Score</th><th>Stage</th>'
        table_html += '</tr></thead><tbody>'
        for _, row in dark_matter.sort_values("marketplace_spend", ascending=False).iterrows():
            table_html += (
                f'<tr><td class="company-name">{row["company"]}</td>'
                f'<td class="num">${row["latest_direct_spend"]:,.0f}</td>'
                f'<td class="num">${row["marketplace_spend"]:,.0f}</td>'
                f'<td class="num" style="color:#D97706;font-weight:700;font-size:15px;">'
                f'{row["marketplace_to_direct"]:.1f}x</td>'
                f'<td>{score_pill(row["conversion_score"])}</td>'
                f'<td>{stage_tag(row["stage"])}</td></tr>'
            )
        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

        # ── Scatter Plot ──
        st.markdown(section_header("Direct vs. Marketplace Spend", "Accounts above the line have untapped potential"),
                    unsafe_allow_html=True)

        fig_scatter = go.Figure()

        for stage_name in ["Enterprise Ready", "High Velocity", "Qualified", "Nurture", "At Risk"]:
            stage_data = dark_matter[dark_matter["stage"] == stage_name]
            if not stage_data.empty:
                fig_scatter.add_trace(go.Scatter(
                    x=stage_data["latest_direct_spend"],
                    y=stage_data["marketplace_spend"],
                    mode="markers",
                    name=stage_name,
                    marker=dict(
                        color=STAGE_COLORS[stage_name],
                        size=stage_data["conversion_score"] / 5 + 6,
                        line=dict(color="#FFFFFF", width=1),
                    ),
                    text=stage_data["company"],
                    hovertemplate="<b>%{text}</b><br>Direct: $%{x:,.0f}<br>Marketplace: $%{y:,.0f}<extra></extra>",
                ))

        # 1:1 diagonal line
        max_val = max(
            dark_matter["latest_direct_spend"].max(),
            dark_matter["marketplace_spend"].max(),
        ) * 1.15

        fig_scatter.add_shape(
            type="line", x0=0, y0=0, x1=max_val, y1=max_val,
            line=dict(dash="dash", color="#CBD5E1", width=1.5),
        )
        fig_scatter.add_annotation(
            x=max_val * 0.35, y=max_val * 0.75,
            text="Opportunity zone",
            showarrow=False,
            font=dict(size=12, color="#94A3B8", style="italic"),
        )

        fig_scatter.update_layout(
            **PLOTLY_LAYOUT,
            height=380,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title="Direct API Spend ($)", tickformat="$,.0f", gridcolor="#E2E8F0",
                       range=[0, max_val]),
            yaxis=dict(title="Marketplace Spend ($)", tickformat="$,.0f", gridcolor="#E2E8F0",
                       range=[0, max_val]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
        )
        st.plotly_chart(fig_scatter, width="stretch")
    else:
        st.info("No hidden revenue opportunities detected with current data.")

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    # ── Channel Migration Opportunities ──
    st.markdown(
        section_header("Channel Migration Opportunities",
                       "Accounts using only marketplace channels that could benefit from direct API access"),
        unsafe_allow_html=True,
    )

    marketplace_heavy = scored_df[
        (scored_df["latest_direct_spend"] < 1000)
        & ((scored_df["latest_bedrock_spend"] + scored_df["latest_vertex_spend"]) > 5000)
    ].copy()

    if len(marketplace_heavy) > 0:
        marketplace_heavy["total_marketplace"] = (
            marketplace_heavy["latest_bedrock_spend"] + marketplace_heavy["latest_vertex_spend"]
        )
        table_html = '<div class="table-wrapper"><table class="data-table"><thead><tr>'
        table_html += '<th>Company</th><th style="text-align:right">Marketplace Spend</th>'
        table_html += '<th style="text-align:right">Direct Spend</th><th>Score</th><th>Stage</th>'
        table_html += '</tr></thead><tbody>'
        for _, row in marketplace_heavy.sort_values("total_marketplace", ascending=False).iterrows():
            table_html += (
                f'<tr><td class="company-name">{row["company"]}</td>'
                f'<td class="num">${row["total_marketplace"]:,.0f}</td>'
                f'<td class="num">${row["latest_direct_spend"]:,.0f}</td>'
                f'<td>{score_pill(row["conversion_score"])}</td>'
                f'<td>{stage_tag(row["stage"])}</td></tr>'
            )
        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="padding:20px;color:#94A3B8;font-size:14px;">'
            "No clear channel migration opportunities in current data."
            "</div>",
            unsafe_allow_html=True,
        )
