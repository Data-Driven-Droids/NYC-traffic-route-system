# NYC Route Optimizer - Implementation Guide

## Phase 1: Google Cloud Platform Setup

### Step 1: Create Google Cloud Account
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account or create a new one
3. Accept the terms of service
4. Set up billing (required for Maps APIs)
   - Add a payment method
   - Consider setting up billing alerts

### Step 2: Create a New Project
1. Click "Select a project" → "New Project"
2. Project name: `nyc-route-optimizer`
3. Note the Project ID (will be auto-generated)
4. Click "Create"

### Step 3: Enable Required APIs
Navigate to "APIs & Services" → "Library" and enable:

1. **Maps JavaScript API**
   - Search for "Maps JavaScript API"
   - Click "Enable"

2. **Places API (New)**
   - Search for "Places API (New)"
   - Click "Enable"

3. **Directions API**
   - Search for "Directions API"
   - Click "Enable"

4. **Geocoding API**
   - Search for "Geocoding API"
   - Click "Enable"

### Step 4: Create API Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the generated API key
4. Click "Restrict Key" for security:
   - **Application restrictions**: HTTP referrers (web sites)
   - Add your domain (e.g., `localhost:8501/*` for development)
   - **API restrictions**: Select the 4 APIs enabled above
5. Save the restrictions

### Step 5: Set Up Billing Alerts (Recommended)
1. Go to "Billing" → "Budgets & alerts"
2. Create a budget (e.g., $50/month)
3. Set up email alerts at 50%, 90%, and 100%

## Phase 2: Development Environment Setup

### Step 1: Create Project Directory
```bash
mkdir nyc_route_optimizer
cd nyc_route_optimizer
```

### Step 2: Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
Create `requirements.txt`:
```txt
streamlit==1.28.1
googlemaps==4.10.0
folium==0.14.0
streamlit-folium==0.15.0
pandas==2.1.1
numpy==1.24.3
python-dotenv==1.0.0
requests==2.31.0
geopy==2.4.0
```

Install packages:
```bash
pip install -r requirements.txt
```

### Step 4: Create Project Structure
```bash
mkdir -p config src/maps src/ui src/utils
touch config/__init__.py config/settings.py config/api_keys.py
touch src/__init__.py src/maps/__init__.py src/ui/__init__.py src/utils/__init__.py
touch src/maps/places_api.py src/maps/directions.py src/maps/traffic.py
touch src/ui/components.py src/ui/map_display.py
touch src/utils/validation.py src/utils/helpers.py
touch app.py .env .gitignore README.md
```

### Step 5: Configure Environment Variables
Create `.env` file:
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
NYC_BOUNDS_NORTH=40.9176
NYC_BOUNDS_SOUTH=40.4774
NYC_BOUNDS_EAST=-73.7004
NYC_BOUNDS_WEST=-74.2591
DEFAULT_CENTER_LAT=40.7589
DEFAULT_CENTER_LNG=-73.9851
CACHE_DURATION=300
MAX_ROUTES=5
```

Create `.gitignore`:
```gitignore
# Environment variables
.env
config/api_keys.py

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Streamlit
.streamlit/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## Phase 3: Core Implementation

### Step 1: Configuration Management
`config/settings.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # NYC Boundaries
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
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 300))
    MAX_ROUTES = int(os.getenv('MAX_ROUTES', 5))
    
    @classmethod
    def validate(cls):
        if not cls.GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY is required")
        return True
```

### Step 2: Google Maps Integration
`src/maps/places_api.py`:
```python
import googlemaps
from config.settings import Config

class PlacesAPI:
    def __init__(self):
        self.client = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
    
    def autocomplete(self, input_text, location_bias=None):
        """Get place autocomplete suggestions"""
        try:
            if location_bias is None:
                location_bias = Config.DEFAULT_CENTER
            
            results = self.client.places_autocomplete(
                input_text=input_text,
                location=(location_bias['lat'], location_bias['lng']),
                radius=50000,  # 50km radius
                components={'country': 'us'}
            )
            return results
        except Exception as e:
            print(f"Places API error: {e}")
            return []
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        try:
            result = self.client.place(
                place_id=place_id,
                fields=['geometry', 'formatted_address', 'name']
            )
            return result
        except Exception as e:
            print(f"Place details error: {e}")
            return None
```

### Step 3: Basic Streamlit App
`app.py`:
```python
import streamlit as st
from config.settings import Config
from src.ui.components import AddressInput, RouteDisplay
from src.maps.directions import DirectionsAPI

def main():
    st.set_page_config(
        page_title="NYC Route Optimizer",
        page_icon="🗽",
        layout="wide"
    )
    
    st.title("🗽 NYC Traffic-Aware Route Optimizer")
    st.markdown("Find the best routes in New York City with real-time traffic analysis")
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        st.error(f"Configuration error: {e}")
        st.stop()
    
    # Initialize session state
    if 'routes' not in st.session_state:
        st.session_state.routes = None
    
    # Create two columns for input
    col1, col2 = st.columns(2)
    
    with col1:
        start_address = st.text_input(
            "Start Address",
            placeholder="Enter starting location in NYC..."
        )
    
    with col2:
        end_address = st.text_input(
            "End Address", 
            placeholder="Enter destination in NYC..."
        )
    
    # Route calculation button
    if st.button("Find Best Routes", type="primary"):
        if start_address and end_address:
            with st.spinner("Calculating routes with traffic data..."):
                directions_api = DirectionsAPI()
                routes = directions_api.get_routes(start_address, end_address)
                st.session_state.routes = routes
        else:
            st.warning("Please enter both start and end addresses")
    
    # Display routes if available
    if st.session_state.routes:
        st.subheader("Route Recommendations")
        # Route display will be implemented in Phase 4
        st.json(st.session_state.routes)  # Temporary display

if __name__ == "__main__":
    main()
```

## Phase 4: Testing and Validation

### Step 1: Test API Connection
Create `test_api.py`:
```python
from config.settings import Config
from src.maps.places_api import PlacesAPI

def test_api_connection():
    try:
        Config.validate()
        places_api = PlacesAPI()
        
        # Test autocomplete
        results = places_api.autocomplete("Times Square")
        print(f"API test successful. Found {len(results)} suggestions.")
        return True
    except Exception as e:
        print(f"API test failed: {e}")
        return False

if __name__ == "__main__":
    test_api_connection()
```

### Step 2: Run the Application
```bash
streamlit run app.py
```

## Phase 5: Advanced Features Implementation

### Upcoming Features:
1. **Interactive Map Display**: Folium integration for route visualization
2. **Route Comparison**: Side-by-side analysis of multiple routes
3. **Real-time Traffic**: Live traffic data integration
4. **Address Validation**: NYC boundary checking
5. **Error Handling**: Comprehensive error management
6. **Performance Optimization**: Caching and rate limiting

## Troubleshooting

### Common Issues:

1. **API Key Errors**
   - Verify API key is correct in `.env`
   - Check API restrictions in Google Cloud Console
   - Ensure billing is enabled

2. **Import Errors**
   - Verify virtual environment is activated
   - Check all dependencies are installed
   - Ensure Python path includes project directory

3. **Streamlit Issues**
   - Clear Streamlit cache: `streamlit cache clear`
   - Check port availability (default: 8501)
   - Verify firewall settings

### Getting Help:
- Google Maps API Documentation: https://developers.google.com/maps/documentation
- Streamlit Documentation: https://docs.streamlit.io
- Project Issues: Create GitHub issues for bugs or feature requests

## Next Steps

After completing this implementation guide:
1. Test the basic functionality
2. Implement advanced features from the todo list
3. Add comprehensive error handling
4. Optimize performance and user experience
5. Deploy to production environment

This guide provides a solid foundation for building your NYC traffic-aware route optimization system.