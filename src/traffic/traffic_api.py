import requests
import streamlit as st

class NYTrafficAPI:
    """Fetch live NYC traffic data from 511NY API"""

    BASE_URL = "https://511ny.org/api/getevents"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @st.cache_data(ttl=300)
    def _cached_congestion_data(_self, api_key: str):
        params = {
            "apiKey": api_key,
            "format": "json",
            "type": "event"
        }
        try:
            response = requests.get(NYTrafficAPI.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            st.error(f"Unable to fetch 511NY data: {e}")
            return []

        if not data or "events" not in data:
            return []

        traffic_data = []
        for event in data["events"]:
            try:
                lat = float(event.get("latitude", 0))
                lng = float(event.get("longitude", 0))
            except (TypeError, ValueError):
                lat, lng = None, None
            traffic_data.append({
                "road": event.get("roadwayName", "Unknown Road"),
                "description": event.get("headlineDescription", "No description"),
                "severity": event.get("severity", "Unknown"),
                "startTime": event.get("starttime", "N/A"),
                "endTime": event.get("endtime", "N/A"),
                "latitude": lat,
                "longitude": lng
            })
        return traffic_data

    def get_congestion_data(self):
        return self._cached_congestion_data(self.api_key)
