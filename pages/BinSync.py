import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from utils import calculate_monthly_waste_metrics, get_bin_locations_data

# ======================================================================
# DATA LOADING FUNCTIONS
# ======================================================================

@st.cache_data
def load_monthly_data():
    df = calculate_monthly_waste_metrics()
    if df is not None and not df.empty:
        # Convert 'MONTH' safely from "YYYY / MM" → datetime
        df["MONTH"] = (
            df["MONTH"]
            .astype(str)
            .str.strip()
            .str.replace(" / ", "-", regex=False)
            .apply(lambda x: pd.to_datetime(x + "-01", errors="coerce"))
        )
    return df


@st.cache_data
def load_bin_locations():
    df = get_bin_locations_data()
    return df


# ======================================================================
# LOAD DATA
# ======================================================================
monthly_df = load_monthly_data()
bin_locations_df = load_bin_locations()

if monthly_df is not None and not monthly_df.empty:
    latest = monthly_df.iloc[-1]
    recent_12 = monthly_df.tail(12)
else:
    latest = pd.Series({
        "MONTH": datetime.now(),
        "TOTAL_WASTE_TONS_MONTHLY": 0,
        "TOTAL_RECYCLED_TONS_MONTHLY": 0,
        "DIVERSION_RATE_AVG_MONTHLY": 0.0
    })
    recent_12 = pd.DataFrame()


# ======================================================================
# PAGE CONFIG
# ======================================================================
st.set_page_config(
    page_title="Smart City - Waste Management Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main { background-color: #1E2129; }
    div[data-testid="stMetric"] > div[data-testid="stMetricValue"] {
        font-size: 2.5rem; font-weight: bold; color: #FFFFFF;
    }
    div[data-testid="stMetric"] > div[data-testid="stMetricLabel"] {
        font-size: 0.9rem; color: #A0A4AE;
    }
    hr { border: 0; border-top: 1px solid #3A3F4B; }
    h2, h3, p { color: #FFFFFF; }
    button[data-testid="stBaseButton-secondary"] {
        background: #2F3240 !important;
        color: #00BFFF !important;
        border-radius: 50%;
        font-weight: bold;
        padding: 2px 8px;
    }
</style>
""", unsafe_allow_html=True)


# ======================================================================
# ABOUT SECTION
# ======================================================================
st.markdown("""
<h2 style='text-align:center; color:#FFFFFF;'>🌍 Smart City - Waste Management Dashboard</h2>
<p style='text-align:center; color:#A0A4AE;'>
This dashboard provides a real-time view of <b>waste generation, recycling performance,</b> and <b>bin locations</b> across the city.<br>
It helps city administrators monitor sustainability efforts and track diversion rates effectively.
</p>
""", unsafe_allow_html=True)

st.markdown("---")


# ======================================================================
# METRICS WITH INFO BUTTONS
# ======================================================================
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        c1, c2 = st.columns([4, 1])
        with c1:
            st.metric("Total Waste Collected", f"{latest['TOTAL_WASTE_TONS_MONTHLY']:,.2f}", "Tons")
        with c2:
            with st.popover("ℹ️"):
                st.markdown("""
                **Total Waste Collected**  
                The total tonnage of municipal solid waste generated across the city for the given month.  
                Includes both recyclable and non-recyclable materials.
                """)

with col2:
    with st.container():
        c1, c2 = st.columns([4, 1])
        with c1:
            st.metric("Total Recycled Waste", f"{latest['TOTAL_RECYCLED_TONS_MONTHLY']:,.2f}", "Tons")
        with c2:
            with st.popover("ℹ️"):
                st.markdown("""
                **Total Recycled Waste**  
                The portion of collected waste that has been processed and reused  
                through recycling or composting facilities in the same period.
                """)

with col3:
    with st.container():
        c1, c2 = st.columns([4, 1])
        with c1:
            st.metric("Average Diversion Rate", f"{latest['DIVERSION_RATE_AVG_MONTHLY']:.2f}%", "Recycled / Total")
        with c2:
            with st.popover("ℹ️"):
                st.markdown("""
                **Diversion Rate (%)**  
                The percentage of waste diverted away from landfills through recycling or composting.  
                Calculated as:  
                **(Recycled Waste ÷ Total Waste) × 100**
                """)

st.markdown("---")


# ======================================================================
# BIN LOCATIONS MAP
# ======================================================================
if bin_locations_df is not None and not bin_locations_df.empty and {"lat", "lon"}.issubset(bin_locations_df.columns):
    st.markdown('<h3 style="color:#FFFFFF;">🗺️ Real-Time Bin Locations</h3>', unsafe_allow_html=True)

    st.map(bin_locations_df, latitude='lat', longitude='lon', zoom=11, use_container_width=True)

    with st.expander("Show Raw Bin Location Data"):
        st.dataframe(bin_locations_df[["Name", "lat", "lon"]])

    st.markdown("---")
else:
    st.warning("⚠️ Could not load or display bin location data. Check data source or Snowflake connection.")


# ======================================================================
# TREND CHART
# ======================================================================
if not recent_12.empty:
    st.markdown('<h3 style="color:#FFFFFF;">📈 12-Month Trend: Waste vs Recycled</h3>', unsafe_allow_html=True)

    trend_df = recent_12.melt(
        id_vars="MONTH",
        value_vars=["TOTAL_WASTE_TONS_MONTHLY", "TOTAL_RECYCLED_TONS_MONTHLY"],
        var_name="Type",
        value_name="Tons"
    )

    trend_df["Type"] = trend_df["Type"].replace({
        "TOTAL_WASTE_TONS_MONTHLY": "Total Waste",
        "TOTAL_RECYCLED_TONS_MONTHLY": "Recycled Waste"
    })

    chart = (
        alt.Chart(trend_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("MONTH:T", title="Month", axis=alt.Axis(labelColor="#A0A4AE")),
            y=alt.Y("Tons:Q", title="Tons of Waste", axis=alt.Axis(labelColor="#A0A4AE")),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(domain=["Total Waste", "Recycled Waste"], range=["#2ECC71", "#3498DB"]),
            ),
            tooltip=["MONTH:T", "Type:N", "Tons:Q"]
        )
        .properties(height=350, background="#282C34")
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"<p style='color:#A0A4AE;'>Waste diversion improved to <b>{latest['DIVERSION_RATE_AVG_MONTHLY']:.2f}%</b> in <b>{latest['MONTH'].strftime('%b %Y')}</b>.</p>",
            unsafe_allow_html=True
        )
    with col_b:
        avg_12 = recent_12["DIVERSION_RATE_AVG_MONTHLY"].mean()
        st.markdown(
            f"<p style='color:#A0A4AE;'>Average diversion rate for the last 12 months: <b>{avg_12:.2f}%</b></p>",
            unsafe_allow_html=True
        )
