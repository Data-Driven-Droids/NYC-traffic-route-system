import os
import sys
import pandas as pd
from dotenv import load_dotenv

# --- Import the necessary functions and constants from your utils file ---
# This assumes your utils.py file contains get_city_guard_data_by_view
# and the CITY_GUARD_VIEWS dictionary.
try:
    from utils import get_city_guard_data_by_view, CITY_GUARD_VIEWS
except ImportError:
    print("🚨 ERROR: Could not find 'utils.py'.")
    print("Please ensure 'utils.py' is in the same directory and contains 'get_city_guard_data_by_view' and 'CITY_GUARD_VIEWS'.")
    sys.exit(1)


def main():
    """
    Tests the get_city_guard_data_by_view function for each known view.
    """
    
    # Check if essential environment variables are set before starting
    required_vars = ["SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT"]
    if not all(os.environ.get(v) for v in required_vars):
        print("🚨 ERROR: Essential Snowflake environment variables are not set.")
        print(f"Please create a '.env' file or set the following environment variables: {', '.join(required_vars)}")
        sys.exit(1)

    print("--- Starting City Guard Data Retrieval Test ---")
    
    # Get the list of view keys to test from the imported dictionary
    view_keys_to_test = list(CITY_GUARD_VIEWS.keys())
    
    all_tests_passed = True
    
    for view_key in view_keys_to_test:
        
        # Call the specific function for City Guard views
        df = get_city_guard_data_by_view(view_key=view_key)
        
        if df is not None and not df.empty:
            print(f"\n✅ SUCCESS: Retrieved data for '{view_key}'.")
            print(f"   - Data shape: {df.shape}")
            print(f"   - Columns: {df.columns.tolist()}")
            print(f"   - First 3 rows:\n{df.head(3)}\n")
        elif df is not None and df.empty:
            print(f"\n⚠️  WARNING: Query for '{view_key}' was successful but returned no data.")
        else:
            print(f"\n❌ FAILURE: Could not retrieve data for '{view_key}'. Check error logs above.\n")
            all_tests_passed = False

    print("--- Test Complete ---")
    if all_tests_passed:
        print("🎉 All views returned data successfully!")
    else:
        print("🔥 Some views failed to return data.")


if __name__ == "__main__":
    # Load environment variables from a .env file in the same directory
    load_dotenv() 
    main()