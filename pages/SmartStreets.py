import streamlit as st
import sys, os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.maps.directions import DirectionsAPI
from src.traffic.traffic_api import NYTrafficAPI
from src.ui.map_display import MapDisplay
from src.ui.components import RouteDisplay
from config.settings import Config

# 511NY API Key
API_KEY_511 = "fd7bd4600ee94588be5a28d448666112"

def get_severity_color(severity):
    """Return color based on severity level"""
    severity_map = {
        "Critical": "#dc2626",
        "Major": "#ea580c",
        "Moderate": "#f59e0b",
        "Minor": "#84cc16",
        "Unknown": "#6b7280"
    }
    return severity_map.get(severity, "#6b7280")

def get_severity_emoji(severity):
    """Return emoji based on severity level"""
    severity_map = {
        "Critical": "🔴",
        "Major": "🟠",
        "Moderate": "🟡",
        "Minor": "🟢",
        "Unknown": "⚪"
    }
    return severity_map.get(severity, "⚪")

def render_congestion_card(event, index):
    """Render a modern card for each congestion event"""
    severity = event.get("severity", "Unknown")
    color = get_severity_color(severity)
    emoji = get_severity_emoji(severity)
    
    # Build location string with light colors
    location_str = ""
    if event.get("latitude") and event.get("longitude"):
        location_str = f'<div style="margin-top: 0.75rem; font-size: 0.85rem; color: #d1d5db;">📍 Location: {event.get("latitude")}, {event.get("longitude")}</div>'
    
    # Single HTML block - all in one to avoid rendering issues
    # Using light colors for dark theme compatibility
    html = f'''
<div style="background: linear-gradient(135deg, {color}25 0%, {color}15 100%); border-left: 4px solid {color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
        <div style="flex: 1;">
            <div style="font-size: 0.85rem; color: #9ca3af; font-weight: 500; margin-bottom: 0.25rem;">#{index + 1} • CONGESTION ALERT</div>
            <h3 style="margin: 0; color: #f3f4f6; font-size: 1.25rem; font-weight: 700;">{emoji} {event.get("road", "Unknown Road")}</h3>
        </div>
        <div style="background-color: {color}; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{severity}</div>
    </div>
    <div style="color: #e5e7eb; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">{event.get("description", "No description available")}</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
        <div style="background-color: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.7rem; color: #9ca3af; font-weight: 600; margin-bottom: 0.25rem;">START TIME</div>
            <div style="font-size: 0.9rem; color: #f3f4f6; font-weight: 600;">⏰ {event.get("startTime", "N/A")}</div>
        </div>
        <div style="background-color: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.7rem; color: #9ca3af; font-weight: 600; margin-bottom: 0.25rem;">END TIME</div>
            <div style="font-size: 0.9rem; color: #f3f4f6; font-weight: 600;">⏱️ {event.get("endTime", "N/A")}</div>
        </div>
    </div>
    {location_str}
</div>
'''
    
    st.markdown(html, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Smart Streets | NYC Traffic", layout="wide", page_icon="🚦")

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #0e4d92 0%, #1e3a8a 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 2rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 800;">🚦 NYC Traffic Congestion Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95;">Real-time Congestion Monitoring • Live Traffic Events • Smart Analytics</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize components
    traffic_api = NYTrafficAPI(API_KEY_511)
    directions_api = DirectionsAPI()
    map_display = MapDisplay()

    # Sidebar Controls
    st.sidebar.markdown("### ⚙️ Dashboard Controls")
    refresh_btn = st.sidebar.button("🔄 Refresh Traffic Data", use_container_width=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Filters")
    
    # Fetch traffic data
    try:
        if refresh_btn or "congestion_data" not in st.session_state:
            with st.spinner("🔍 Fetching live congestion data..."):
                st.session_state["congestion_data"] = traffic_api.get_congestion_data()
                st.session_state["traffic_events"] = traffic_api.get_events()
        
        congestion_data = st.session_state.get("congestion_data", [])
        traffic_events = st.session_state.get("traffic_events", [])
        
        # Severity filter
        all_severities = list(set([event.get("severity", "Unknown") for event in congestion_data]))
        selected_severities = st.sidebar.multiselect(
            "Severity Level",
            options=all_severities,
            default=all_severities
        )
        
        # Limit results for performance
        max_results = st.sidebar.slider(
            "Max Results to Display",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            help="Limit the number of results to improve performance"
        )
        
        # Filter data
        filtered_data = [event for event in congestion_data if event.get("severity", "Unknown") in selected_severities]
        
        # Apply max results limit
        total_filtered = len(filtered_data)
        
        # Sort options
        sort_by = st.sidebar.selectbox(
            "Sort By",
            ["Severity (High to Low)", "Severity (Low to High)", "Road Name", "Start Time"]
        )
        
        # Apply sorting
        severity_order = {"Critical": 0, "Major": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
        if sort_by == "Severity (High to Low)":
            filtered_data.sort(key=lambda x: severity_order.get(x.get("severity", "Unknown"), 4))
        elif sort_by == "Severity (Low to High)":
            filtered_data.sort(key=lambda x: severity_order.get(x.get("severity", "Unknown"), 4), reverse=True)
        elif sort_by == "Road Name":
            filtered_data.sort(key=lambda x: x.get("road", ""))
        elif sort_by == "Start Time":
            filtered_data.sort(key=lambda x: x.get("startTime", ""))
        
        # Limit results after sorting
        filtered_data = filtered_data[:max_results]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Statistics")
        st.sidebar.metric("Total Congestion Spots", len(congestion_data))
        st.sidebar.metric("After Filters", total_filtered)
        st.sidebar.metric("Displaying", len(filtered_data))
        st.sidebar.metric("Total Traffic Events", len(traffic_events))
        
        # Main Dashboard
        # KPI Metrics
        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        critical_count = len([e for e in congestion_data if e.get("severity") == "Critical"])
        major_count = len([e for e in congestion_data if e.get("severity") == "Major"])
        moderate_count = len([e for e in congestion_data if e.get("severity") == "Moderate"])
        minor_count = len([e for e in congestion_data if e.get("severity") == "Minor"])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc262615 0%, #dc262605 100%); 
                        border-left: 4px solid #dc2626; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #dc2626;">{critical_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🔴 CRITICAL</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ea580c15 0%, #ea580c05 100%); 
                        border-left: 4px solid #ea580c; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #ea580c;">{major_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🟠 MAJOR</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f59e0b15 0%, #f59e0b05 100%); 
                        border-left: 4px solid #f59e0b; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #f59e0b;">{moderate_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🟡 MODERATE</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #84cc1615 0%, #84cc1605 100%); 
                        border-left: 4px solid #84cc16; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #84cc16;">{minor_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🟢 MINOR</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["🗺️ Congestion Map", "📋 Congestion Hotspots", "🚨 Traffic Events"])
        
        with tab1:
            st.markdown("### 🗺️ Live Congestion Map")
            if congestion_data:
                center_location = {"lat": 40.7128, "lng": -74.0060}
                map_display.render_traffic_overlay_map(center_location)
            else:
                st.info("No congestion data available to display on map.")
        
        with tab2:
            st.markdown("### 📋 Active Congestion Hotspots")
            
            # Filter for congestion-specific events (construction, roadwork)
            congestion_types = ['roadwork', 'construction', 'road_closure', 'lane_closure']
            congestion_filtered = [e for e in filtered_data if e.get('eventType', '').lower() in congestion_types]
            
            if congestion_filtered:
                st.markdown(f"**Showing {len(congestion_filtered)} congestion hotspots (roadwork, construction, closures)**")
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Render cards
                for idx, event in enumerate(congestion_filtered):
                    render_congestion_card(event, idx)
            else:
                st.info("🎉 No congestion hotspots found. These include roadwork, construction, and road closures.")
        
        with tab3:
            st.markdown("### 🚨 All Traffic Events & Incidents")
            
            # Filter for incident-related events (accidents, incidents, weather, etc.)
            # Show everything that's NOT roadwork/construction
            congestion_types = ['roadwork', 'construction', 'road_closure', 'lane_closure']
            incidents_filtered = [e for e in traffic_events if e.get('eventType', '').lower() not in congestion_types]
            
            if incidents_filtered:
                # Limit traffic events too
                limited_events = incidents_filtered[:max_results]
                
                if len(incidents_filtered) > len(limited_events):
                    st.info(f"ℹ️ Showing top {len(limited_events)} of {len(incidents_filtered)} traffic incidents. Adjust the 'Max Results' slider to see more.")
                else:
                    st.markdown(f"**{len(incidents_filtered)} active traffic incidents (accidents, weather, special events)**")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                for idx, event in enumerate(limited_events):
                    render_congestion_card(event, idx)
            else:
                st.info("✅ No active traffic incidents at this time.")
        
        # Route Planning Section
        st.markdown("---")
        st.markdown("### 🚗 Route Planning")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start = st.text_input("🟢 Start Address", "Times Square, NYC")
        with col2:
            end = st.text_input("🔴 Destination", "Central Park, NYC")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            route_btn = st.button("🚦 Get Route", use_container_width=True)
        
        if route_btn:
            try:
                with st.spinner("🔍 Finding optimal route..."):
                    routes_data = directions_api.get_routes(start, end)
                    st.session_state["routes_data"] = routes_data
            except Exception as e:
                st.error(f"❌ Error fetching route: {e}")
        
        # Routes section
        if "routes_data" in st.session_state:
            st.markdown("### 🗺️ Route Visualization")
            routes_data = st.session_state["routes_data"]
            
            map_display.render_route_map(routes_data)
            RouteDisplay.render_route_comparison(routes_data)
            
            if len(routes_data.get("routes", [])) > 1:
                best = routes_data["best_route"]
                alternate = routes_data["routes"][1]
                time_diff = (alternate["duration_in_traffic"]["value"] - best["duration_in_traffic"]["value"]) / 60
                
                st.info(f"💡 **Alternate Route Insight:** The alternate route may take **{time_diff:.1f} minutes** longer due to current traffic conditions.")
    
    except Exception as e:
        st.error(f"❌ Unable to fetch traffic data: {e}")
        st.info("Please try refreshing the page or check your API connection.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#888; padding: 1rem;">
        <strong>NYC Smart Streets Dashboard</strong> | Powered by 511NY & Google Maps | Auto-refresh every 5 minutes<br>
        <small>Data updated in real-time from NYC traffic monitoring systems</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
