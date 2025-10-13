import googlemaps
import streamlit as st
from typing import List, Dict, Optional
from config.settings import Config

class PlacesAPI:
    """Google Places API integration for address autocomplete and validation"""
    
    def __init__(self):
        """Initialize the Places API client"""
        self.client = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
    
    @st.cache_data(ttl=Config.CACHE_DURATION)
    def autocomplete(_self, input_text: str, location_bias: Optional[Dict] = None) -> List[Dict]:
        """
        Get place autocomplete suggestions for NYC
        
        Args:
            input_text: The text to search for
            location_bias: Optional location to bias results towards
            
        Returns:
            List of autocomplete suggestions
        """
        try:
            if not input_text or len(input_text) < 2:
                return []
            
            if location_bias is None:
                location_bias = Config.DEFAULT_CENTER
            
            # Restrict to NYC area with components filter
            results = _self.client.places_autocomplete(
                input_text=input_text,
                location=(location_bias['lat'], location_bias['lng']),
                radius=50000,  # 50km radius from center
                components={'country': 'us', 'administrative_area': 'NY'},
                types=['address', 'establishment', 'geocode']
            )
            
            # Filter results to NYC bounds
            filtered_results = []
            for result in results:
                place_details = _self.get_place_details(result['place_id'])
                if place_details:
                    location = place_details['result']['geometry']['location']
                    if Config.is_in_nyc_bounds(location['lat'], location['lng']):
                        filtered_results.append(result)
            
            return filtered_results[:10]  # Limit to 10 suggestions
            
        except Exception as e:
            st.error(f"Places API error: {str(e)}")
            return []
    
    @st.cache_data(ttl=Config.CACHE_DURATION)
    def get_place_details(_self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a place
        
        Args:
            place_id: Google Places place ID
            
        Returns:
            Place details or None if error
        """
        try:
            result = _self.client.place(
                place_id=place_id,
                fields=['geometry', 'formatted_address', 'name', 'types']
            )
            return result
        except Exception as e:
            st.error(f"Place details error: {str(e)}")
            return None
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """
        Geocode an address to get coordinates
        
        Args:
            address: Address string to geocode
            
        Returns:
            Geocoding result or None if error
        """
        try:
            results = self.client.geocode(
                address=address,
                components={'country': 'US', 'administrative_area': 'NY'}
            )
            
            if results:
                location = results[0]['geometry']['location']
                # Verify it's within NYC bounds
                if Config.is_in_nyc_bounds(location['lat'], location['lng']):
                    return results[0]
                else:
                    st.warning("Address is outside NYC boundaries")
                    return None
            return None
            
        except Exception as e:
            st.error(f"Geocoding error: {str(e)}")
            return None
    
    def validate_nyc_address(self, address: str) -> bool:
        """
        Validate that an address is within NYC boundaries
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid NYC address, False otherwise
        """
        geocode_result = self.geocode_address(address)
        return geocode_result is not None