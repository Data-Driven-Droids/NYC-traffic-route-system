import requests
import streamlit as st

class NYTrafficAPI:
    """Fetch live NYC traffic data from 511NY API"""

    BASE_URL = "https://511ny.org/api/getevents"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @st.cache_data(ttl=300)
    def _cached_congestion_data(_self, api_key: str, event_type: str = "event"):
        params = {
            "apiKey": api_key,
            "format": "json",
            "type": event_type
        }
        try:
            response = requests.get(NYTrafficAPI.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            st.error(f"Unable to fetch 511NY data: {e}")
            return []

        # API returns a direct list, not a dict with "events" key
        if not data or not isinstance(data, list):
            return []

        traffic_data = []
        for event in data:
            try:
                lat = float(event.get("Latitude", 0))
                lng = float(event.get("Longitude", 0))
            except (TypeError, ValueError):
                lat, lng = None, None
            
            traffic_data.append({
                "road": event.get("RoadwayName", "Unknown Road"),
                "description": event.get("Description", "No description"),
                "severity": event.get("Severity", "Unknown"),
                "startTime": event.get("StartDate", "N/A"),
                "endTime": event.get("PlannedEndDate", "N/A"),
                "latitude": lat,
                "longitude": lng,
                "eventType": event.get("EventType", "Unknown"),
                "eventSubType": event.get("EventSubType", ""),
                "region": event.get("RegionName", ""),
                "county": event.get("CountyName", "")
            })
        return traffic_data

    def get_congestion_data(self):
        return self._cached_congestion_data(self.api_key, "congestion")

    def get_events(self, event_type: str = "event"):
        return self._cached_congestion_data(self.api_key, event_type)
