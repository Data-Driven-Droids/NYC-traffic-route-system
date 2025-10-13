import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

class TimeUtils:
    """Time-related utility functions"""
    
    @staticmethod
    def seconds_to_readable(seconds: int) -> str:
        """Convert seconds to human-readable format"""
        if seconds < 60:
            return f"{seconds} sec"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds == 0:
                return f"{minutes} min"
            return f"{minutes} min {remaining_seconds} sec"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes == 0:
                return f"{hours} hr"
            return f"{hours} hr {remaining_minutes} min"
    
    @staticmethod
    def format_duration_with_traffic(normal_duration: int, traffic_duration: int) -> str:
        """Format duration showing traffic impact"""
        normal_str = TimeUtils.seconds_to_readable(normal_duration)
        traffic_str = TimeUtils.seconds_to_readable(traffic_duration)
        
        if traffic_duration > normal_duration:
            delay = traffic_duration - normal_duration
            delay_str = TimeUtils.seconds_to_readable(delay)
            return f"{traffic_str} (normally {normal_str}, +{delay_str} due to traffic)"
        else:
            return f"{traffic_str} (normal: {normal_str})"

class DistanceUtils:
    """Distance-related utility functions"""
    
    @staticmethod
    def meters_to_readable(meters: int) -> str:
        """Convert meters to human-readable format"""
        if meters < 1000:
            return f"{meters} m"
        else:
            km = meters / 1000
            if km < 10:
                return f"{km:.1f} km"
            else:
                return f"{km:.0f} km"

class RouteDisplayUtils:
    """Utilities for displaying route information"""
    
    @staticmethod
    def create_route_comparison_df(routes: List[Dict]) -> pd.DataFrame:
        """Create a DataFrame for route comparison"""
        data = []
        
        for i, route in enumerate(routes):
            data.append({
                'Route': f"Route {i+1}: {route['summary']}",
                'Distance': route['distance']['text'],
                'Normal Time': route['duration']['text'],
                'With Traffic': route['duration_in_traffic']['text'],
                'Traffic Delay': f"{route['traffic_delay']['delay_minutes']} min",
                'Efficiency Score': f"{route['efficiency_score']}/100"
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def get_route_color(route_index: int) -> str:
        """Get color for route display based on index"""
        colors = ['#FF0000', '#0000FF', '#00FF00', '#FF8C00', '#8A2BE2']
        return colors[route_index % len(colors)]
    
    @staticmethod
    def format_traffic_status(delay_percentage: float) -> tuple:
        """Get traffic status and color based on delay percentage"""
        if delay_percentage < 10:
            return "🟢 Light Traffic", "green"
        elif delay_percentage < 25:
            return "🟡 Moderate Traffic", "orange"
        elif delay_percentage < 50:
            return "🟠 Heavy Traffic", "red"
        else:
            return "🔴 Severe Traffic", "darkred"

class UIHelpers:
    """UI-related helper functions"""
    
    @staticmethod
    def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
        """Create a metric display card"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.metric(label=title, value=value, delta=delta, delta_color=delta_color)
    
    @staticmethod
    def display_route_summary(route_data: Dict):
        """Display route summary information"""
        if not route_data or 'summary' not in route_data:
            return
        
        summary = route_data['summary']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Routes Found",
                value=summary['total_routes']
            )
        
        with col2:
            st.metric(
                label="Average Time",
                value=f"{summary['average_time_minutes']} min"
            )
        
        with col3:
            st.metric(
                label="Average Distance",
                value=f"{summary['average_distance_km']} km"
            )
        
        with col4:
            st.metric(
                label="Average Delay",
                value=f"{summary['average_delay_minutes']} min"
            )
    
    @staticmethod
    def display_best_route_highlight(best_route: Dict):
        """Display highlighted information for the best route"""
        if not best_route:
            return
        
        st.success("🏆 **Recommended Route**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Route:** {best_route['summary']}")
            st.write(f"**Distance:** {best_route['distance']['text']}")
            st.write(f"**Time with Traffic:** {best_route['duration_in_traffic']['text']}")
        
        with col2:
            traffic_status, color = RouteDisplayUtils.format_traffic_status(
                best_route['traffic_delay']['delay_percentage']
            )
            st.write(f"**Traffic Status:** {traffic_status}")
            st.write(f"**Efficiency Score:** {best_route['efficiency_score']}/100")
            
            if best_route['traffic_delay']['delay_minutes'] > 0:
                st.write(f"**Traffic Delay:** +{best_route['traffic_delay']['delay_minutes']} min")

class DataUtils:
    """Data processing utilities"""
    
    @staticmethod
    def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
        """Safely get value from dictionary"""
        try:
            return dictionary.get(key, default)
        except (AttributeError, TypeError):
            return default
    
    @staticmethod
    def format_address_for_display(address: str, max_length: int = 50) -> str:
        """Format address for display with length limit"""
        if not address:
            return "Unknown Address"
        
        if len(address) <= max_length:
            return address
        
        return address[:max_length-3] + "..."
    
    @staticmethod
    def calculate_time_savings(routes: List[Dict]) -> Dict:
        """Calculate potential time savings between routes"""
        if len(routes) < 2:
            return {}
        
        fastest_time = min(route['duration_in_traffic']['value'] for route in routes)
        slowest_time = max(route['duration_in_traffic']['value'] for route in routes)
        
        time_savings = slowest_time - fastest_time
        
        return {
            'max_savings_seconds': time_savings,
            'max_savings_minutes': round(time_savings / 60, 1),
            'fastest_route_time': TimeUtils.seconds_to_readable(fastest_time),
            'slowest_route_time': TimeUtils.seconds_to_readable(slowest_time)
        }

class ErrorHandling:
    """Error handling utilities"""
    
    @staticmethod
    def handle_api_error(error: Exception, context: str = "API call"):
        """Handle and display API errors gracefully"""
        error_msg = str(error)
        
        if "OVER_QUERY_LIMIT" in error_msg:
            st.error("🚫 API quota exceeded. Please try again later or check your billing settings.")
        elif "REQUEST_DENIED" in error_msg:
            st.error("🔑 API request denied. Please check your API key configuration.")
        elif "INVALID_REQUEST" in error_msg:
            st.error("❌ Invalid request. Please check your input addresses.")
        elif "ZERO_RESULTS" in error_msg:
            st.warning("🔍 No routes found between the specified locations.")
        else:
            st.error(f"⚠️ {context} failed: {error_msg}")
    
    @staticmethod
    def validate_session_state():
        """Validate and initialize session state variables"""
        if 'routes_data' not in st.session_state:
            st.session_state.routes_data = None
        
        if 'last_search' not in st.session_state:
            st.session_state.last_search = None
        
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []