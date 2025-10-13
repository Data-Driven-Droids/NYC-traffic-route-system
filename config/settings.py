import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for NYC Route Optimizer"""
    
    # Google Maps API Key
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # NYC Boundaries (approximate)
    NYC_BOUNDS = {
        'north': float(os.getenv('NYC_BOUNDS_NORTH', 40.9176)),
        'south': float(os.getenv('NYC_BOUNDS_SOUTH', 40.4774)),
        'east': float(os.getenv('NYC_BOUNDS_EAST', -73.7004)),
        'west': float(os.getenv('NYC_BOUNDS_WEST', -74.2591))
    }
    
    # Default map center (Times Square)
    DEFAULT_CENTER = {
        'lat': float(os.getenv('DEFAULT_CENTER_LAT', 40.7589)),
        'lng': float(os.getenv('DEFAULT_CENTER_LNG', -73.9851))
    }
    
    # Application settings
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 300))  # 5 minutes
    MAX_ROUTES = int(os.getenv('MAX_ROUTES', 5))
    
    # Traffic model settings
    TRAFFIC_MODEL = 'best_guess'  # Options: best_guess, pessimistic, optimistic
    DEPARTURE_TIME = 'now'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY is required. Please set it in your .env file")
        return True
    
    @classmethod
    def is_in_nyc_bounds(cls, lat, lng):
        """Check if coordinates are within NYC boundaries"""
        return (cls.NYC_BOUNDS['south'] <= lat <= cls.NYC_BOUNDS['north'] and
                cls.NYC_BOUNDS['west'] <= lng <= cls.NYC_BOUNDS['east'])
    
    @classmethod
    def get_nyc_bounds_string(cls):
        """Get NYC bounds as a formatted string for API calls"""
        return f"{cls.NYC_BOUNDS['south']},{cls.NYC_BOUNDS['west']}|{cls.NYC_BOUNDS['north']},{cls.NYC_BOUNDS['east']}"