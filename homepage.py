import streamlit as st
import pandas as pd
import numpy as np
from streamlit_card import card
from config.settings import Config

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

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/252/252025.png", width=64)
st.sidebar.title("New York")
st.sidebar.write("(Tap to go back to home)")
st.sidebar.markdown("## Available City Data")
menu = st.sidebar.radio("", ["Weather", "Environment", "Health", "Education", "About City"], index=0)

# --- Live Status ---
st.markdown("""
<div style='display: flex; align-items: center; gap:12px'>
    <span style='color:limegreen; font-weight:bold;'>● ONLINE</span>
    <span style='color:red; font-weight:bold;'>● DISCONNECTED</span>
</div>
""", unsafe_allow_html=True)

# --- Top Row: Weather Status & Interactive Google Map ---
c1, c2, c3, c4 = st.columns([1.1,1.1,1.1,1.7])
with c1:
    st.markdown("""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/869/869869.png" class="metric-icon">
        <br><b>Clear</b>
        <div style="font-size:1.1em;">Now</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/1163/1163661.png" class="metric-icon">
        <br><b>3:44</b>
        <div style="font-size:1.1em;">Time</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="weather-card card-title">
        <img src="https://cdn-icons-png.flaticon.com/128/4150/4150897.png" class="metric-icon">
        <br><b>3.6 Km/h 10°N</b>
        <div style="font-size:1.1em;">Wind</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div style="border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px #20204033;">
        <iframe
            width="100%"
            height="220"
            style="border:0"
            loading="lazy"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            src="https://www.google.com/maps/embed/v1/place?key={Config.GOOGLE_MAPS_API_KEY}&q=New+York,NY&maptype=roadmap">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

# --- Temperature Cards ---
col1, col2 = st.columns(2)
col1.markdown("""
<div class="weather-card card-title">
    <img src="https://cdn-icons-png.flaticon.com/128/869/869869.png" class="metric-icon">
    <b>22.8°C</b>
    <div style="font-size:1.1em;">Temperature</div>
</div>
""", unsafe_allow_html=True)
col2.markdown("""
<div class="weather-card card-title">
    <img src="https://cdn-icons-png.flaticon.com/128/869/869869.png" class="metric-icon">
    <b>24.9°C</b>
    <div style="font-size:1.1em;">Feels Like</div>
</div>
""", unsafe_allow_html=True)

# --- Line Chart for Hourly Data ---
st.subheader("Hourly Weather")
hourly = pd.DataFrame({
    "Time": [f"{h}:00" for h in range(24)],
    "Temperature": np.random.uniform(21,30,24),
    "Humidity": np.random.uniform(60,85,24),
})
st.line_chart(hourly.set_index('Time'))

# --- Forecast Table ---
st.subheader("Forecast")
forecast = pd.DataFrame({
    "Date": ["Today", "13/8", "14/8"],
    "Max Temp": ["30.3°C", "33.5°C", "31.6°C"],
    "Min Temp": ["22.1°C", "21.9°C", "22.1°C"],
    "Humidity": ["74.0%", "69.0%", "63.0%"]
})
st.table(forecast)
