import re
import streamlit as st
from typing import Optional, Tuple
from config.settings import Config
from src.maps.places_api import PlacesAPI

class AddressValidator:
    """Address validation utilities for NYC locations"""
    
    def __init__(self):
        self.places_api = PlacesAPI()
    
    def validate_address_format(self, address: str) -> Tuple[bool, str]:
        """
        Basic format validation for addresses
        
        Args:
            address: Address string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not address or not address.strip():
            return False, "Address cannot be empty"
        
        address = address.strip()
        
        if len(address) < 5:
            return False, "Address is too short"
        
        if len(address) > 200:
            return False, "Address is too long"
        
        # Check for basic address components
        has_number = bool(re.search(r'\d', address))
        has_letters = bool(re.search(r'[a-zA-Z]', address))
        
        if not (has_number and has_letters):
            return False, "Address should contain both numbers and letters"
        
        return True, ""
    
    def validate_nyc_address(self, address: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Comprehensive NYC address validation
        
        Args:
            address: Address to validate
            
        Returns:
            Tuple of (is_valid, message, geocode_result)
        """
        # First check basic format
        format_valid, format_error = self.validate_address_format(address)
        if not format_valid:
            return False, format_error, None
        
        # Check if address exists and is in NYC
        try:
            geocode_result = self.places_api.geocode_address(address)
            
            if not geocode_result:
                return False, "Address not found or outside NYC area", None
            
            location = geocode_result['geometry']['location']
            
            # Double-check NYC bounds
            if not Config.is_in_nyc_bounds(location['lat'], location['lng']):
                return False, "Address is outside New York City boundaries", None
            
            return True, "Valid NYC address", geocode_result
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None
    
    def suggest_address_corrections(self, address: str) -> list:
        """
        Suggest address corrections using autocomplete
        
        Args:
            address: Partial or incorrect address
            
        Returns:
            List of suggested addresses
        """
        try:
            suggestions = self.places_api.autocomplete(address)
            return [suggestion['description'] for suggestion in suggestions[:5]]
        except Exception:
            return []
    
    def validate_route_endpoints(self, start_address: str, end_address: str) -> Tuple[bool, str]:
        """
        Validate both start and end addresses for route calculation
        
        Args:
            start_address: Starting address
            end_address: Destination address
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate start address
        start_valid, start_message, _ = self.validate_nyc_address(start_address)
        if not start_valid:
            return False, f"Start address error: {start_message}"
        
        # Validate end address
        end_valid, end_message, _ = self.validate_nyc_address(end_address)
        if not end_valid:
            return False, f"End address error: {end_message}"
        
        # Check if addresses are the same
        if start_address.strip().lower() == end_address.strip().lower():
            return False, "Start and end addresses cannot be the same"
        
        return True, "Both addresses are valid"

class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_address(address: str) -> str:
        """
        Sanitize address input
        
        Args:
            address: Raw address input
            
        Returns:
            Sanitized address string
        """
        if not address:
            return ""
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address.strip())
        
        # Remove potentially harmful characters
        address = re.sub(r'[<>"\']', '', address)
        
        # Limit length
        if len(address) > 200:
            address = address[:200]
        
        return address
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """
        General text input sanitization
        
        Args:
            text: Raw text input
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags and potentially harmful characters
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'[<>"\']', '', text)
        
        return text

def display_validation_error(error_message: str):
    """Display validation error in Streamlit UI"""
    st.error(f"❌ {error_message}")

def display_validation_success(success_message: str):
    """Display validation success in Streamlit UI"""
    st.success(f"✅ {success_message}")

def display_validation_warning(warning_message: str):
    """Display validation warning in Streamlit UI"""
    st.warning(f"⚠️ {warning_message}")