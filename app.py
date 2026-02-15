"""
API-to-Enterprise Conversion Intelligence Dashboard

A unified view of customer footprint across Anthropic's sales channels,
surfacing enterprise conversion opportunities through composite scoring.
"""

import streamlit as st

st.set_page_config(
    page_title="Conversion Intelligence | Anthropic GTM",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Global CSS ──
from components.styles import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

from data.generator import generate_accounts
from analytics.signals import compute_all_signals
from analytics.scoring import score_all_accounts
from components import overview, conversion_pipeline, account_detail, cross_channel


@st.cache_data
def load_data():
    """Generate and score all account data (cached)."""
    raw = generate_accounts()
    enriched = compute_all_signals(raw["accounts"], raw["monthly_usage"])
    scored = score_all_accounts(enriched)
    return scored, raw["monthly_usage"]


def main():
    scored_df, monthly_df = load_data()

    # ── Banner ──
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1C1917 0%, #292524 100%);
        padding: 16px 28px;
        border-radius: 10px;
        margin-bottom: 28px;
    ">
        <div style="font-size:22px;font-weight:700;color:#FAFAF9;margin:0;">
            Conversion Intelligence Dashboard
        </div>
        <div style="font-size:13px;color:#A8A29E;margin-top:2px;">
            Unified customer footprint across API, Bedrock, Vertex AI &amp; Enterprise products
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar — Navigation Only ──
    with st.sidebar:
        st.markdown(
            '<div style="padding:8px 0 4px 0;font-size:11px;font-weight:600;'
            'text-transform:uppercase;letter-spacing:1px;color:#78716C;">Navigation</div>',
            unsafe_allow_html=True,
        )
        page = st.radio(
            "nav",
            options=[
                "Executive Dashboard",
                "Conversion Pipeline",
                "Account Intelligence",
                "Cross-Channel View",
            ],
            label_visibility="collapsed",
        )
        st.markdown('<div style="flex:1;"></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(
            '<div style="font-size:11px;color:#78716C;line-height:1.4;">'
            "Simulated data for portfolio demonstration"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Route ──
    if page == "Executive Dashboard":
        overview.render(scored_df, monthly_df)
    elif page == "Conversion Pipeline":
        conversion_pipeline.render(scored_df)
    elif page == "Account Intelligence":
        account_detail.render(scored_df, monthly_df)
    elif page == "Cross-Channel View":
        cross_channel.render(scored_df, monthly_df)


if __name__ == "__main__":
    main()
