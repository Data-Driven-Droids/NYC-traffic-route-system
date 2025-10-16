import os
import sys
import pandas as pd
from dotenv import load_dotenv
from utils import get_binsync_data_by_view , calculate_monthly_waste_metrics

# NOTE: This line assumes your functions (get_binsync_data_by_view, 
# fetch_data_from_snowflake, _create_snowflake_connection, and BINSYNC_VIEWS) 
# are defined and available, typically by importing them from a module.
# Since the full context isn't available, we'll redefine the necessary views 
# and mock the function for a runnable file, or you can uncomment the import 
# if you put the functions in 'snowflake_utils.py'.

# from snowflake_utils import get_binsync_data_by_view, BINSYNC_VIEWS 

# --- Minimal definitions for a standalone test if you haven't split the files ---
# If you kept the functions in the file you run, remove the 'import' line above 
# and ensure the functions/dictionary are defined before this block.

# Redefine the views and the function here for a *single runnable file*
BINSYNC_VIEWS: dict[str, str] = {
    "WASTE_TONNAGE": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_MONTHLY_WASTE_TONNAGE_BY_BOROUGH",
    "NON_OPERATIONAL_BINS": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_UNIQUE_NON_OPERATIONAL_BINS",
    "RECYCLING_DIVERSION_RATE": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_MONTHLY_RECYCLING_DIVERSION_RATE"
}

# Add the function definitions from the previous answer here for a runnable file:
# def _create_snowflake_connection(...): ...
# def fetch_data_from_snowflake(...): ...
# def get_binsync_data_by_view(...): ...
# (You must copy these in if you want the file to run without a utility module)
# -----------------------------------------------------------------------------


def main():
    
    return calculate_monthly_waste_metrics()
    """
    Tests the get_binsync_data_by_view function for each known view.
    """
    
    # Check if essential env vars are set before starting
    required_vars = ["SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT"]
    if not all(os.environ.get(v) for v in required_vars):
        print("🚨 ERROR: Essential Snowflake environment variables are not set.")
        print(f"Please set: {', '.join(required_vars)}")
        sys.exit(1)

    print("--- Starting BinSync Data Retrieval Test ---")
    
    # List of view keys to test
    view_keys_to_test = list(BINSYNC_VIEWS.keys())
    
    for view_key in view_keys_to_test:
        print(f"\n=======================================================")
        print(f"  Attempting to fetch data for view: {view_key}")
        print(f"=======================================================")
        
        # Call the function
        # Ensure the function definition for get_binsync_data_by_view is available!
        df = get_binsync_data_by_view(view_key=view_key)
        
        if df is not None:
            print(f"\n✅ SUCCESS: Retrieved data for '{view_key}'.")
            print(f"Data shape: {df.shape}")
            print(f"First 5 rows:\n{df.head()}\n")
        else:
            print(f"\n❌ FAILURE: Could not retrieve data for '{view_key}'. Check error logs above.\n")


if __name__ == "__main__":
    # Ensure you have installed the necessary libraries:
    # pip install snowflake-connector-python pandas
    load_dotenv() 
    main()