#!/usr/bin/env python3
"""
Debug script to test 511NY Traffic API
"""

import requests
import json

API_KEY = "fd7bd4600ee94588be5a28d448666112"
BASE_URL = "https://511ny.org/api/getevents"

def test_api_call(event_type):
    """Test API call with specific event type"""
    print(f"\n{'='*60}")
    print(f"Testing API with event_type: '{event_type}'")
    print(f"{'='*60}")
    
    params = {
        "apiKey": API_KEY,
        "format": "json",
        "type": event_type
    }
    
    try:
        print(f"Making request to: {BASE_URL}")
        print(f"Parameters: {params}")
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API call successful!")
            print(f"Response type: {type(data).__name__}")
            
            # Check if data is a list or dict
            if isinstance(data, list):
                events = data
                print(f"\n📊 Found {len(events)} events (direct list)")
                
                if len(events) > 0:
                    print(f"\n📋 Sample event (first one):")
                    print(json.dumps(events[0], indent=2))
                    
                    # Show all available keys in the event
                    print(f"\n🔑 Available keys in event:")
                    for key in events[0].keys():
                        value = events[0][key]
                        print(f"   - {key}: {type(value).__name__} = {str(value)[:50]}")
                else:
                    print("⚠️ No events in response")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
                if "events" in data:
                    events = data["events"]
                    print(f"\n📊 Found {len(events)} events")
                    
                    if len(events) > 0:
                        print(f"\n📋 Sample event (first one):")
                        print(json.dumps(events[0], indent=2))
                else:
                    print("⚠️ No 'events' key in response")
                    print(f"Full response: {json.dumps(data, indent=2)}")
            else:
                print(f"⚠️ Unexpected response type: {type(data)}")
                print(f"Response: {data}")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚦 Testing 511NY Traffic API")
    print("="*60)
    
    # Test different event types
    event_types = ["event", "congestion", "construction", "incident"]
    
    for event_type in event_types:
        test_api_call(event_type)
    
    print("\n" + "="*60)
    print("Testing complete!")

if __name__ == "__main__":
    main()
