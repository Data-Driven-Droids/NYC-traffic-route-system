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

st.title("City Scope 360 Dashboard")
st.markdown("""This is just a prototype for New York City.""")

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
# PLACEHOLDER SKELETON (DRAW THIS FIRST)
# ======================================================================

# --- Metrics Placeholders ---
metrics_placeholder = st.empty()
with metrics_placeholder.container():
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Waste Collected", "Loading...", "Tons")
    col2.metric("Total Recycled Waste", "Loading...", "Tons")
    col3.metric("Average Diversion Rate", "Loading...", "%")
st.markdown("---")

# --- News Ticker Placeholder ---
news_placeholder = st.empty()
with news_placeholder.container():
    st.markdown('<h3 style="color:#FFFFFF;">♻️ Latest Recycling & Waste Management News</h3>', unsafe_allow_html=True)
    st.info("Loading latest news headlines...")
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# --- Map Placeholder ---
map_placeholder = st.empty()
with map_placeholder.container():
    st.markdown('<h3 style="color:#FFFFFF;">🗺️ Real-Time Bin Locations</h3>', unsafe_allow_html=True)
    st.info("Loading bin location data...")
st.markdown("---")

# --- Trend Chart Placeholder ---
chart_placeholder = st.empty()
with chart_placeholder.container():
    st.markdown('<h3 style="color:#FFFFFF;">📈 12-Month Trend: Waste vs Recycled</h3>', unsafe_allow_html=True)
    st.info("Loading 12-month trend data...")
st.markdown("---")

# --- Highlights Placeholder ---
highlights_placeholder = st.empty()
with highlights_placeholder.container():
    st.markdown('<h3 style="color:#FFFFFF; margin-bottom: 20px;">📊 Key Highlights</h3>', unsafe_allow_html=True)
    st.info("Loading key highlights...")


# ======================================================================
# LOAD DATA (THIS HAPPENS *AFTER* SKELETON IS DRAWN)
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
# REPLACE METRICS PLACEHOLDER WITH REAL DATA
# ======================================================================
with metrics_placeholder.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.metric("Total Waste Collected", f"{latest['TOTAL_WASTE_TONS_MONTHLY']:,.2f}", "Tons")
            with c2:
                with st.popover("ℹ️"):
                    st.markdown("""
                    **Total Waste Collected** The total tonnage of municipal solid waste generated across the city for the given month.  
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
                    **Total Recycled Waste** The portion of collected waste that has been processed and reused  
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
                    **Diversion Rate (%)** The percentage of waste diverted away from landfills through recycling or composting.  
                    Calculated as:  
                    **(Recycled Waste ÷ Total Waste) × 100**
                    """)

# ======================================================================
# REPLACE NEWS TICKER PLACEHOLDER WITH REAL DATA
# ======================================================================
with news_placeholder.container():
    st.markdown('<h3 style="color:#FFFFFF;">♻️ Latest Recycling & Waste Management News</h3>', unsafe_allow_html=True)

    # Fetch recycling/waste management related news
    try:
        from utils import get_news_headlines
        # Get general news and filter for recycling/waste keywords
        news_headlines = get_news_headlines(query="New York City recycling and waste management", max_results=15)
        
        if isinstance(news_headlines, str):
            headlines_list = [h.strip() for h in news_headlines.split("•") if h.strip()]
        else:
            headlines_list = news_headlines if news_headlines else []
        
        # Use the list directly (query is already specific)
        filtered_headlines = headlines_list
        
        # If no recycling news found, use general environmental news or default messages
        if not filtered_headlines:
            filtered_headlines = [
                "NYC continues to improve waste diversion rates across all boroughs",
                "New recycling initiatives launched to increase sustainability",
                "Smart bin technology being deployed citywide",
                "Composting programs expand to more neighborhoods",
                "City targets 90% waste diversion rate by 2030"
            ]
        
        headlines_html = "".join([f"<div class='headline-item'>♻️ {h}</div>" for h in filtered_headlines[:10]])
        
    except Exception as e:
        headlines_html = "<div class='headline-item'>♻️ NYC continues to improve waste management and recycling efforts</div>"

    # Custom CSS for news ticker
    news_ticker_css = """
    <style>
    .recycling-news-container {
        background: linear-gradient(135deg, rgba(46, 204, 113, 0.1) 0%, rgba(39, 174, 96, 0.1) 100%);
        border-radius: 12px;
        padding: 15px 20px;
        height: 120px;
        overflow: hidden;
        position: relative;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 2px solid rgba(46, 204, 113, 0.3);
    }

    .recycling-news-scroll {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: absolute;
        width: 100%;
        animation: scrollUpRecycling 25s linear infinite;
    }

    .recycling-news-container .headline-item {
        font-size: 1.05em;
        font-weight: 500;
        color: #FFFFFF;
        text-align: center;
        padding: 8px 0;
        line-height: 1.5;
    }

    .recycling-live-indicator {
        position: absolute;
        top: 12px;
        right: 15px;
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 0.85em;
        color: #2ecc71;
        font-weight: 600;
        z-index: 10;
        background: rgba(30, 33, 41, 0.9);
        padding: 5px 10px;
        border-radius: 12px;
        border: 1px solid #2ecc71;
    }

    .recycling-live-dot {
        width: 8px;
        height: 8px;
        background-color: #2ecc71;
        border-radius: 50%;
        animation: pulseGreen 2s infinite;
    }

    @keyframes pulseGreen {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.6;
            transform: scale(1.1);
        }
    }

    @keyframes scrollUpRecycling {
        0%   { top: 100%; }
        100% { top: -100%; }
    }
    </style>
    """

    st.markdown(news_ticker_css, unsafe_allow_html=True)

    # Render the news ticker
    st.markdown(f"""
    <div class="recycling-news-container">
        <div class="recycling-live-indicator"><span class="recycling-live-dot"></span>Live</div>
        <div class="recycling-news-scroll">
            {headlines_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ======================================================================
# REPLACE BIN LOCATIONS MAP PLACEHOLDER WITH REAL DATA
# ======================================================================
with map_placeholder.container():
    if bin_locations_df is not None and not bin_locations_df.empty and {"lat", "lon"}.issubset(bin_locations_df.columns):
        st.markdown('<h3 style="color:#FFFFFF;">🗺️ Real-Time Bin Locations</h3>', unsafe_allow_html=True)

        # Create pydeck map with tooltips using open-street-map (no API key needed)
        import pydeck as pdk
        
        # Define the layer with tooltips
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=bin_locations_df,
            get_position=["lon", "lat"],
            get_color=[46, 204, 113, 220],  # Bright green color
            get_radius=80,
            pickable=True,
            auto_highlight=True,
            highlight_color=[255, 255, 0, 200],  # Yellow on hover
        )
        
        # Set the initial view state
        view_state = pdk.ViewState(
            latitude=bin_locations_df["lat"].mean(),
            longitude=bin_locations_df["lon"].mean(),
            zoom=11,
            pitch=0,
        )
        
        # Create tooltip with better formatting
        tooltip_html = """
        <div style="background-color: rgba(30, 33, 41, 0.95); padding: 12px; border-radius: 10px; color: white; border: 2px solid #2ecc71; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px; color: #2ecc71;">📍 {Name}</div>
            <div style="font-size: 13px; margin-bottom: 4px;"><b>Area:</b> {Area}</div>
            <div style="font-size: 13px; margin-bottom: 4px;"><b>Type:</b> {Type}</div>
            <div style="font-size: 12px; color: #A0A4AE;">Lat: {lat:.4f}, Lon: {lon:.4f}</div>
        </div>
        """
        
        tooltip = {
            "html": tooltip_html,
            "style": {
                "backgroundColor": "transparent",
                "color": "white"
            }
        }
        
        # Render the map with open-street-map style (no API key required)
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        )
        
        st.pydeck_chart(r, use_container_width=True)

        with st.expander("Show Raw Bin Location Data"):
            # Display table with Area column after Name
            display_cols = ["Name"]
            if "Area" in bin_locations_df.columns:
                display_cols.append("Area")
            if "Type" in bin_locations_df.columns:
                display_cols.append("Type")
            display_cols.extend(["lat", "lon"])
            
            # Filter to only existing columns
            available_display_cols = [col for col in display_cols if col in bin_locations_df.columns]
            st.dataframe(bin_locations_df[available_display_cols], use_container_width=True)

    else:
        st.warning("⚠️ Could not load or display bin location data. Check data source or Snowflake connection.")


# ======================================================================
# REPLACE TREND CHART PLACEHOLDER WITH REAL DATA
# ======================================================================
with chart_placeholder.container():
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
            .mark_line(point=True, size=3)
            .encode(
                x=alt.X(
                    "MONTH:T", 
                    title="Month",
                    axis=alt.Axis(
                        labelColor="#A0A4AE",
                        format="%b %Y",  # Format as "Jan 2024"
                        labelAngle=-45,  # Rotate labels for better readability
                        labelFontSize=11,
                        titleColor="#FFFFFF",
                        titleFontSize=13,
                        grid=False
                    )
                ),
                y=alt.Y(
                    "Tons:Q", 
                    title="Tons of Waste",
                    axis=alt.Axis(
                        labelColor="#A0A4AE",
                        titleColor="#FFFFFF",
                        titleFontSize=13,
                        gridColor="#3A3F4B",
                        gridOpacity=0.5
                    )
                ),
                color=alt.Color(
                    "Type:N",
                    scale=alt.Scale(domain=["Total Waste", "Recycled Waste"], range=["#2ECC71", "#3498DB"]),
                    legend=alt.Legend(
                        title="Waste Type",
                        titleColor="#FFFFFF",
                        labelColor="#A0A4AE",
                        orient="bottom",
                        direction="horizontal",
                        titleFontSize=12,
                        labelFontSize=11
                    )
                ),
                tooltip=[
                    alt.Tooltip("MONTH:T", title="Month", format="%B %Y"),
                    alt.Tooltip("Type:N", title="Type"),
                    alt.Tooltip("Tons:Q", title="Tons", format=",.2f")
                ]
            )
            .properties(
                height=400, 
                background="#282C34",
                padding={"left": 10, "right": 10, "top": 20, "bottom": 60}
            )
            .configure_view(
                strokeWidth=0
            )
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("⚠️ Could not load 12-month trend data.")

# ======================================================================
# REPLACE HIGHLIGHTS PLACEHOLDER WITH REAL DATA
# ======================================================================
with highlights_placeholder.container():
    if not recent_12.empty:
        # Highlights Section with Enhanced Styling
        st.markdown("""
        <style>
        .highlight-card {
            background: linear-gradient(135deg, rgba(30, 33, 41, 0.9) 0%, rgba(40, 44, 52, 0.9) 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            border-left: 4px solid #2ecc71;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: transform 0.2s ease;
        }
        .highlight-card:hover {
            transform: translateY(-2px);
        }
        .highlight-card h4 {
            color: #2ecc71;
            margin: 0 0 10px 0;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .highlight-card p {
            color: #A0A4AE;
            margin: 0;
            font-size: 0.95em;
            line-height: 1.5;
        }
        .highlight-card .value {
            color: #FFFFFF;
            font-weight: 600;
            font-size: 1.2em;
        }
        .highlight-card .date {
            color: #6c757d;
            font-size: 0.85em;
            margin-top: 6px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<h3 style="color:#FFFFFF; margin-bottom: 20px;">📊 Key Highlights</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="highlight-card">
                <h4>📈 Current Diversion Rate</h4>
                <p>Waste diversion improved to <span class="value">{latest['DIVERSION_RATE_AVG_MONTHLY']:.2f}%</span></p>
                <div class="date">As of {latest['MONTH'].strftime('%B %Y')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_12 = recent_12["DIVERSION_RATE_AVG_MONTHLY"].mean()
            st.markdown(f"""
            <div class="highlight-card">
                <h4>📅 12-Month Average</h4>
                <p>Average diversion rate: <span class="value">{avg_12:.2f}%</span></p>
                <div class="date">Last 12 months</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Could not load key highlights data.")