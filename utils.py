import snowflake.connector
import pandas as pd
from typing import Optional, Dict
import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime
from config.settings import Config
import json as json

load_dotenv() 

# Updated function to accept latitude and longitude
def get_air_quality_data_nyc(latitude: float = 40.7128, longitude: float = -74.0060):
    """
    Fetches current air quality data for a given location using the Google Cloud Air Quality API.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict: A dictionary containing the current AQI, category, dominant pollutant, 
              and concentrations for PM2.5 and PM10, or None on error.
    """
    try:
        # NOTE: Ensure you are using the correct API Key here, 
        # it should probably be Config.GOOGLE_AIR_QUALITY_API_KEY
        api_key = Config.GOOGLE_MAPS_API_KEY 
    except (NameError, AttributeError) as e:
        print(f"Error accessing API Key: {e}")
        return None

    url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
    
    # Payload for the API request uses the provided coordinates
    payload = {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        # Ensure all necessary computations are requested
        "extraComputations": ["POLLUTANT_CONCENTRATION"], 
        "languageCode": "en"
    }
    
    # Request headers
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Make the POST request to the Google Air Quality API
        response = requests.post(url, headers=headers, params={'key': api_key}, data=json.dumps(payload))
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        # --- Parse the relevant data ---
        aqi_data = {}
        
        # 1. Extract AQI value, Category, and DOMINANT POLLUTANT from 'indexes'
        if 'indexes' in data and data['indexes']:
            # The API might return multiple indexes, usually the first one is the main 'Overall' index.
            current_aqi_data = data['indexes'][0] 
            
            aqi_data['aqi'] = current_aqi_data.get('aqi')
            aqi_data['category'] = current_aqi_data.get('category')
            # CORRECT EXTRACTION: The dominant pollutant is directly in the index data
            aqi_data['pollutant'] = current_aqi_data.get('dominantPollutant', 'N/A')
        
        # 2. Extract PM2.5 and PM10 from 'pollutants'
        aqi_data['pm25'] = 'N/A'
        aqi_data['pm10'] = 'N/A'
        
        if 'pollutants' in data and data['pollutants']:
             for pollutant in data['pollutants']:
                 code = pollutant.get('code')
                 # Safely extract concentration value
                 concentration = pollutant.get('concentration', {}).get('value')
                 units = pollutant.get('concentration', {}).get('units')
                 
                 formatted_value = f"{concentration} {units}" if concentration is not None else 'N/A'

                 if code == 'pm25':
                     aqi_data['pm25'] = formatted_value
                 elif code == 'pm10':
                     aqi_data['pm10'] = formatted_value

        # Return the comprehensive dictionary
        if aqi_data.get('aqi') is not None:
             return aqi_data
        else:
             print("Data found but could not extract main AQI index.")
             return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching air quality data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    
def get_weather_data_nyc(latitude: float = 40.7143, longitude: float = -74.006):
    """
    Fetches current, hourly, and daily weather forecast data for a given location
    from the Open-Meteo API.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict: A dictionary containing the current conditions, hourly DataFrame,
              and daily DataFrame. Returns None on API failure.
    """

    # API request parameters use the provided coordinates
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude, 
        "longitude": longitude, 
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,uv_index_max",
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "forecast_days": 7
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        # --- Current Data Structuring ---
        current = data.get('current', {})
        
        # Simple weather status based on precipitation or wind
        status = "Clear"
        
        raw_precipitation = current.get('precipitation', 0)
        raw_wind_value = current.get('wind_speed_10m', 0)
        
        try:
            wind_value = float(raw_wind_value)
        except (ValueError, TypeError):
            wind_value = 0.0 # Default to 0 if wind value is unparseable

        if raw_precipitation > 0.5: # 0.5mm threshold for "Rainy"
             status = "Rainy"
        elif wind_value > 25:
             status = "Windy"
        
        current_data = {
            'time': current.get('time', '2025-10-15T17:45').split('T')[1][:5], 
            'date_time_raw': current.get('time', '2025-10-15T17:45'),
            'temp': f"{current.get('temperature_2m', 'N/A')}",
            'humidity': f"{current.get('relative_humidity_2m', 'N/A')}",
            'wind': f"{current.get('wind_speed_10m', 'N/A')} {data['current_units'].get('wind_speed_10m', '')}",
            'status': status
        }
        
        # --- Hourly Data Structuring (FIXED) ---
        hourly_raw = data.get('hourly', {})
        hourly_df_raw = pd.DataFrame({
            "Time": [t.split('T')[1].split(':')[0] for t in hourly_raw.get('time', [])],
            "Date": [t.split('T')[0] for t in hourly_raw.get('time', [])],
            "Temperature": hourly_raw.get('temperature_2m', []),
            "Humidity": hourly_raw.get('relative_humidity_2m', []),
            "Precip. Prob.": hourly_raw.get('precipitation_probability', []),
        })
        
        # Filter for current hour and next 24 hours
        try:
            # Use the full time string from the hourly data for filtering precision
            hourly_df_raw['datetime'] = pd.to_datetime(hourly_df_raw['Date'] + 'T' + hourly_df_raw['Time'] + ':00')
            current_time = datetime.strptime(current_data['date_time_raw'], "%Y-%m-%dT%H:%M")
            
            # Find the index of the first hour that is equal to or after the current time
            start_index = hourly_df_raw[hourly_df_raw['datetime'] >= current_time].index.min()
            
            if pd.isna(start_index):
                start_index = 0

            # Filter for 24 hours starting from the current hour/next hour
            filtered_hourly_df = hourly_df_raw.iloc[start_index:start_index + 24].copy()
            
            # Rename the 'Time' column to HH:00 format for cleaner chart labels
            filtered_hourly_df['Time'] = filtered_hourly_df['datetime'].dt.strftime('%H:00')
            
            # --- CRITICAL FIX: DO NOT SET INDEX HERE ---
            final_hourly_df = filtered_hourly_df[['Time', 'Temperature', 'Humidity', 'Precip. Prob.']]

        except Exception as e:
            print(f"Error processing hourly data: {e}")
            final_hourly_df = pd.DataFrame(columns=['Time', 'Temperature', 'Humidity', 'Precip. Prob.'])

        # --- Daily Data Structuring ---
        daily_raw = data.get('daily', {})
        daily_df = pd.DataFrame({
            "Date": daily_raw.get('time', []),
            "Max Temp": [f"{t}{data['daily_units'].get('temperature_2m_max', '')}" for t in daily_raw.get('temperature_2m_max', [])],
            "Min Temp": [f"{t}{data['daily_units'].get('temperature_2m_min', '')}" for t in daily_raw.get('temperature_2m_min', '')],
            "Max UV Index": daily_raw.get('uv_index_max', []),
        })
        
        if not daily_df.empty:
            # Rename the first entry to 'Today'
            daily_df.loc[0, 'Date'] = 'Today'
            # Format the remaining dates
            daily_df['Date'] = daily_df['Date'].apply(
                lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%a, %b %d") if x != 'Today' and isinstance(x, str) else x
            )
        
        # --- Final Return ---
        return {
            'current': current_data,
            'hourly_df': final_hourly_df, # Returns the DataFrame WITH the 'Time' column
            'daily_df': daily_df[['Date', 'Max Temp', 'Min Temp', 'Max UV Index']]
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None # Returns None on API/network failure
    except Exception as e:
        print(f"An unexpected error occurred during weather data processing: {e}")
        return None # Returns None on any other processing error
    
def get_news_headlines(region: str) -> str:
    """
    Fetches top news headlines for the specified region using NewsAPI.

    Args:
        region: The NYC subregion (e.g., "Brooklyn", "The Bronx").

    Returns:
        A formatted string of headlines separated by a separator, or an error message.
    """
    # Get API key from config
    api_key = os.getenv('NEWS_API_KEY')

    # Construct the query to be broad for NYC news, and specific to the region
    search_query = f"New York City AND {region}"
    url = f"https://newsapi.org/v2/everything?q={search_query}&sortBy=publishedAt&language=en&pageSize=10&apiKey={api_key}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        articles = data.get('articles', [])
        
        if not articles:
            return f"No recent headlines found for {region}."

        # Format headlines for the marquee
        headlines = [f"📰 {article['title']}" for article in articles]
        
        # Use a distinctive separator for the continuous scroll effect
        return " \t • \t ".join(headlines) + " \t • \t "
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news data: {e}")
        return f"Error fetching news for {region}: API request failed."
    


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

        conn_params = {
            'user': user,
            'password': password,
            'account': account,
            'warehouse': warehouse,
            'database': database,
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

BINSYNC_VIEWS: Dict[str, str] = {
    "WASTE_TONNAGE": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_MONTHLY_WASTE_TONNAGE_BY_BOROUGH",
    "NON_OPERATIONAL_BINS": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_UNIQUE_NON_OPERATIONAL_BINS",
    "RECYCLING_DIVERSION_RATE": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_MONTHLY_RECYCLING_DIVERSION_RATE",
    "BIN_LOCATIONS": "DEV_PREMIER_LEAGUE.BIN_SYNC_SERVICE.VW_COMBINED_BIN_LOCATIONS"
}

def get_binsync_data_by_view(
    view_key: str,
    conn_params: Optional[Dict[str, str]] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    account: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Fetches data from a specified BinSync view in Snowflake.
    (This is the original function, unmodified, as its role is fetching raw data.)
    """
    view_key = view_key.upper()
    view_name = BINSYNC_VIEWS.get(view_key)
    
    if view_name is None:
        print(f"ERROR: Invalid view_key: '{view_key}'. Available keys are: {', '.join(BINSYNC_VIEWS.keys())}")
        return None
    
    query = f"SELECT * FROM {view_name};"
    
    print(f"\n=======================================================")
    print(f"Attempting to fetch data for view: {view_key}")
    print(f"=======================================================")

    df = fetch_data_from_snowflake(
        query=query,
        conn_params=conn_params,
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema
    )
    
    return df


def calculate_monthly_waste_metrics(connection_params: Optional[Dict] = None) -> Optional[pd.DataFrame]:
    """
    Fetches the raw recycling diversion data and aggregates it to provide
    the total waste, total recycled waste, and the true overall diversion 
    rate on a monthly basis across all boroughs.

    Args:
        connection_params (Optional[Dict]): Dictionary of Snowflake connection details.

    Returns:
        Optional[pd.DataFrame]: A DataFrame with the aggregated monthly metrics.
    """
    
    # 1. Fetch the raw monthly/borough data
    df = get_binsync_data_by_view(
        view_key='RECYCLING_DIVERSION_RATE',
        conn_params=connection_params
    )
    
    if df is None:
        print("Aggregation failed: Could not retrieve data for 'RECYCLING_DIVERSION_RATE'.")
        return None
    
    # 2. Perform the aggregation by 'MONTH'
    # We sum the tons to get the total amounts across all boroughs for the month.
    # The monthly average DIVERSION RATE is calculated from the *total* tons, 
    # not by averaging the existing DIVERSION_RATE_PERCENTAGE column (which 
    # would incorrectly weight the smaller boroughs).
    
    monthly_summary = df.groupby('MONTH').agg(
        # Aggregate 1: Total waste collected monthly
        TOTAL_WASTE_TONS_MONTHLY=('TOTAL_WASTE_TONS', 'sum'),
        
        # Aggregate 2: Total recycled waste monthly
        TOTAL_RECYCLED_TONS_MONTHLY=('TOTAL_RECYCLED_TONS', 'sum')
    ).reset_index()

    # Aggregate 3: Calculate the TRUE overall diversion rate for the month
    # Formula: (Total Recycled TONS / Total Waste TONS) * 100
    monthly_summary['DIVERSION_RATE_AVG_MONTHLY'] = (
        monthly_summary['TOTAL_RECYCLED_TONS_MONTHLY'] / 
        monthly_summary['TOTAL_WASTE_TONS_MONTHLY']
    ) * 100
    
    # 3. Round the aggregated metrics to 2 decimal places
    columns_to_round = [
        'TOTAL_WASTE_TONS_MONTHLY', 
        'TOTAL_RECYCLED_TONS_MONTHLY', 
        'DIVERSION_RATE_AVG_MONTHLY'
    ]
    monthly_summary[columns_to_round] = monthly_summary[columns_to_round].round(2)
    
    print("\n✅ SUCCESS: Calculated aggregated monthly metrics.")
    
    return monthly_summary

def get_bin_locations_data(connection_params: Optional[Dict] = None) -> Optional[pd.DataFrame]:
    """
    Fetches and cleans all bin locations (latitude, longitude, name)
    from the VW_COMBINED_BIN_LOCATIONS view.

    Args:
        connection_params (Optional[Dict]): Snowflake connection details.

    Returns:
        Optional[pd.DataFrame]: Clean DataFrame with 'lat', 'lon', and 'Name' columns.
    """
    # 1. Fetch the raw bin locations data
    df = get_binsync_data_by_view(
        view_key='BIN_LOCATIONS',
        conn_params=connection_params
    )

    if df is None or df.empty:
        print("⚠️ Data retrieval failed or empty for 'BIN_LOCATIONS'.")
        return None

    # 2. Normalize column names (make uppercase for consistency)
    df.columns = [col.upper().strip() for col in df.columns]

    # 3. Rename to Streamlit-compatible names
    rename_map = {
        'LATITUDE': 'lat',
        'LONGITUDE': 'lon',
        'NAME': 'Name',
        'BIN_TYPE': 'Type'
    }
    df = df.rename(columns=rename_map)

    # 4. Create placeholders if missing
    if 'lat' not in df.columns:
        df['lat'] = None
    if 'lon' not in df.columns:
        df['lon'] = None
    if 'Name' not in df.columns:
        df['Name'] = 'Bin Location'

    # 5. Remove invalid or garbage coordinates
    # Drop rows where lat/lon are missing, null, or not numbers
    df = df[pd.to_numeric(df['lat'], errors='coerce').notna()]
    df = df[pd.to_numeric(df['lon'], errors='coerce').notna()]
    df['lat'] = df['lat'].astype(float)
    df['lon'] = df['lon'].astype(float)

    # Filter out out-of-range coordinates (not on Earth)
    df = df[(df['lat'].between(-90, 90)) & (df['lon'].between(-180, 180))]

    # 6. Drop duplicates, reset index
    df = df.drop_duplicates(subset=['lat', 'lon', 'Name']).reset_index(drop=True)

    if df.empty:
        print("⚠️ All bin location rows were invalid or filtered out.")
        return None

    print(f"✅ SUCCESS: Fetched and cleaned {len(df)} bin locations.")
    return df[['lat', 'lon', 'Name']]
