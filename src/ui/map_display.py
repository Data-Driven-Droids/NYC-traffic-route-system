import streamlit as st
import folium
from streamlit_folium import st_folium
import googlemaps
from typing import Dict, List, Tuple
from config.settings import Config

class MapDisplay:
    """Interactive map display component using Folium"""

    def __init__(self):
        self.client = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)

    # ======================== TRAFFIC MAP ========================
    def render_traffic_overlay_map(self, center_location: Dict) -> None:
        """Render traffic map with simplified parameters"""
        try:
            # Ensure coordinates are float values with safe defaults
            lat = float(center_location.get('lat', 40.7128))
            lng = float(center_location.get('lng', -74.0060))
            
            # Create base map with minimal parameters
            m = folium.Map(
                location=[lat, lng],
                zoom_start=12,
                tiles='OpenStreetMap'  # Use default tile layer
            )

            # Add traffic layer directly without dict
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}',
                attr='Google Traffic',
                name='Traffic',
                overlay=True
            ).add_to(m)

            # Render map with minimal parameters
            st_folium(
                m,
                width=800,
                height=400,
                key="traffic_map_static"
            )

        except Exception as e:
            st.error(f"Traffic map error: {str(e)}")

    # ======================== ROUTE MAP ========================
    def render_route_map(self, routes_data: Dict) -> None:
        """Render route map with simplified parameters"""
        try:
            routes = routes_data.get('routes', [])
            if not routes:
                return

            # Extract and validate center coordinates
            first_route = routes[0]
            start_loc = first_route.get('start_location', {})
            end_loc = first_route.get('end_location', {})
            
            center_lat = (float(start_loc.get('lat', 40.7128)) + float(end_loc.get('lat', 40.7128))) / 2
            center_lng = (float(start_loc.get('lng', -74.0060)) + float(end_loc.get('lng', -74.0060))) / 2
            
            # Create base map with validated coordinates
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=12,
                tiles='OpenStreetMap'
            )

            # Add routes with basic styling
            for i, route in enumerate(routes[:5]):
                coords = self._safe_decode_polyline(route.get('polyline', ''))
                if coords:
                    # Ensure coordinates are float values
                    try:
                        coords = [[float(lat), float(lng)] for lat, lng in coords]
                        folium.PolyLine(
                            locations=coords,
                            color='blue' if i == 0 else 'gray',
                            weight=6 if i == 0 else 4,
                            opacity=0.8 if i == 0 else 0.6,
                            tooltip=f"Route {i+1}"
                        ).add_to(m)
                    except (ValueError, TypeError):
                        continue

            # Add markers with validated coordinates
            if routes:
                start = routes[0].get('start_location', {})
                end = routes[0].get('end_location', {})
                
                try:
                    folium.Marker(
                        [float(start.get('lat', 40.7128)), float(start.get('lng', -74.0060))],
                        popup='Start',
                        icon=folium.Icon(color='green')
                    ).add_to(m)
                    
                    folium.Marker(
                        [float(end.get('lat', 40.7128)), float(end.get('lng', -74.0060))],
                        popup='End',
                        icon=folium.Icon(color='red')
                    ).add_to(m)
                except (ValueError, TypeError):
                    st.warning("Could not add route markers due to invalid coordinates")

            # Render map with minimal parameters
            st_folium(
                m,
                width=800,
                height=600,
                key="route_map_static"
            )

        except Exception as e:
            st.error(f"Route map error: {str(e)}")

    def _calculate_map_center(self, route: Dict) -> Dict:
        """Calculate map center from route endpoints"""
        start = route.get('start_location', {'lat': 40.7128, 'lng': -74.0060})
        end = route.get('end_location', {'lat': 40.7128, 'lng': -74.0060})
        return {
            'lat': (start['lat'] + end['lat']) / 2,
            'lng': (start['lng'] + end['lng']) / 2
        }

    def _safe_decode_polyline(self, polyline: str) -> List[Tuple[float, float]]:
        """Safely decode polyline to coordinates"""
        try:
            return googlemaps.convert.decode_polyline(polyline)
        except:
            return []

    def _add_markers(self, m: folium.Map, route: Dict) -> None:
        """Add start/end markers to map"""
        start = route.get('start_location', {})
        end = route.get('end_location', {})
        
        # Start marker
        folium.Marker(
            [start.get('lat', 40.7128), start.get('lng', -74.0060)],
            popup='Start',
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
        
        # End marker
        folium.Marker(
            [end.get('lat', 40.7128), end.get('lng', -74.0060)],
            popup='End',
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
