import streamlit as st
import pandas as pd
import numpy as np
from streamlit_card import card
# The following imports are retained, but the main file structure changes for multi-page
from config.settings import Config # Assuming this exists for Google Maps key
from utils import get_weather_data_nyc # Import the new function

# --- Set Page Config (Important for multi-page) ---
st.set_page_config(
    page_title="NYC City Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Data Fetching ---
# Move this function call outside the main app logic if it's the 'Home' page
# so it can run once. For a multi-page app, this might need restructuring.
# For simplicity, we'll keep it here as this file is now the 'Weather' page.
# If this file is named 'Home.py' and 'Weather' is another page, move all weather logic.
# ASSUMING THIS FILE IS NOW THE 'WEATHER' PAGE OR 'HOME' WITH WEATHER CONTENT.

try:
    weather_data = get_weather_data_nyc()
except Exception as e:
    st.error(f"Error fetching weather data: {e}")
    weather_data = None

if weather_data is None:
    st.error("Could not fetch weather data. Please check the API connection or your utils.py function.")
    st.stop() # Stop execution if data is missing

current = weather_data['current']
hourly_df = weather_data['hourly_df']
daily_df = weather_data['daily_df']

# Extract current data for cards
current_temp = current['temp'].replace('°C', '')
current_wind = current['wind']
current_time_gmt = current['time']
current_status = current['status']
# Streamlit Card Icons (simple logic - customize as needed)
status_icon = "https://cdn-icons-png.flaticon.com/128/869/869869.png" if current_status == "Clear" else "https://cdn-icons-png.flaticon.com/128/3353/3353748.png"

# --- Custom CSS for dashboard look & cards ---
custom_css = """
<style>
.card-title { font-size: 1.3em; }
.card-metric { margin-bottom: 1em; }
.metric-icon { width: 32px; height: 32px; vertical-align: middle; margin-right: 8px;}
.weather-card { background: #232940; border-radius: 1em; padding: 1.2em 1em; box-shadow: 0 4px 16px #20204033; color: #fff; margin-bottom: 1em;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Sidebar (Simplified for Multi-Page App) ---
# Streamlit automatically adds navigation based on the 'pages' folder.
# We only add static elements here.
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/252/252025.png", width=64)
st.sidebar.title("New York City Dashboard")
st.sidebar.markdown("## Available City Data")
# The multi-page app structure replaces the radio buttons.

# --- Main Page Title ---
st.title("Current Weather in New York")
st.subheader("Live Status & Overview")

# --- Top Row: Weather Status & Interactive Google Map ---
c1, c2, c3, c4 = st.columns([1.1,1.1,1.1,1.7])
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
with c4:
    # Google Maps iframe (assuming Config.GOOGLE_MAPS_API_KEY is available)
    # NOTE: The provided URL in the original code is malformed. A correct, illustrative
    # structure is used here, assuming Config.GOOGLE_MAPS_API_KEY is accessible.
    try:
        api_key = Config.GOOGLE_MAPS_API_KEY # Access the key
    except (NameError, AttributeError):
        api_key = "YOUR_API_KEY_PLACEHOLDER" # Fallback if Config isn't properly defined
        st.warning("Google Maps API key not found in Config. Displaying placeholder.")

    st.markdown(f"""
    <div style="border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px #20204033;">
        <iframe
            width="100%"
            height="220"
            style="border:0"
            loading="lazy"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            src="https://www.google.com/maps/embed/v1/place?key={api_key}&q=New+York,NY&maptype=roadmap">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

# --- Temperature Cards ---
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/869/869869.png" class="metric-icon">
        <b>{current_temp}°C</b>
        <div style="font-size:1.1em;">Temperature</div>
    </div>
    """, unsafe_allow_html=True)

# Note: The API does not return "Feels Like" directly, using a placeholder/approximation
# For simplicity, we'll use Max Temp from the daily forecast as a placeholder.
max_temp_today = daily_df.loc[daily_df['Date'] == 'Today', 'Max Temp'].iloc[0]
with col2:
    st.markdown(f"""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/869/869869.png" class="metric-icon">
        <b>{max_temp_today}</b>
        <div style="font-size:1.1em;">Daily Max Temp</div>
    </div>
    """, unsafe_allow_html=True)

# --- Line Chart for Hourly Data ---
st.markdown("---")
st.subheader("Hourly Weather (Next 24 Hours)")
# The hourly data is filtered and set up for the chart in utils.py
st.line_chart(hourly_df[['Temperature', 'Humidity']])

# --- Forecast Table ---
st.markdown("---")
st.subheader("Forecast")
# The daily_df is formatted in utils.py to have "Today" and Max/Min Temps
st.table(daily_df.rename(columns={'Max UV Index': 'Max UV'}))