import streamlit as st
import pandas as pd
import numpy as np
import asyncio
from config.settings import Config 
from utils import get_weather_data_nyc, get_air_quality_data_nyc, get_news_headlines, get_nyc_demographics

# 1. Define NYC Subregions and Coordinates 📍
NYC_REGIONS = {
    "New York City": {"latitude": 40.7128, "longitude": -74.0060},
    "The Bronx": {"latitude": 40.8448, "longitude": -73.8648},
    "Brooklyn": {"latitude": 40.6782, "longitude": -73.9442},
    "Queens": {"latitude": 40.7282, "longitude": -73.7949},
    "Staten Island": {"latitude": 40.5795, "longitude": -74.1502},
}
DEFAULT_REGION = list(NYC_REGIONS.keys())[0]


st.set_page_config(
    page_title="NYC City Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====================================================================================================
# --- Data Fetching and Caching ---
# ====================================================================================================

@st.cache_data(ttl=86400) # Cache for 24 hours
def load_demographics_data():
    """Fetches NYC demographics from Gemini and caches the result."""
    # We must use asyncio.run() to execute the async function and get its result
    try:
        return asyncio.run(get_nyc_demographics())
    except Exception as e:
        st.error(f"Error running async demographic fetch: {e}")
        return None

# Load the demographic data
demographics_data = load_demographics_data()
print(demographics_data)
# Extract values with a fallback if the API call fails
if demographics_data:
    nyc_population = demographics_data.get('population', 'N/A')
    nyc_birth_rate = demographics_data.get('birth_rate', 'N/A')
else:
    nyc_population = "Data Unavailable"
    nyc_birth_rate = "Data Unavailable"
    st.warning("Could not fetch live NYC demographic data from Gemini.")

# ====================================================================================================
# --- ABOUT NEW YORK CITY SECTION (Unchanged) ---
# ====================================================================================================

st.title("🗽 New York City: The Crossroads of the World")

st.markdown("""
New York City, affectionately known as "The Big Apple," is the most populous and influential metropolis in the United States. Situated at the mouth of the Hudson River on one of the world's largest natural harbors, NYC is a **global center for finance, media, art, fashion, technology, and international diplomacy**. It is often described as the cultural capital of the world, with a dynamism fueled by its incredible diversity.

### The Five Boroughs
The city is geographically composed of five distinct boroughs, each of which is a county of New York State, consolidated into a single entity in 1898:
* **Manhattan** (New York County): The commercial, financial, and cultural heart.
* **Brooklyn** (Kings County): The most populous borough, celebrated for its artistic flair.
* **Queens** (Queens County): The most ethnically diverse urban area in the world.
* **The Bronx** (Bronx County): The birthplace of hip-hop and salsa music.
* **Staten Island** (Richmond County): Offers a quieter, more suburban environment.

### A Beacon of Global Influence
New York's position as a global city is undisputed. It hosts the headquarters of the **United Nations**, and its two largest stock exchanges, the **New York Stock Exchange (NYSE)** and **NASDAQ**, anchor the world's financial markets.

The city's reputation as a **gateway for legal immigration** has led to it being the most linguistically diverse city on the planet. This rich tapestry of cultures makes every neighborhood a unique experience.

Despite its constant rush, New York offers extensive green retreats, most famously the 843 acres of **Central Park**. The city’s robust 24/7 public transit system, the New York City Subway, allows millions to navigate this dense urban environment.
""")

st.markdown("---")

# --- Region Selection Dropdown ---
selected_region = st.selectbox(
    "Select a Borough in NYC:",
    options=list(NYC_REGIONS.keys()),
    index=0 
)

coords = NYC_REGIONS[selected_region]
latitude = coords['latitude']
longitude = coords['longitude']


# --- Fetch Weather Data ---
weather_data = get_weather_data_nyc(latitude=latitude, longitude=longitude)
if weather_data is None:
    st.error("Could not fetch weather data.")
    st.stop()

current = weather_data['current']
hourly_df = weather_data['hourly_df']
daily_df = weather_data['daily_df']

# Prepare weather variables
current_temp = str(current['temp']).replace('°C', '').strip() 
current_wind = current['wind']
current_time_gmt = current['time']
current_status = current['status']
status_icon = "https://cdn-icons-png.flaticon.com/128/869/869869.png" if current_status == "Clear" else "https://cdn-icons-png.flaticon.com/128/3353/3353748.png"

# --- Fetch Air Quality Data ---
aqi_data = get_air_quality_data_nyc(latitude=latitude, longitude=longitude)
if aqi_data is None:
    current_aqi_value, current_aqi_category, dominant_pollutant, pm25_value, pm10_value = "N/A", "Unavailable", "N/A", "N/A", "N/A"
else:
    current_aqi_value = aqi_data.get('aqi', 'N/A')
    current_aqi_category = aqi_data.get('category', 'N/A')
    dominant_pollutant = aqi_data.get('pollutant', 'N/A').upper() 
    pm25_value = aqi_data.get('pm25', 'N/A').split(' ')[0]
    pm10_value = aqi_data.get('pm10', 'N/A').split(' ')[0]

# --- Custom CSS (Unchanged) ---
# ... (Your custom_css string remains here) ...
custom_css = """
<style>
    /* Example: Add some breathing room for the cards */
    .st-emotion-cache-1e5imcs {
        gap: 1rem;
    }
    .weather-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 12px 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
        word-wrap: break-word;
    }
    .metric-icon {
        width: 35px;
        height: 35px;
        margin-bottom: 6px;
    }
    .card-title {
        font-weight: 500;
        color: #333;
    }
    .aqi-detail {
        font-size: 0.75em;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
        padding: 0 4px;
    }
    .live-indicator {
        position: absolute;
        bottom: 8px;
        right: 10px;
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75em;
        color: #10b981;
        font-weight: 600;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.6;
            transform: scale(1.1);
        }
    }
</style>
""" # Placeholder for brevity
st.markdown(custom_css, unsafe_allow_html=True)

st.sidebar.title("New York City 360 Dashboard")

# --- Main Page Title ---
st.title(f"Current Status in {selected_region}") 
st.subheader("Live Weather, Air Quality & Demographics Overview")

# ====================================================================================================
# --- Row 1: Top Cards (MODIFIED to 6 COLUMNS) ---
# ====================================================================================================

c1, c2, c3, c4, c5, c6 = st.columns(6) 

with c1:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="{status_icon}" class="metric-icon"><br><b style="font-size:1.1em;">{current_status}</b>
        <div style="font-size:0.9em; margin-top:4px;">Now</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/1163/1163661.png" class="metric-icon"><br><b style="font-size:1em;">{current_time_gmt}</b>
        <div style="font-size:0.9em; margin-top:4px;">Time (GMT)</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/4150/4150897.png" class="metric-icon"><br><b style="font-size:1em;">{current_wind}</b>
        <div style="font-size:0.9em; margin-top:4px;">Wind</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    aqi_icon = "https://cdn-icons-png.flaticon.com/128/3303/3303867.png" 
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="{aqi_icon}" class="metric-icon">
        <div class="aqi-detail">AQI: {current_aqi_value}<br/>Pollutant: {dominant_pollutant}</div>
        <div style="font-size:0.8em; margin-top:2px;"><b>PM2.5: {pm25_value} / PM10: {pm10_value}</b></div>
        <div style="font-size:0.85em; margin-top:4px;">Air Quality ({current_aqi_category})</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)

# --- MODIFICATION: New Population Card ---
with c5:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/921/921346.png" class="metric-icon">
        <br><b style="font-size:1em;">{nyc_population}</b>
        <div style="font-size:0.9em; margin-top:4px;">Population</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)

# --- MODIFICATION: New Birth Rate Card ---
with c6:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/3353/3353491.png" class="metric-icon">
        <br><b style="font-size:1em;">{nyc_birth_rate}</b>
        <div style="font-size:0.9em; margin-top:4px;">Birth Rate</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)

# ====================================================================================================
# --- NEWS TICKER SECTION ---
# ====================================================================================================

st.markdown("---")
st.subheader(f"📰 Latest Headlines in {selected_region}")

# 1. Fetch news data
news_headlines = None
try:
    headlines_list = get_news_headlines(region=selected_region)
    if isinstance(headlines_list, str):
        # Split if returned as a single string
        headlines_list = [h.strip() for h in headlines_list.split("•") if h.strip()]
    if not headlines_list:
        headlines_list = ["No recent headlines found."]
except Exception as e:
    headlines_list = [f"Could not fetch news headlines: {e}"]
    st.warning("Ensure 'requests' is installed and your NewsAPI key is set in Config.")

# Convert to HTML for vertical scrolling
headlines_html = "".join([f"<div class='headline-item'>• {h}</div>" for h in headlines_list])

# Custom CSS with centered text
vertical_scroll_css = """
<style>
.news-container {
    background-color: #f8f9fa;
    border-radius: 12px;
    padding: 10px 20px;
    height: 120px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.news-live-indicator {
    position: absolute;
    top: 10px;
    right: 15px;
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.85em;
    color: #10b981;
    font-weight: 600;
    z-index: 10;
    background: rgba(248, 249, 250, 0.9);
    padding: 4px 8px;
    border-radius: 12px;
}

.news-scroll {
    display: flex;
    flex-direction: column;
    align-items: center; /* Center horizontally */
    position: absolute;
    width: 100%;
    animation: scrollUp 30s linear infinite;
}

.headline-item {
    font-size: 1.05em;
    font-weight: 500;
    color: #222;
    text-align: center; /* Center the text */
    padding: 6px 0;
}

/* Vertical scroll animation */
@keyframes scrollUp {
    0%   { top: 100%; }
    100% { top: -100%; }
}
</style>
"""

st.markdown(vertical_scroll_css, unsafe_allow_html=True)

# Render the vertical ticker with live indicator
st.markdown(f"""
<div class="news-container">
    <div class="news-live-indicator"><span class="live-dot"></span>Live</div>
    <div class="news-scroll">
        {headlines_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ====================================================================================================
# --- Row 2: Google Map (FULL WIDTH) ---
# ====================================================================================================

st.markdown("---")
st.subheader(f"📍 Map Location: {selected_region}")

# Use a single column container for the full-width map
c_map = st.container()

# Get the city name for the map query
map_query = selected_region if selected_region == "New York City (General)" else selected_region + ", New York"
map_query = map_query.replace(' ', '+') # Format for URL

try:
    api_key = Config.GOOGLE_MAPS_API_KEY # Access the key
except (NameError, AttributeError, KeyError):
    api_key = "YOUR_API_KEY_PLACEHOLDER" # Fallback if Config isn't properly defined
    st.warning("Google Maps API key not found in Config. Displaying placeholder.")

with c_map:
    # --- MODIFICATION: Corrected the Google Maps Embed URL ---
    st.markdown(f"""
    <div style="border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px #20204033;">
        <iframe
            width="100%"
            height="350"
            style="border:0"
            loading="lazy"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            src="https://www.google.com/maps/embed/v1/place?key={api_key}&q={map_query}&center={latitude},{longitude}&zoom=11">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

# ====================================================================================================
# --- Row 3: Temperature Cards (Below the map) ---
# ====================================================================================================

st.markdown("---") # Separator after the map
col1, col2 = st.columns(2)

# Current Temperature Card
with col1:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/3731/3731872.png" class="metric-icon">
        <br><b style="font-size:1.3em;">{current_temp}°C</b>
        <div style="font-size:0.95em; margin-top:4px;">Current Temperature</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)

# Daily Max Temperature Card
if not daily_df.empty and 'Today' in daily_df['Date'].values:
    # Use .iloc[0] to get the value from the filtered Series
    max_temp_today = daily_df.loc[daily_df['Date'] == 'Today', 'Max Temp'].iloc[0]
else:
    max_temp_today = "N/A"
    
with col2:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/869/869869.png" class="metric-icon">
        <br><b style="font-size:1.3em;">{max_temp_today}</b>
        <div style="font-size:0.95em; margin-top:4px;">Daily Max Temp</div>
        <div class="live-indicator"><span class="live-dot"></span>Live</div>
    </div>
    """, unsafe_allow_html=True)

# ====================================================================================================
# --- Charts and Tables ---
# ====================================================================================================

# --- Line Chart for Hourly Data (FIXED FOR ROBUSTNESS) ---
st.markdown("---")
st.subheader("Hourly Weather (Next 24 Hours)")

# Robust check for the time column name (Time vs time)
# Assuming the column is 'Time' based on previous context, but checking just in case
time_col = 'Time'
if time_col not in hourly_df.columns:
    # Check for lowercase 'time' as a common error
    if 'time' in hourly_df.columns:
        time_col = 'time'
    else:
        st.error("Cannot display hourly chart: Missing 'Time' or 'time' column in hourly data.")
        time_col = None # Prevent the chart from trying to run

if time_col:
    try:
        st.line_chart(hourly_df.set_index(time_col)[['Temperature', 'Humidity']])
    except KeyError:
        st.error("Error generating line chart. Check if 'Temperature' and 'Humidity' columns exist.")

# --- Forecast Table ---
st.markdown("---")
st.subheader("7-Day Forecast")
st.table(daily_df.rename(columns={'Max UV Index': 'Max UV'}))