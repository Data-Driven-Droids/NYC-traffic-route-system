import streamlit as st
from datetime import datetime
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from src.maps.directions import DirectionsAPI
from src.ui.components import (
    AddressInput, RouteDisplay, SearchControls, 
    LoadingIndicator, ErrorDisplay, SearchHistory
)
from src.ui.map_display import MapDisplay, MapControls
from src.utils.validation import AddressValidator
from src.utils.helpers import ErrorHandling, UIHelpers

def initialize_app():
    """Initialize the Streamlit application"""
    st.set_page_config(
        page_title="NYC Route Optimizer",
        page_icon="🗽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79, #2e86ab);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .route-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
    .best-route {
        border-left: 5px solid #28a745;
        background-color: #f8fff9;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🗽 NYC Traffic-Aware Route Optimizer</h1>
        <p>Find the best routes in New York City with real-time traffic analysis</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with app information and controls"""
    with st.sidebar:
        st.header("ℹ️ About")
        st.write("""
        This application helps you find the most efficient routes in New York City 
        by analyzing real-time traffic conditions and providing multiple route options.
        """)
        
        st.header("🚀 Features")
        st.write("""
        • **Real-time Traffic Analysis**
        • **Multiple Route Options**
        • **Efficiency Scoring**
        • **Interactive Map Display**
        • **Address Autocomplete**
        • **NYC Boundary Validation**
        """)
        
        st.header("📊 Quick Stats")
        if 'routes_data' in st.session_state and st.session_state.routes_data:
            routes_data = st.session_state.routes_data
            if 'summary' in routes_data:
                summary = routes_data['summary']
                st.metric("Routes Found", summary['total_routes'])
                st.metric("Avg Time", f"{summary['average_time_minutes']} min")
                st.metric("Avg Distance", f"{summary['average_distance_km']} km")
        
        # Search history
        SearchHistory.render_search_history()
        
        st.header("⚙️ Settings")
        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        if st.button("Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Session reset!")
            st.experimental_rerun()

def validate_configuration():
    """Validate application configuration"""
    try:
        Config.validate()
        return True
    except ValueError as e:
        st.error(f"⚠️ **Configuration Error:** {str(e)}")
        st.write("**Setup Instructions:**")
        st.write("1. Copy `.env.example` to `.env`")
        st.write("2. Add your Google Maps API key to the `.env` file")
        st.write("3. Ensure all required APIs are enabled in Google Cloud Console")
        
        with st.expander("📋 Required APIs"):
            st.write("• Google Maps JavaScript API")
            st.write("• Google Places API (New)")
            st.write("• Google Maps Directions API")
            st.write("• Google Maps Geocoding API")
        
        return False

def main():
    """Main application function"""
    # Initialize app
    initialize_app()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Validate configuration
    if not validate_configuration():
        st.stop()
    
    # Initialize session state
    ErrorHandling.validate_session_state()
    
    # Initialize components
    address_input = AddressInput()
    directions_api = DirectionsAPI()
    map_display = MapDisplay()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📍 Route Planning")
        
        # Address input section
        with st.container():
            input_col1, input_col2 = st.columns(2)
            
            with input_col1:
                start_address, start_valid = address_input.render_address_input(
                    label="🟢 Start Address",
                    key="start_address",
                    placeholder="Enter starting location in NYC..."
                )
            
            with input_col2:
                end_address, end_valid = address_input.render_address_input(
                    label="🔴 End Address", 
                    key="end_address",
                    placeholder="Enter destination in NYC..."
                )
        
        # Search options
        SearchControls.render_search_options()
        
        # Search button
        search_clicked = SearchControls.render_search_button(
            start_address, end_address, start_valid, end_valid
        )
        
        # Process search
        if search_clicked:
            try:
                # Show loading indicator
                with st.spinner("🗺️ Calculating optimal routes..."):
                    # Get routes
                    routes_data = directions_api.get_routes(start_address, end_address)
                    
                    if routes_data:
                        st.session_state.routes_data = routes_data
                        st.session_state.last_search_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Add to search history
                        SearchHistory.add_to_history(start_address, end_address)
                        
                        st.success("✅ Routes calculated successfully!")
                        st.experimental_rerun()
                    else:
                        ErrorDisplay.show_no_routes_error()
                        
            except Exception as e:
                ErrorHandling.handle_api_error(e, "Route calculation")
    
    with col2:
        st.header("🎛️ Map Controls")
        map_options = MapControls.render_map_options()
    
    # Display results if available
    if 'routes_data' in st.session_state and st.session_state.routes_data:
        routes_data = st.session_state.routes_data
        
        # Route summary
        RouteDisplay.render_route_summary(routes_data)
        
        # Best route highlight
        RouteDisplay.render_best_route(routes_data)
        
        # Create two columns for map and route details
        map_col, details_col = st.columns([3, 2])
        
        with map_col:
            st.subheader("🗺️ Interactive Route Map")
            
            # Route selector
            selected_route = MapControls.render_route_selector(routes_data['routes'])
            
            # Display map
            try:
                map_data = map_display.render_route_map(
                    routes_data, 
                    height=map_options['height']
                )
                
                # Show map interaction info
                if map_data and map_data.get('last_object_clicked_tooltip'):
                    st.info(f"📍 Selected: {map_data['last_object_clicked_tooltip']}")
                    
            except Exception as e:
                st.error(f"Map display error: {str(e)}")
                st.write("Showing route data in table format instead:")
                RouteDisplay.render_route_comparison(routes_data)
        
        with details_col:
            st.subheader("📊 Route Analysis")
            
            # Route comparison
            RouteDisplay.render_route_comparison(routes_data)
            
            # Additional insights
            if len(routes_data['routes']) > 1:
                st.subheader("💡 Insights")
                
                best_route = routes_data['best_route']
                worst_route = max(routes_data['routes'], 
                                key=lambda x: x['duration_in_traffic']['value'])
                
                time_diff = (worst_route['duration_in_traffic']['value'] - 
                           best_route['duration_in_traffic']['value']) / 60
                
                if time_diff > 5:
                    st.info(f"💰 **Time Savings:** Choosing the best route can save you "
                           f"up to {time_diff:.1f} minutes!")
                
                # Traffic analysis
                avg_delay = sum(route['traffic_delay']['delay_percentage'] 
                              for route in routes_data['routes']) / len(routes_data['routes'])
                
                if avg_delay > 20:
                    st.warning("🚦 **Heavy Traffic Alert:** Consider departing at a different time.")
                elif avg_delay < 10:
                    st.success("🟢 **Good Traffic Conditions:** Great time to travel!")
    
    else:
        # Show welcome message when no routes are loaded
        st.info("""
        👋 **Welcome to NYC Route Optimizer!**
        
        Enter your start and end addresses above to get started. The app will:
        
        1. **Validate** your addresses are in NYC
        2. **Calculate** multiple route options
        3. **Analyze** real-time traffic conditions
        4. **Recommend** the most efficient route
        5. **Display** interactive maps and detailed comparisons
        
        💡 **Tip:** Use specific street addresses for best results!
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🗽 NYC Route Optimizer | Powered by Google Maps API | Built with Streamlit</p>
        <p><small>Real-time traffic data updates every 5 minutes</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()