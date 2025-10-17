import streamlit as st
import sys, os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.maps.directions import DirectionsAPI
from src.traffic.traffic_api import NYTrafficAPI
from src.ui.map_display import MapDisplay
from src.ui.components import RouteDisplay
from config.settings import Config

# 511NY API Key
API_KEY_511 = "fd7bd4600ee94588be5a28d448666112"

def main():
    st.set_page_config(page_title="Smart Streets | NYC Traffic", layout="wide")

    st.markdown("""
    <div style="text-align:center; background-color:#0e4d92; color:white; padding:1rem; border-radius:10px;">
        <h1>🛣️ Smart Streets NYC</h1>
        <p>Real-time Traffic Congestion • Alternate Routes • Smart Map Visualization</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize APIs and components
    traffic_api = NYTrafficAPI(API_KEY_511)
    directions_api = DirectionsAPI()
    map_display = MapDisplay()

    # Sidebar
    st.sidebar.header("⚙️ Map Controls")
    show_traffic = st.sidebar.checkbox("Show Live Traffic", value=True)
    show_alt_routes = st.sidebar.checkbox("Show Alternate Routes", value=True)
    refresh_btn = st.sidebar.button("🔄 Refresh Traffic Data")

    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        start = st.text_input("🟢 Start Address", "Times Square, NYC")
    with col2:
        end = st.text_input("🔴 Destination", "Central Park, NYC")

    # Route button
    if st.button("🚦 Show Route"):
        try:
            with st.spinner("Fetching optimal routes and live traffic data..."):
                routes_data = directions_api.get_routes(start, end)
                st.session_state["routes_data"] = routes_data
        except Exception as e:
            st.error(f"Error fetching route: {e}")

    # Live Traffic Section
    if show_traffic:
        st.subheader("🚧 Live Traffic Conditions (511NY)")
        try:
            if refresh_btn or "traffic_data" not in st.session_state:
                st.session_state["traffic_data"] = traffic_api.get_congestion_data()

            traffic_data = st.session_state["traffic_data"]
            st.success(f"✅ Loaded {len(traffic_data)} active traffic alerts across NYC.")

            with st.expander("📋 View Traffic Details"):
                st.dataframe(traffic_data)

            # Center at NYC
            center_location = {"lat": 40.7128, "lng": -74.0060}
            map_display.render_traffic_overlay_map(center_location)

        except Exception as e:
            st.error(f"Unable to fetch 511NY data: {e}")

    # Route Visualization
    if "routes_data" in st.session_state:
        st.subheader("🗺️ Route Visualization")
        routes_data = st.session_state["routes_data"]

        map_display.render_route_map(routes_data)
        RouteDisplay.render_route_comparison(routes_data)

        if show_alt_routes and len(routes_data.get("routes", [])) > 1:
            st.info("💡 Alternate Route Insights:")
            best = routes_data["best_route"]
            alternate = routes_data["routes"][1]
            time_diff = (alternate["duration_in_traffic"]["value"] - best["duration_in_traffic"]["value"]) / 60
            st.write(f"🚗 Alternate route may take **{time_diff:.1f} minutes** longer due to traffic.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#888;">
        NYC Smart Streets | Powered by 511NY & Google Maps | Updated every 5 minutes
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
