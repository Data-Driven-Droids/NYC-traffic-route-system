#!/usr/bin/env python3
"""
Test script for NYC Route Optimizer API connections
Run this script to verify your Google Maps API setup
"""

import os
import sys
from datetime import datetime

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from src.maps.places_api import PlacesAPI
from src.maps.directions import DirectionsAPI
from src.utils.validation import AddressValidator

def test_configuration():
    """Test configuration setup"""
    print("🔧 Testing Configuration...")
    try:
        Config.validate()
        print("✅ Configuration is valid")
        print(f"   API Key: {'*' * 20}{Config.GOOGLE_MAPS_API_KEY[-4:]}")
        print(f"   NYC Bounds: {Config.NYC_BOUNDS}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_places_api():
    """Test Google Places API"""
    print("\n📍 Testing Places API...")
    try:
        places_api = PlacesAPI()
        
        # Test autocomplete
        results = places_api.autocomplete("Times Square")
        if results:
            print(f"✅ Places API working - Found {len(results)} suggestions for 'Times Square'")
            for i, result in enumerate(results[:3]):
                print(f"   {i+1}. {result['description']}")
        else:
            print("⚠️ Places API returned no results")
        
        # Test geocoding
        geocode_result = places_api.geocode_address("Times Square, New York, NY")
        if geocode_result:
            location = geocode_result['geometry']['location']
            print(f"✅ Geocoding working - Times Square: {location['lat']:.4f}, {location['lng']:.4f}")
        else:
            print("❌ Geocoding failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Places API error: {e}")
        return False

def test_directions_api():
    """Test Google Directions API"""
    print("\n🗺️ Testing Directions API...")
    try:
        directions_api = DirectionsAPI()
        
        # Test route calculation
        start = "Times Square, New York, NY"
        end = "Central Park, New York, NY"
        
        print(f"   Calculating route from {start} to {end}...")
        routes_data = directions_api.get_routes(start, end)
        
        if routes_data and 'routes' in routes_data:
            routes = routes_data['routes']
            print(f"✅ Directions API working - Found {len(routes)} route(s)")
            
            best_route = routes_data['best_route']
            print(f"   Best route: {best_route['summary']}")
            print(f"   Distance: {best_route['distance']['text']}")
            print(f"   Time: {best_route['duration_in_traffic']['text']}")
            print(f"   Traffic delay: +{best_route['traffic_delay']['delay_minutes']} min")
            print(f"   Efficiency score: {best_route['efficiency_score']}/100")
        else:
            print("❌ Directions API returned no routes")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Directions API error: {e}")
        return False

def test_address_validation():
    """Test address validation"""
    print("\n✅ Testing Address Validation...")
    try:
        validator = AddressValidator()
        
        # Test valid NYC address
        valid_address = "350 5th Ave, New York, NY 10118"  # Empire State Building
        is_valid, message, geocode_result = validator.validate_nyc_address(valid_address)
        
        if is_valid:
            print(f"✅ Address validation working - '{valid_address}' is valid")
            print(f"   Message: {message}")
        else:
            print(f"❌ Valid address rejected: {message}")
        
        # Test invalid address
        invalid_address = "123 Fake Street, Los Angeles, CA"
        is_valid, message, _ = validator.validate_nyc_address(invalid_address)
        
        if not is_valid:
            print(f"✅ Invalid address correctly rejected: '{invalid_address}'")
            print(f"   Message: {message}")
        else:
            print(f"⚠️ Invalid address was accepted")
        
        return True
        
    except Exception as e:
        print(f"❌ Address validation error: {e}")
        return False

def test_nyc_bounds():
    """Test NYC boundary checking"""
    print("\n🗽 Testing NYC Bounds...")
    
    # Test coordinates within NYC
    nyc_coords = [
        (40.7589, -73.9851, "Times Square"),
        (40.6892, -74.0445, "Statue of Liberty"),
        (40.7505, -73.9934, "Empire State Building"),
        (40.7829, -73.9654, "Central Park")
    ]
    
    for lat, lng, name in nyc_coords:
        is_in_nyc = Config.is_in_nyc_bounds(lat, lng)
        status = "✅" if is_in_nyc else "❌"
        print(f"   {status} {name}: ({lat}, {lng}) - {'In NYC' if is_in_nyc else 'Outside NYC'}")
    
    # Test coordinates outside NYC
    outside_coords = [
        (34.0522, -118.2437, "Los Angeles"),
        (41.8781, -87.6298, "Chicago")
    ]
    
    for lat, lng, name in outside_coords:
        is_in_nyc = Config.is_in_nyc_bounds(lat, lng)
        status = "✅" if not is_in_nyc else "❌"
        print(f"   {status} {name}: ({lat}, {lng}) - {'Outside NYC' if not is_in_nyc else 'Incorrectly in NYC'}")

def run_all_tests():
    """Run all tests"""
    print("🧪 NYC Route Optimizer - API Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Configuration", test_configuration),
        ("Places API", test_places_api),
        ("Directions API", test_directions_api),
        ("Address Validation", test_address_validation),
        ("NYC Bounds", test_nyc_bounds)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your API setup is working correctly.")
        print("You can now run the main application with: streamlit run app.py")
    else:
        print("\n⚠️ Some tests failed. Please check your API configuration.")
        print("Refer to the implementation guide for setup instructions.")
    
    return passed == len(results)

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and add your Google Maps API key.")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)