import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import List, Dict, Optional, Tuple
import googlemaps
from config.settings import Config
from src.utils.helpers import RouteDisplayUtils

class MapDisplay:
    """Interactive map display component using Folium"""
    
    def __init__(self):
        self.client = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
    
    def render_route_map(self, routes_data: Dict, height: int = 600) -> Optional[Dict]:
        """
        Render interactive map with route visualization
        
        Args:
            routes_data: Route data from DirectionsAPI
            height: Map height in pixels
            
        Returns:
            Map interaction data
        """
        if not routes_data or 'routes' not in routes_data:
            return None
        
        routes = routes_data['routes']
        if not routes:
            return None
        
        # Create base map centered on NYC
        map_center = self._calculate_map_center(routes)
        m = folium.Map(
            location=[map_center['lat'], map_center['lng']],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add route layers
        self._add_routes_to_map(m, routes)
        
        # Add start and end markers
        self._add_endpoint_markers(m, routes[0])
        
        # Add map legend
        self._add_map_legend(m, routes)
        
        # Display map in Streamlit
        map_data = st_folium(
            m,
            width=None,
            height=height,
            returned_objects=["last_object_clicked_tooltip"]
        )
        
        return map_data
    
    def _calculate_map_center(self, routes: List[Dict]) -> Dict:
        """Calculate optimal map center based on routes"""
        if not routes:
            return Config.DEFAULT_CENTER
        
        # Use the first route's midpoint
        start_loc = routes[0]['start_location']
        end_loc = routes[0]['end_location']
        
        center_lat = (start_loc['lat'] + end_loc['lat']) / 2
        center_lng = (start_loc['lng'] + end_loc['lng']) / 2
        
        return {'lat': center_lat, 'lng': center_lng}
    
    def _add_routes_to_map(self, map_obj: folium.Map, routes: List[Dict]):
        """Add route polylines to the map"""
        for i, route in enumerate(routes):
            try:
                # Decode polyline
                coordinates = self._decode_polyline(route['polyline'])
                
                if not coordinates:
                    continue
                
                # Get route color and style
                color = RouteDisplayUtils.get_route_color(i)
                weight = 6 if i == 0 else 4  # Best route is thicker
                opacity = 0.8 if i == 0 else 0.6
                
                # Create route popup content
                popup_content = self._create_route_popup(route, i)
                
                # Add polyline to map
                folium.PolyLine(
                    locations=coordinates,
                    color=color,
                    weight=weight,
                    opacity=opacity,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"Route {i+1}: {route['summary']}"
                ).add_to(map_obj)
                
            except Exception as e:
                st.warning(f"Could not display route {i+1}: {str(e)}")
    
    def _decode_polyline(self, polyline_string: str) -> List[Tuple[float, float]]:
        """Decode Google Maps polyline string"""
        try:
            return googlemaps.convert.decode_polyline(polyline_string)
        except Exception:
            return []
    
    def _create_route_popup(self, route: Dict, route_index: int) -> str:
        """Create HTML popup content for route"""
        traffic_status, _ = RouteDisplayUtils.format_traffic_status(
            route['traffic_delay']['delay_percentage']
        )
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="margin: 0; color: #333;">Route {route_index + 1}</h4>
            <hr style="margin: 5px 0;">
            <p style="margin: 2px 0;"><b>Summary:</b> {route['summary']}</p>
            <p style="margin: 2px 0;"><b>Distance:</b> {route['distance']['text']}</p>
            <p style="margin: 2px 0;"><b>Time:</b> {route['duration_in_traffic']['text']}</p>
            <p style="margin: 2px 0;"><b>Traffic:</b> {traffic_status}</p>
            <p style="margin: 2px 0;"><b>Delay:</b> +{route['traffic_delay']['delay_minutes']} min</p>
            <p style="margin: 2px 0;"><b>Score:</b> {route['efficiency_score']}/100</p>
        </div>
        """
        return popup_html
    
    def _add_endpoint_markers(self, map_obj: folium.Map, route: Dict):
        """Add start and end point markers"""
        # Start marker (green)
        folium.Marker(
            location=[route['start_location']['lat'], route['start_location']['lng']],
            popup=folium.Popup(f"<b>Start:</b><br>{route['start_address']}", max_width=200),
            tooltip="Starting Point",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(map_obj)
        
        # End marker (red)
        folium.Marker(
            location=[route['end_location']['lat'], route['end_location']['lng']],
            popup=folium.Popup(f"<b>Destination:</b><br>{route['end_address']}", max_width=200),
            tooltip="Destination",
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(map_obj)
    
    def _add_map_legend(self, map_obj: folium.Map, routes: List[Dict]):
        """Add legend to the map"""
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.2);">
            <h4 style="margin: 0 0 10px 0;">Route Legend</h4>
        """
        
        for i, route in enumerate(routes[:5]):  # Show max 5 routes in legend
            color = RouteDisplayUtils.get_route_color(i)
            legend_html += f"""
            <p style="margin: 5px 0;">
                <span style="color: {color}; font-size: 18px;">●</span>
                Route {i+1}: {route['duration_in_traffic']['text']}
            </p>
            """
        
        legend_html += """
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0; font-size: 12px;">
                <span style="color: green;">🟢</span> Start Point<br>
                <span style="color: red;">🔴</span> End Point
            </p>
        </div>
        """
        
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def render_traffic_overlay_map(self, center_location: Dict, zoom: int = 12) -> Optional[Dict]:
        """
        Render map with traffic overlay for general traffic conditions
        
        Args:
            center_location: Map center coordinates
            zoom: Map zoom level
            
        Returns:
            Map interaction data
        """
        # Create map with traffic layer
        m = folium.Map(
            location=[center_location['lat'], center_location['lng']],
            zoom_start=zoom
        )
        
        # Add traffic layer using Google Maps traffic tiles
        # Note: This requires additional setup for traffic tiles
        traffic_layer = folium.raster_layers.WmsTileLayer(
            url='https://mt1.google.com/vt/lyrs=h@159000000,traffic&x={x}&y={y}&z={z}',
            name='Traffic',
            overlay=True,
            control=True,
            attr='Google Maps Traffic'
        )
        traffic_layer.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Display in Streamlit
        map_data = st_folium(m, width=None, height=400)
        return map_data
    
    def render_simple_location_map(self, locations: List[Dict], zoom: int = 13) -> Optional[Dict]:
        """
        Render simple map with location markers
        
        Args:
            locations: List of location dictionaries with lat, lng, name
            zoom: Map zoom level
            
        Returns:
            Map interaction data
        """
        if not locations:
            return None
        
        # Calculate center
        center_lat = sum(loc['lat'] for loc in locations) / len(locations)
        center_lng = sum(loc['lng'] for loc in locations) / len(locations)
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom
        )
        
        # Add markers for each location
        for i, location in enumerate(locations):
            folium.Marker(
                location=[location['lat'], location['lng']],
                popup=location.get('name', f'Location {i+1}'),
                tooltip=location.get('name', f'Location {i+1}'),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        # Display in Streamlit
        map_data = st_folium(m, width=None, height=400)
        return map_data

class MapControls:
    """Map control components"""
    
    @staticmethod
    def render_map_options():
        """Render map display options"""
        with st.expander("🗺️ Map Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                map_height = st.slider(
                    "Map Height",
                    min_value=400,
                    max_value=800,
                    value=600,
                    step=50,
                    help="Adjust map display height"
                )
                
                show_traffic = st.checkbox(
                    "Show Traffic Layer",
                    value=False,
                    help="Display real-time traffic conditions"
                )
            
            with col2:
                map_style = st.selectbox(
                    "Map Style",
                    ["OpenStreetMap", "Satellite", "Terrain"],
                    help="Choose map background style"
                )
                
                show_markers = st.checkbox(
                    "Show Route Markers",
                    value=True,
                    help="Display start/end point markers"
                )
            
            return {
                'height': map_height,
                'show_traffic': show_traffic,
                'style': map_style,
                'show_markers': show_markers
            }
    
    @staticmethod
    def render_route_selector(routes: List[Dict]) -> Optional[int]:
        """
        Render route selection controls
        
        Args:
            routes: List of route data
            
        Returns:
            Selected route index or None
        """
        if not routes or len(routes) <= 1:
            return None
        
        st.subheader("🎯 Focus on Specific Route")
        
        route_options = []
        for i, route in enumerate(routes):
            option_text = f"Route {i+1}: {route['summary']} ({route['duration_in_traffic']['text']})"
            route_options.append(option_text)
        
        selected_option = st.selectbox(
            "Select route to highlight:",
            ["All Routes"] + route_options,
            help="Choose a specific route to focus on"
        )
        
        if selected_option == "All Routes":
            return None
        else:
            return route_options.index(selected_option)