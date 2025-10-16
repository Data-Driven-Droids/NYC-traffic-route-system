import streamlit as st
import pandas as pd
import numpy as np
# NOTE: Assuming config.settings.Config and utils.py are accessible
from config.settings import Config 
from utils import get_weather_data_nyc, get_air_quality_data_nyc, get_news_headlines # Added get_news_headlines

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
# --- ABOUT NEW YORK CITY SECTION (Approx. 500 Words) ---
# ====================================================================================================

st.title("🗽 New York City: The Crossroads of the World")

st.markdown("""
New York City, affectionately known as "The Big Apple," is the most populous and influential metropolis in the United States. Situated at the mouth of the Hudson River on one of the world's largest natural harbors, NYC is a **global center for finance, media, art, fashion, technology, and international diplomacy**. It is often described as the cultural capital of the world, with a dynamism fueled by its incredible diversity.

### The Five Boroughs
The city is geographically composed of five distinct boroughs, each of which is a county of New York State, consolidated into a single entity in 1898:
* **Manhattan** (New York County): The commercial, financial, and cultural heart, home to Wall Street, Times Square, Central Park, and the iconic skyscraper skyline.
* **Brooklyn** (Kings County): The most populous borough, celebrated for its artistic flair, historic brownstones, and vibrant neighborhood diversity, from Williamsburg to Coney Island.
* **Queens** (Queens County): The most ethnically diverse urban area in the world, hosting both JFK and LaGuardia airports and major sports venues like the USTA Billie Jean King National Tennis Center.
* **The Bronx** (Bronx County): The birthplace of hip-hop and salsa music, featuring Yankee Stadium and expansive green spaces like the Bronx Zoo and Pelham Bay Park.
* **Staten Island** (Richmond County): Offers a quieter, more suburban environment, connected to Manhattan by the famous free Staten Island Ferry, which provides stunning views of the Statue of Liberty.

### A Beacon of Global Influence
New York's position as a global city is undisputed. It hosts the headquarters of the **United Nations**, solidifying its role in world affairs. Its two largest stock exchanges, the **New York Stock Exchange (NYSE)** and **NASDAQ**, anchor the world's financial markets. Furthermore, its influence in the arts—from the Broadway Theater District to world-class institutions like the Metropolitan Museum of Art—shapes global trends in entertainment and culture.

The city’s reputation as a **gateway for legal immigration** has led to it being the most linguistically diverse city on the planet, with hundreds of languages spoken. This rich tapestry of cultures makes every neighborhood a unique experience, from the concentrated Chinese populations in Flushing and Manhattan's Chinatown to the historic Italian-American communities.

Despite its constant rush and notorious traffic, New York offers extensive green retreats, most famously the 843 acres of **Central Park**. The city’s robust 24/7 public transit system, the New York City Subway, allows millions of residents and visitors to navigate this dense urban environment.

In essence, New York City is a relentless, ever-evolving megacity—a powerful symbol of ambition, resilience, and the enduring promise of a place where people from every corner of the globe can contribute to a collective, unforgettable energy.
""")

st.markdown("---") 

# --- Region Selection Dropdown ---
selected_region = st.selectbox(
    "Select a Region in NYC:",
    options=list(NYC_REGIONS.keys()),
    index=0 # Default to New York City (General)
)

# Get coordinates for the selected region
coords = NYC_REGIONS[selected_region]
latitude = coords['latitude']
longitude = coords['longitude']


# --- Fetch Weather Data ---
weather_data = None
try:
    # Pass latitude and longitude to the fetching function
    weather_data = get_weather_data_nyc(latitude=latitude, longitude=longitude)
except Exception as e:
    st.error(f"Error fetching weather data: {e}")

if weather_data is None:
    st.error("Could not fetch weather data. Please check the API connection or your utils.py function.")
    st.stop()

current = weather_data['current']
hourly_df = weather_data['hourly_df']
daily_df = weather_data['daily_df']

# Prepare weather variables (handle potential mock data string formats)
current_temp = str(current['temp']).replace('°C', '').strip() 
current_wind = current['wind']
current_time_gmt = current['time']
current_status = current['status']
# Streamlit Card Icons (simple logic - customize as needed)
status_icon = "https://cdn-icons-png.flaticon.com/128/869/869869.png" if current_status == "Clear" else "https://cdn-icons-png.flaticon.com/128/3353/3353748.png"

# --- Fetch Air Quality Data ---
aqi_data = None
try:
    # Pass latitude and longitude to the fetching function
    aqi_data = get_air_quality_data_nyc(latitude=latitude, longitude=longitude)
except Exception as e:
    st.error(f"Error fetching air quality data: {e}")

if aqi_data is None:
    # Set default/placeholder values if data fetching fails
    current_aqi_value = "N/A"
    current_aqi_category = "Data Unavailable"
    dominant_pollutant = "N/A"
    pm25_value = "N/A"
    pm10_value = "N/A"
else:
    current_aqi_value = aqi_data.get('aqi', 'N/A')
    current_aqi_category = aqi_data.get('category', 'N/A')
    dominant_pollutant = aqi_data.get('pollutant', 'N/A').upper() 
    pm25_raw = aqi_data.get('pm25', 'N/A')
    pm10_raw = aqi_data.get('pm10', 'N/A')
    # Clean up the string values from mock data
    pm25_value = pm25_raw.split(' ')[0] if pm25_raw != 'N/A' else 'N/A'
    pm10_value = pm10_raw.split(' ')[0] if pm10_raw != 'N/A' else 'N/A'

# --- Custom CSS for dashboard look & cards & marquee ---
custom_css = """
<style>
.card-title { font-size: 1.3em; }
.card-metric { margin-bottom: 1em; }
.metric-icon { width: 32px; height: 32px; vertical-align: middle; margin-right: 8px;}
.weather-card { 
    background: #232940; 
    border-radius: 1em; 
    padding: 1.2em 1em; 
    box-shadow: 0 4px 16px #20204033; 
    color: #fff; 
    margin-bottom: 1em;
    min-height: 120px; /* Ensure uniform height */
}
.aqi-detail { font-size: 0.9em; line-height: 1.4; margin-top: 10px; } 

/* Adjust the dropdown selector font size for better visual flow */
div[data-testid="stForm"] > div:first-child > div:first-child .stSelectbox {
    font-size: 1.2em;
}

/* --- New Marquee CSS for continuous scroll --- */
.news-ticker-container {
    background-color: #f0f2f6; /* Light gray background */
    padding: 10px 0;
    margin-top: 20px;
    white-space: nowrap;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-radius: 8px;
}
.news-ticker-content {
    display: inline-block;
    padding-left: 100%; /* Start off-screen */
    animation: marquee 30s linear infinite; /* Adjust time for speed */
    font-size: 1.1em;
    font-weight: 500;
    color: #333333;
}
@keyframes marquee {
    0%   { transform: translate(0, 0); }
    100% { transform: translate(-100%, 0); } /* Scrolls the length of the content */
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.sidebar.title("New York City 360 Dashboard")

# --- Main Page Title ---
st.title(f"Current Weather & Air Quality in {selected_region}") 
st.subheader("Live Status & Overview")

# ====================================================================================================
# --- Row 1: Weather Status, Time, Wind, and AQI (4 EQUAL COLUMNS) ---
# ====================================================================================================

c1, c2, c3, c4 = st.columns(4) 
with c1:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="{status_icon}" class="metric-icon">
        <br><b>{current_status}</b>
        <div style="font-size:1.1em;">Now</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/1163/1163661.png" class="metric-icon">
        <br><b>{current_time_gmt}</b>
        <div style="font-size:1.1em;">Time (GMT)</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/4150/4150897.png" class="metric-icon">
        <br><b>{current_wind}</b>
        <div style="font-size:1.1em;">Wind</div>
    </div>
    """, unsafe_allow_html=True)
# AQI CARD
with c4:
    aqi_icon = "https://cdn-icons-png.flaticon.com/128/3303/3303867.png" 
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="{aqi_icon}" class="metric-icon">
        <div class="aqi-detail">
             AQI: {current_aqi_value} 
             <br/>Pollutant: {dominant_pollutant}
        </div>
        <br><b>PM2.5: {pm25_value} / PM10: {pm10_value}</b>
        <div style="font-size:1.1em;">Air Quality ({current_aqi_category})</div>
    </div>
    """, unsafe_allow_html=True)


# ====================================================================================================
# --- NEWS TICKER SECTION ---
# ====================================================================================================

st.markdown("---")
st.subheader(f"⚡ Today's Headlines in {selected_region}")

# 1. Fetch news data
news_headlines = None
try:
    # Fetch news headlines for the selected region
    news_headlines = get_news_headlines(region=selected_region)
except Exception as e:
    news_headlines = f"Could not fetch news headlines: {e}"
    st.warning("Ensure 'requests' is installed and your NewsAPI key is set in Config.")


# 2. Display the headlines with the custom marquee CSS
st.markdown(f"""
<div class="news-ticker-container">
    <div class="news-ticker-content">
        {news_headlines}
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
except (NameError, AttributeError):
    api_key = "YOUR_API_KEY_PLACEHOLDER" # Fallback if Config isn't properly defined
    st.warning("Google Maps API key not found in Config. Displaying placeholder.")

with c_map:
    # Update the iframe src to use the selected region's coordinates/query
    # NOTE: The Google Maps URL must be properly formed for security and functionality.
    # The URL below is a general embed format which often requires a full API key.
    # It uses latitude/longitude for centering and a query for a marker.
    st.markdown(f"""
    <div style="border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px #20204033;">
        <iframe
            width="100%"
            height="350"  style="border:0"
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
        <br><b>{current_temp}°C</b>
        <div style="font-size:1.1em;">Current Temperature</div>
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
        <br><b>{max_temp_today}</b>
        <div style="font-size:1.1em;">Daily Max Temp</div>
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