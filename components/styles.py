"""
Shared CSS system, color constants, and HTML component helpers.
Provides the design system for the entire dashboard.
"""

# ── Color System ──────────────────────────────────────────────────────────────

COLORS = {
    "bg": "#FDF6EC",
    "card": "#FFFFFF",
    "shadow": "0 1px 3px rgba(0,0,0,0.08)",
    "accent": "#D97706",
    "text_dark": "#1E293B",
    "text_body": "#475569",
    "text_light": "#94A3B8",
    "border": "#E2E8F0",
    "hover": "#FFF8F0",
}

STAGE_COLORS = {
    "Enterprise Ready": "#059669",
    "High Velocity": "#2563EB",
    "Qualified": "#D97706",
    "Nurture": "#64748B",
    "At Risk": "#DC2626",
}

STAGE_BG_COLORS = {
    "Enterprise Ready": "#ECFDF5",
    "High Velocity": "#EFF6FF",
    "Qualified": "#FFFBEB",
    "Nurture": "#F8FAFC",
    "At Risk": "#FEF2F2",
}

CHANNEL_COLORS = {
    "Direct API": "#D97706",
    "AWS Bedrock": "#F59E0B",
    "GCP Vertex AI": "#2563EB",
    "Seat-Based": "#7C3AED",
}


# ── Score / Signal Helpers ────────────────────────────────────────────────────

def get_score_color(score: float) -> str:
    if score >= 78:
        return "#059669"
    elif score >= 63:
        return "#2563EB"
    elif score >= 48:
        return "#D97706"
    else:
        return "#DC2626"


def get_signal_health(metric: str, value) -> tuple[str, str]:
    """Return (color, label) for a signal's health status."""
    rules = {
        "growth_rate": [
            (0.20, "#059669", "Strong growth"),
            (0.05, "#D97706", "Moderate"),
            (-999, "#DC2626", "Declining"),
        ],
        "prod_ratio": [
            (0.80, "#059669", "Healthy"),
            (0.50, "#D97706", "Developing"),
            (0, "#DC2626", "Low maturity"),
        ],
        "error_rate_inv": [
            (0.04, "#DC2626", "High errors"),
            (0.02, "#059669", "Healthy range"),
            (0.005, "#059669", "Healthy range"),
            (0, "#D97706", "Very low volume"),
        ],
        "models": [
            (3, "#059669", "Diverse"),
            (2, "#D97706", "Moderate"),
            (0, "#DC2626", "Single model"),
        ],
        "days_inactive": [
            (8, "#DC2626", "Needs attention"),
            (3, "#D97706", "Monitor"),
            (0, "#059669", "Active"),
        ],
        "unique_users": [
            (10, "#059669", "Strong adoption"),
            (5, "#D97706", "Growing"),
            (0, "#DC2626", "Limited"),
        ],
        "daily_requests": [
            (10000, "#059669", "High volume"),
            (1000, "#D97706", "Moderate"),
            (0, "#DC2626", "Low volume"),
        ],
        "channels": [
            (3, "#059669", "Multi-channel"),
            (2, "#D97706", "Dual-channel"),
            (0, "#DC2626", "Single-channel"),
        ],
    }

    if metric == "error_rate_inv":
        # Error rate: lower is generally better, but 0.5-2% is sweet spot
        for threshold, color, label in rules[metric]:
            if value >= threshold:
                return color, label
        return "#94A3B8", ""

    if metric == "days_inactive":
        # Higher is worse
        for threshold, color, label in rules[metric]:
            if value >= threshold:
                return color, label
        return "#059669", "Active"

    if metric in rules:
        for threshold, color, label in rules[metric]:
            if value >= threshold:
                return color, label

    return "#94A3B8", ""


# ── HTML Component Helpers ────────────────────────────────────────────────────

def kpi_card(label: str, value: str, border_color: str = "#D97706",
             delta: str = None, delta_positive: bool = True) -> str:
    """Render a KPI card with left accent border."""
    delta_html = ""
    if delta:
        delta_color = "#059669" if delta_positive else "#DC2626"
        arrow = "\u2191" if delta_positive else "\u2193"
        delta_html = f'<div style="font-size:12px;color:{delta_color};margin-top:4px;font-weight:500;">{arrow} {delta}</div>'

    return (
        f'<div style="background:#FFFFFF;border-radius:8px;border-left:4px solid {border_color};'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.08);padding:16px 20px;height:100%;">'
        f'<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;'
        f'color:#94A3B8;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:28px;font-weight:700;color:#1E293B;font-variant-numeric:tabular-nums;'
        f'line-height:1.2;">{value}</div>'
        f'{delta_html}</div>'
    )


def score_pill(score: float) -> str:
    """Render a score as a small colored pill — white text on solid color."""
    color = get_score_color(score)
    return (
        f'<span style="'
        f"display:inline-block;padding:2px 10px;border-radius:12px;"
        f"font-size:12px;font-weight:700;font-variant-numeric:tabular-nums;"
        f"background:{color};color:#FFFFFF;line-height:1.6;"
        f'">{score:.1f}</span>'
    )


def stage_tag(stage: str) -> str:
    """Render a stage as a compact colored tag with pill shape."""
    color = STAGE_COLORS.get(stage, "#64748B")
    bg = STAGE_BG_COLORS.get(stage, "#F8FAFC")
    return (
        f'<span style="'
        f"display:inline-block;padding:2px 10px;border-radius:12px;"
        f"font-size:11px;font-weight:600;background:{bg};color:{color};"
        f"white-space:nowrap;line-height:1.6;"
        f'">{stage}</span>'
    )


def metric_card(label: str, value: str, health_color: str = None,
                health_label: str = None, top_border_color: str = None) -> str:
    """Render a signal metric card with optional health indicator."""
    top_border = f"border-top:3px solid {top_border_color};" if top_border_color else ""
    health_html = ""
    if health_color and health_label:
        health_html = (
            f'<div style="font-size:11px;font-weight:500;color:{health_color};margin-top:4px;">'
            f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
            f'background:{health_color};margin-right:4px;vertical-align:middle;"></span>'
            f'{health_label}</div>'
        )
    elif health_label and not health_color:
        health_html = f'<div style="font-size:11px;color:#94A3B8;margin-top:4px;">{health_label}</div>'

    return (
        f'<div style="background:#FFFFFF;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);'
        f'padding:14px 16px;{top_border}">'
        f'<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;'
        f'color:#94A3B8;margin-bottom:4px;">{label}</div>'
        f'<div style="font-size:20px;font-weight:700;color:#1E293B;font-variant-numeric:tabular-nums;'
        f'line-height:1.3;">{value}</div>'
        f'{health_html}</div>'
    )


def action_card(action: str, explanation: str, stage: str) -> str:
    """Render a recommended action card with stage-colored border."""
    color = STAGE_COLORS.get(stage, "#64748B")
    return (
        f'<div style="background:#FFFFFF;border-radius:8px;border-left:4px solid {color};'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.08);padding:20px 24px;">'
        f'<div style="font-size:11px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.5px;color:#94A3B8;margin-bottom:8px;">Recommended Action</div>'
        f'<div style="font-size:16px;font-weight:600;color:#1E293B;margin-bottom:8px;">{action}</div>'
        f'<div style="font-size:13px;color:#475569;line-height:1.5;">{explanation}</div>'
        f'</div>'
    )


def alert_card(title: str, message: str, border_color: str = "#D97706") -> str:
    """Render an alert/callout card."""
    return (
        f'<div style="background:#FFFBEB;border-radius:8px;border-left:4px solid {border_color};'
        f'padding:16px 20px;margin-bottom:16px;">'
        f'<div style="font-size:14px;font-weight:600;color:#92400E;margin-bottom:4px;">'
        f'\u26A0\uFE0F &nbsp;{title}</div>'
        f'<div style="font-size:13px;color:#78716C;line-height:1.5;">{message}</div>'
        f'</div>'
    )


def section_header(title: str, subtitle: str = None) -> str:
    """Render a section header with optional subtitle."""
    sub_html = ""
    if subtitle:
        sub_html = f'<div style="font-size:13px;color:#94A3B8;margin-top:2px;">{subtitle}</div>'
    return (
        f'<div style="margin-bottom:16px;">'
        f'<div style="font-size:20px;font-weight:600;color:#1E293B;">{title}</div>'
        f'{sub_html}</div>'
    )


def comparison_card(label: str, value: str, delta: str, delta_positive: bool = True) -> str:
    """Render a comparison stat card."""
    delta_color = "#059669" if delta_positive else "#DC2626"
    arrow = "\u2191" if delta_positive else "\u2193"
    return (
        f'<div style="background:#FFFFFF;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);'
        f'padding:20px 24px;text-align:center;">'
        f'<div style="font-size:11px;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.5px;color:#94A3B8;margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:36px;font-weight:700;color:#1E293B;'
        f'font-variant-numeric:tabular-nums;">{value}</div>'
        f'<div style="font-size:13px;font-weight:500;color:{delta_color};margin-top:4px;">'
        f'{arrow} {delta}</div></div>'
    )


# ── Plotly Layout Template ────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, DM Sans, -apple-system, sans-serif", color="#475569", size=12),
    hoverlabel=dict(
        bgcolor="#1E293B",
        font_size=12,
        font_color="#FFFFFF",
        font_family="Plus Jakarta Sans, DM Sans, -apple-system, sans-serif",
    ),
)


# ── Global CSS ────────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* ── Base Reset ── */
    *, *::before, *::after {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ── Background ── */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #FDF6EC;
    }

    /* ── Max Width Centered ── */
    .block-container {
        max-width: 1200px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #1C1917;
        width: 240px !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: #D6D3D1 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #FAFAF9 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        transition: background 0.15s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
    section[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
        color: #FBBF24 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
        margin: 16px 0 !important;
    }

    /* ── Typography ── */
    h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #1E293B !important;
    }
    h2 {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }
    h3 {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }
    p, li, span, td, th {
        color: #475569;
    }

    /* ── Metric Overrides (prevent truncation) ── */
    [data-testid="stMetric"] {
        background: transparent;
        border: none;
        padding: 0;
    }
    [data-testid="stMetricValue"] {
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
        font-variant-numeric: tabular-nums;
    }
    [data-testid="stMetricLabel"] {
        white-space: nowrap !important;
        overflow: visible !important;
    }

    /* ── Dividers ── */
    hr {
        border-color: #E2E8F0 !important;
        margin: 24px 0 !important;
    }

    /* ── Multiselect / Filter Overrides ── */
    div[data-baseweb="select"] span[data-baseweb="tag"] {
        background-color: #F1F5F9 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        color: #475569 !important;
    }
    div[data-baseweb="select"] span[data-baseweb="tag"] span {
        color: #475569 !important;
    }
    div[data-baseweb="tag"] svg {
        color: #94A3B8 !important;
    }
    div[data-baseweb="select"] {
        border-radius: 8px !important;
    }

    /* ── Slider Override ── */
    [data-baseweb="slider"] div[role="slider"] {
        background-color: #D97706 !important;
    }
    [data-baseweb="slider"] div[data-testid="stTickBarMin"],
    [data-baseweb="slider"] div[data-testid="stTickBarMax"] {
        color: #94A3B8 !important;
    }

    /* ── Selectbox Override ── */
    div[data-baseweb="select"] > div {
        border-color: #E2E8F0 !important;
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
    }

    /* ── Expander Override ── */
    [data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        background: #FFFFFF !important;
    }

    /* ── Dataframe Override ── */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }

    /* ── Hide default Streamlit elements ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}

    /* ── Card container class ── */
    .card {
        background: #FFFFFF;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        padding: 20px 24px;
        border: 1px solid #F1F5F9;
    }

    /* ── Table wrapper (horizontal scroll for wide tables) ── */
    .table-wrapper {
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid #F1F5F9;
    }

    /* ── Data table styling ── */
    .data-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 13px;
        border-radius: 8px;
        overflow: hidden;
    }
    .table-wrapper .data-table {
        border: none;
    }
    .data-table thead th {
        background: #FAFAFA;
        color: #64748B;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 14px;
        text-align: left;
        border-bottom: 1px solid #F1F5F9;
        white-space: nowrap;
    }
    .data-table tbody td {
        padding: 12px 14px;
        color: #475569;
        border-bottom: 1px solid #F1F5F9;
        vertical-align: middle;
        background: #FFFFFF;
    }
    .data-table tbody tr:hover td {
        background: #FFF8F0;
    }
    .data-table tbody tr:last-child td {
        border-bottom: none;
    }
    .data-table .company-name {
        font-weight: 600;
        color: #1E293B;
        white-space: nowrap;
    }
    .data-table .num {
        font-variant-numeric: tabular-nums;
        text-align: right;
        color: #1E293B;
        font-weight: 500;
    }
    .data-table .positive { color: #059669; font-weight: 600; }
    .data-table .negative { color: #DC2626; font-weight: 600; }
    .data-table td.industry-cell {
        color: #64748B;
        font-weight: 400;
    }
    .data-table .action-text {
        font-size: 12px;
        color: #64748B;
        min-width: 200px;
        line-height: 1.4;
    }
</style>
"""
