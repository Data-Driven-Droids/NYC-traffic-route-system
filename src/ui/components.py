import streamlit as st
from typing import List, Dict, Optional, Tuple
from src.maps.places_api import PlacesAPI
from src.utils.validation import AddressValidator, InputSanitizer
from src.utils.helpers import UIHelpers, RouteDisplayUtils, DataUtils

class AddressInput:
    """Address input component with autocomplete functionality"""
    
    def __init__(self):
        self.places_api = PlacesAPI()
        self.validator = AddressValidator()
        self.sanitizer = InputSanitizer()
    
    def render_address_input(self, label: str, key: str, placeholder: str = "") -> Tuple[str, bool]:
        """
        Render address input with validation
        
        Args:
            label: Input field label
            key: Unique key for the input
            placeholder: Placeholder text
            
        Returns:
            Tuple of (address, is_valid)
        """
        # Create input field
        address = st.text_input(
            label=label,
            key=key,
            placeholder=placeholder,
            help="Enter a valid address in New York City"
        )
        
        if not address:
            return "", False
        
        # Sanitize input
        sanitized_address = self.sanitizer.sanitize_address(address)
        
        # Show autocomplete suggestions if address is being typed
        if len(sanitized_address) >= 3:
            self._show_autocomplete_suggestions(sanitized_address, key)
        
        # Validate address
        is_valid, message, _ = self.validator.validate_nyc_address(sanitized_address)
        
        # Display validation feedback
        if sanitized_address:
            if is_valid:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
                # Show suggestions for corrections
                suggestions = self.validator.suggest_address_corrections(sanitized_address)
                if suggestions:
                    st.info("💡 Did you mean:")
                    for suggestion in suggestions[:3]:
                        st.write(f"   • {suggestion}")
        
        return sanitized_address, is_valid
    
    def _show_autocomplete_suggestions(self, address: str, key: str):
        """Show autocomplete suggestions"""
        try:
            suggestions = self.places_api.autocomplete(address)
            if suggestions and len(suggestions) > 0:
                with st.expander("📍 Address Suggestions", expanded=False):
                    for suggestion in suggestions[:5]:
                        if st.button(
                            suggestion['description'], 
                            key=f"{key}_suggestion_{suggestion['place_id']}"
                        ):
                            st.session_state[key] = suggestion['description']
                            st.experimental_rerun()
        except Exception:
            pass  # Silently handle autocomplete errors

class RouteDisplay:
    """Component for displaying route information and comparisons"""
    
    @staticmethod
    def render_route_summary(routes_data: Dict):
        """Render route summary section"""
        if not routes_data or 'summary' not in routes_data:
            return
        
        st.subheader("📊 Route Analysis Summary")
        UIHelpers.display_route_summary(routes_data)
        
        # Show time savings potential
        if 'routes' in routes_data and len(routes_data['routes']) > 1:
            savings = DataUtils.calculate_time_savings(routes_data['routes'])
            if savings:
                st.info(
                    f"💡 **Time Savings Opportunity:** Choose the fastest route to save up to "
                    f"{savings['max_savings_minutes']} minutes compared to the slowest option."
                )
    
    @staticmethod
    def render_best_route(routes_data: Dict):
        """Render best route recommendation"""
        if not routes_data or 'best_route' not in routes_data:
            return
        
        best_route = routes_data['best_route']
        if best_route:
            UIHelpers.display_best_route_highlight(best_route)
    
    @staticmethod
    def render_route_comparison(routes_data: Dict):
        """Render detailed route comparison table"""
        if not routes_data or 'routes' not in routes_data:
            return
        
        routes = routes_data['routes']
        if not routes:
            return
        
        st.subheader("🛣️ Route Comparison")
        
        # Create comparison DataFrame
        df = RouteDisplayUtils.create_route_comparison_df(routes)
        
        # Display table with styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Show detailed route information
        RouteDisplay._render_detailed_routes(routes)
    
    @staticmethod
    def _render_detailed_routes(routes: List[Dict]):
        """Render detailed information for each route"""
        st.subheader("📋 Detailed Route Information")
        
        for i, route in enumerate(routes):
            with st.expander(f"Route {i+1}: {route['summary']}", expanded=(i == 0)):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📍 Route Details:**")
                    st.write(f"• **From:** {DataUtils.format_address_for_display(route['start_address'])}")
                    st.write(f"• **To:** {DataUtils.format_address_for_display(route['end_address'])}")
                    st.write(f"• **Distance:** {route['distance']['text']}")
                    st.write(f"• **Normal Time:** {route['duration']['text']}")
                    st.write(f"• **With Traffic:** {route['duration_in_traffic']['text']}")
                
                with col2:
                    st.write("**🚦 Traffic Information:**")
                    traffic_status, color = RouteDisplayUtils.format_traffic_status(
                        route['traffic_delay']['delay_percentage']
                    )
                    st.write(f"• **Status:** {traffic_status}")
                    st.write(f"• **Delay:** +{route['traffic_delay']['delay_minutes']} minutes")
                    st.write(f"• **Delay %:** {route['traffic_delay']['delay_percentage']}%")
                    st.write(f"• **Efficiency Score:** {route['efficiency_score']}/100")
                
                # Show warnings if any
                if route.get('warnings'):
                    st.warning("⚠️ **Route Warnings:**")
                    for warning in route['warnings']:
                        st.write(f"• {warning}")

class SearchControls:
    """Search controls and options component"""
    
    @staticmethod
    def render_search_options():
        """Render search options and controls"""
        with st.expander("⚙️ Search Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                departure_option = st.selectbox(
                    "Departure Time",
                    ["Now", "Custom Time"],
                    help="Choose when you want to depart"
                )
                
                if departure_option == "Custom Time":
                    departure_date = st.date_input("Departure Date")
                    departure_time = st.time_input("Departure Time")
                    # Store custom time in session state
                    st.session_state['custom_departure'] = {
                        'date': departure_date,
                        'time': departure_time
                    }
                else:
                    st.session_state['custom_departure'] = None
            
            with col2:
                traffic_model = st.selectbox(
                    "Traffic Model",
                    ["Best Guess", "Optimistic", "Pessimistic"],
                    help="How to estimate traffic conditions"
                )
                
                max_routes = st.slider(
                    "Maximum Routes",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="Number of alternative routes to find"
                )
                
                # Store options in session state
                st.session_state['search_options'] = {
                    'traffic_model': traffic_model.lower().replace(' ', '_'),
                    'max_routes': max_routes
                }
    
    @staticmethod
    def render_search_button(start_address: str, end_address: str, 
                           start_valid: bool, end_valid: bool) -> bool:
        """
        Render search button with validation
        
        Returns:
            True if search should be performed
        """
        # Check if both addresses are valid
        can_search = start_valid and end_valid and start_address and end_address
        
        # Create search button
        search_clicked = st.button(
            "🔍 Find Best Routes",
            type="primary",
            disabled=not can_search,
            use_container_width=True
        )
        
        # Show validation messages
        if not can_search:
            if not start_address or not end_address:
                st.warning("⚠️ Please enter both start and end addresses")
            elif not start_valid or not end_valid:
                st.error("❌ Please fix address validation errors before searching")
        
        return search_clicked and can_search

class LoadingIndicator:
    """Loading indicator component"""
    
    @staticmethod
    def show_route_calculation():
        """Show loading indicator for route calculation"""
        with st.spinner("🗺️ Calculating optimal routes with real-time traffic data..."):
            progress_bar = st.progress(0)
            
            # Simulate progress steps
            import time
            steps = [
                "Validating addresses...",
                "Fetching route options...",
                "Analyzing traffic conditions...",
                "Calculating efficiency scores...",
                "Preparing results..."
            ]
            
            for i, step in enumerate(steps):
                st.text(step)
                progress_bar.progress((i + 1) / len(steps))
                time.sleep(0.5)  # Small delay for visual effect
            
            progress_bar.empty()

class ErrorDisplay:
    """Error display component"""
    
    @staticmethod
    def show_no_routes_error():
        """Show error when no routes are found"""
        st.error("🚫 **No Routes Found**")
        st.write("This could be due to:")
        st.write("• Invalid or unreachable addresses")
        st.write("• Addresses outside NYC area")
        st.write("• Temporary API issues")
        st.write("• Network connectivity problems")
        
        st.info("💡 **Try:**")
        st.write("• Double-check your addresses")
        st.write("• Use more specific street addresses")
        st.write("• Ensure both locations are in NYC")
    
    @staticmethod
    def show_api_error(error_message: str):
        """Show API-related errors"""
        st.error(f"🔧 **API Error:** {error_message}")
        st.write("**Possible solutions:**")
        st.write("• Check your internet connection")
        st.write("• Verify API key configuration")
        st.write("• Try again in a few moments")
        
        with st.expander("🔍 Technical Details"):
            st.code(error_message)

class SearchHistory:
    """Search history component"""
    
    @staticmethod
    def add_to_history(start_address: str, end_address: str):
        """Add search to history"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        
        search_entry = {
            'start': start_address,
            'end': end_address,
            'timestamp': st.session_state.get('last_search_time', 'Unknown')
        }
        
        # Avoid duplicates
        if search_entry not in st.session_state.search_history:
            st.session_state.search_history.insert(0, search_entry)
            # Keep only last 10 searches
            st.session_state.search_history = st.session_state.search_history[:10]
    
    @staticmethod
    def render_search_history():
        """Render search history sidebar"""
        if 'search_history' not in st.session_state or not st.session_state.search_history:
            return
        
        with st.sidebar:
            st.subheader("🕒 Recent Searches")
            
            for i, search in enumerate(st.session_state.search_history):
                with st.expander(f"Search {i+1}", expanded=False):
                    st.write(f"**From:** {DataUtils.format_address_for_display(search['start'], 30)}")
                    st.write(f"**To:** {DataUtils.format_address_for_display(search['end'], 30)}")
                    st.write(f"**Time:** {search['timestamp']}")
                    
                    if st.button(f"Repeat Search {i+1}", key=f"repeat_{i}"):
                        st.session_state['start_address'] = search['start']
                        st.session_state['end_address'] = search['end']
                        st.experimental_rerun()