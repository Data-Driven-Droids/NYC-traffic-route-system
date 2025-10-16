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
    df = calculate_monthly_waste_metrics()  # <-- your backend/snowflake fetch
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
    df = get_bin_locations_data()  # <-- your backend/snowflake fetch
    return df


# ======================================================================
# LOAD DATA
# ======================================================================
monthly_df = load_monthly_data()
bin_locations_df = load_bin_locations()

# Handle missing monthly data
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
# PAGE SETUP
# ======================================================================
st.set_page_config(
    page_title="SAP Smart City - Waste Management Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for dark SAP-style theme ---
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
</style>
""", unsafe_allow_html=True)

# ======================================================================
# DASHBOARD TITLE
# ======================================================================
st.markdown('<h2 style="color:#FFFFFF;">Smart City - Waste Management</h2>', unsafe_allow_html=True)

# Safely show date if valid
if pd.notnull(latest["MONTH"]) and isinstance(latest["MONTH"], pd.Timestamp):
    formatted_date = latest["MONTH"].strftime("%b %Y")
else:
    formatted_date = "Unknown"

st.markdown(
    f"<p style='color:#A0A4AE;'>Showing data till <b>{formatted_date}</b></p>",
    unsafe_allow_html=True
)

# ======================================================================
# ROW 1: METRICS
# ======================================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Waste Collected", f"{latest['TOTAL_WASTE_TONS_MONTHLY']:,.2f}", "Tons")

with col2:
    st.metric("Total Recycled Waste", f"{latest['TOTAL_RECYCLED_TONS_MONTHLY']:,.2f}", "Tons")

with col3:
    st.metric("Average Diversion Rate", f"{latest['DIVERSION_RATE_AVG_MONTHLY']:.2f}%", "Recycled / Total")

st.markdown("---")

# ======================================================================
# ROW 2: BIN LOCATIONS MAP
# ======================================================================
if bin_locations_df is not None and not bin_locations_df.empty and {"lat", "lon"}.issubset(bin_locations_df.columns):
    st.markdown('<h3 style="color:#FFFFFF;">Real-Time Bin Locations</h3>', unsafe_allow_html=True)

    st.map(bin_locations_df, latitude='lat', longitude='lon', zoom=11, use_container_width=True)

    with st.expander("Show Raw Bin Location Data"):
        st.dataframe(bin_locations_df[["Name", "lat", "lon"]])

    st.markdown("---")
else:
    st.warning("⚠️ Could not load or display bin location data from Snowflake. Check connection parameters and view columns.")

# ======================================================================
# ROW 3: TREND CHART
# ======================================================================
if not recent_12.empty:
    st.markdown('<h3 style="color:#FFFFFF;">12-Month Trend: Waste vs Recycled</h3>', unsafe_allow_html=True)

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
            f"<p style='color:#A0A4AE;'>Waste diversion improved to <b>{latest['DIVERSION_RATE_AVG_MONTHLY']:.2f}%</b> in <b>{formatted_date}</b>.</p>",
            unsafe_allow_html=True
        )
    with col_b:
        avg_12 = recent_12["DIVERSION_RATE_AVG_MONTHLY"].mean()
        st.markdown(
            f"<p style='color:#A0A4AE;'>Average diversion rate for the last 12 months: <b>{avg_12:.2f}%</b></p>",
            unsafe_allow_html=True
        )
