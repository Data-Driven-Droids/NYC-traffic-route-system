import snowflake.connector
import pandas as pd
from typing import Optional, Dict
import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime

def get_weather_data_nyc():
    """
    Fetches current, hourly, and daily weather forecast data for New York City
    from the Open-Meteo API.

    Returns:
        dict: A dictionary containing the current conditions, hourly DataFrame,
              and daily DataFrame. Returns None on API failure.
    """
    # Coordinates for New York City (approx. used in the original request)
    latitude = 40.7143
    longitude = -74.006

    # API request parameters
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,uv_index_max",
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        # --- Current Data Structuring ---
        current = data.get('current', {})
        current_data = {
            # Use data from the previous successful JSON response for time/temp/wind
            'time': current.get('time', '2025-10-15T17:45').split('T')[1][:5], # Extracts HH:MM
            'date_time_raw': current.get('time', '2025-10-15T17:45'),
            'temp': f"{current.get('temperature_2m', 'N/A')}{data['current_units'].get('temperature_2m', '')}",
            'humidity': f"{current.get('relative_humidity_2m', 'N/A')}{data['current_units'].get('relative_humidity_2m', '')}",
            'wind': f"{current.get('wind_speed_10m', 'N/A')}{data['current_units'].get('wind_speed_10m', '')}",
            'precipitation': current.get('precipitation', 0),
        }
        
        # Determine simple weather status
        if current_data['precipitation'] > 0:
            current_data['status'] = "Rainy"
        elif float(current.get('wind_speed_10m', 0)) > 25:
            current_data['status'] = "Windy"
        else:
            current_data['status'] = "Clear" # Default status

        # --- Hourly Data Structuring ---
        hourly_raw = data.get('hourly', {})
        hourly_df = pd.DataFrame({
            "Time": [t.split('T')[1].split(':')[0] for t in hourly_raw.get('time', [])],
            "Date": [t.split('T')[0] for t in hourly_raw.get('time', [])],
            "Temperature": hourly_raw.get('temperature_2m', []),
            "Humidity": hourly_raw.get('relative_humidity_2m', []),
            "Precip. Prob.": hourly_raw.get('precipitation_probability', []),
        })
        
        # Filter hourly data to show the next 24 hours starting from the current hour
        try:
            current_hour = datetime.strptime(current_data['date_time_raw'], "%Y-%m-%dT%H:%M").replace(minute=0, second=0)
        except ValueError:
            current_hour = datetime.utcnow().replace(minute=0, second=0) # Fallback to current UTC time

        hourly_df['datetime'] = pd.to_datetime(hourly_df['Date'] + 'T' + hourly_df['Time'] + ':00')
        
        filtered_hourly_df = hourly_df[hourly_df['datetime'] >= current_hour].head(24)
        
        # Final hourly DataFrame for Streamlit Chart
        st_hourly_df = filtered_hourly_df[['Time', 'Temperature', 'Humidity', 'Precip. Prob.']].set_index('Time')


        # --- Daily Data Structuring ---
        daily_raw = data.get('daily', {})
        daily_df = pd.DataFrame({
            "Date": daily_raw.get('time', []),
            "Max Temp": [f"{t}{data['daily_units'].get('temperature_2m_max', '')}" for t in daily_raw.get('temperature_2m_max', [])],
            "Min Temp": [f"{t}{data['daily_units'].get('temperature_2m_min', '')}" for t in daily_raw.get('temperature_2m_min', [])],
            "Max UV Index": daily_raw.get('uv_index_max', []),
        })
        
        # Replace first date with "Today" and format others
        if not daily_df.empty:
            daily_df.loc[0, 'Date'] = 'Today'
            daily_df['Date'] = daily_df['Date'].apply(
                lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%d/%m") if x != 'Today' and isinstance(x, str) else x
            )

        return {
            'current': current_data,
            'hourly_df': st_hourly_df,
            'daily_df': daily_df[['Date', 'Max Temp', 'Min Temp', 'Max UV Index']]
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

# Load environment variables from a .env file (if it exists).
# This makes credentials available via os.environ.get()
load_dotenv() 

def _create_snowflake_connection(
    conn_params: Optional[Dict[str, str]] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    account: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None
) -> Optional[snowflake.connector.SnowflakeConnection]:
    """
    Prepares connection parameters and establishes a connection to Snowflake.
    Prioritizes explicit arguments, then falls back to environment variables.
    """
    
    # 1. Prepare Connection Parameters
    if conn_params is None:
        # Fetch individual parameters, prioritizing arguments over environment variables
        user = user or os.environ.get("SNOWFLAKE_USER")
        password = password or os.environ.get("SNOWFLAKE_PASSWORD")
        account = account or os.environ.get("SNOWFLAKE_ACCOUNT")
        warehouse = warehouse or os.environ.get("SNOWFLAKE_WAREHOUSE")
        database = database or os.environ.get("SNOWFLAKE_DATABASE")
        schema = schema or os.environ.get("SNOWFLAKE_SCHEMA")

        conn_params = {
            'user': user,
            'password': password,
            'account': account,
            'warehouse': warehouse,
            'database': database,
            'schema': schema
        }
        
    # Filter out None values for the connection call (important)
    conn_params = {k: v for k, v in conn_params.items() if v is not None}

    # Critical check for required parameters
    required_params = ['user', 'password', 'account']
    if any(p not in conn_params or conn_params.get(p) is None for p in required_params):
        print("ERROR: Essential connection parameters (user, password, account) are missing. Please ensure environment variables are set (SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT) or provided as arguments.")
        return None

    try:
        # 2. Establish Connection
        conn = snowflake.connector.connect(**conn_params)
        print("Snowflake connection established successfully.")
        return conn
    except Exception as e:
        print(f"Failed to establish Snowflake connection: {e}")
        return None


def fetch_data_from_snowflake(
    query: str,
    conn_params: Optional[Dict[str, str]] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    account: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Establishes a connection, executes a query, fetches the results into a Pandas DataFrame,
    and ensures the connection is closed.

    Args:
        query (str): The SQL query to execute.
        conn_params (Optional[Dict]): A dictionary containing connection parameters.
        user (Optional[str]): Snowflake username (defaults to SNOWFLAKE_USER env var).
        password (Optional[str]): Snowflake password (defaults to SNOWFLAKE_PASSWORD env var).
        account (Optional[str]): Snowflake account identifier (defaults to SNOWFLAKE_ACCOUNT env var).
        warehouse (Optional[str]): Snowflake warehouse to use (defaults to SNOWFLAKE_WAREHOUSE env var).
        database (Optional[str]): Snowflake database to use (defaults to SNOWFLAKE_DATABASE env var).
        schema (Optional[str]): Snowflake schema to use (defaults to SNOWFLAKE_SCHEMA env var).

    Returns:
        Optional[pd.DataFrame]: A Pandas DataFrame containing the query results, 
                                or None if an error occurred.
    """
    conn = None
    
    # 1. & 2. Create Connection using the helper function
    conn = _create_snowflake_connection(
        conn_params=conn_params,
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema
    )
    
    if conn is None:
        return None

    try:
        # 3. Execute Query and Fetch Data into DataFrame
        print(f"Executing query: {query[:50]}...")
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch results directly into a Pandas DataFrame
        df = cursor.fetch_pandas_all()
        
        cursor.close()
        print("Query executed successfully and data fetched.")
        return df

    except snowflake.connector.errors.ProgrammingError as e:
        print(f"Snowflake Programming Error: {e.errno}: {e.msg}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during query execution: {e}")
        return None

    finally:
        # 4. Ensure Connection Closure
        if conn:
            conn.close()
            print("Snowflake connection closed.")
