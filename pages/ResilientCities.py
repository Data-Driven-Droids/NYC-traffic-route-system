import streamlit as st
import pandas as pd
import numpy as np
import re # For parsing location data
import altair as alt # Added for better charts
from streamlit.components.v1 import html # Import for embedding HTML
from utils import get_resilient_cities_data_by_view

# --- Page Configuration ---
st.set_page_config(page_title="Resilient Cities Dashboard", layout="wide")


# ==============================================================================
# 1. DATA LOADING DEFINITION
# ==============================================================================
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data():
    """
    Loads all data for the Resilient Cities dashboard.
    - Emergency Response data is static/mocked.
    - 311 Requests data is fetched from Snowflake via utils.
    """
    
    # --- Load Emergency Response Data (Static) ---
    # This logic was moved from the old mock function
    try:
        emergency_data = {
            'SECTION': ['EMS', 'EMS', 'EMS', 'FDNY', 'FDNY', 'NYPD', 'NYPD', 'NYPD', 'NYPD', 'NYPD (Non-CIP)'],
            'FINAL_INCIDENT_TYPE': ['Cardiac', 'Difficulty Breathing', 'Injury', 'Structural Fire', 'Vehicle Fire', 'Assault', 'Robbery', 'Burglary', 'Larceny', 'Noise Complaint'],
            'NUMBER_OF_INCIDENTS': [120, 95, 210, 30, 15, 80, 45, 60, 110, 350],
            'FIRST_PICKUP': ['0:05', '0:06', '0:04', '0:07', '0:05', '0:08', '0:06', '0:07', '0:05', '0:10'],
            'CALLTAKER_HANDOFF': ['0:45', '0:50', '0:42', '0:55', '0:48', '1:05', '0:58', '1:02', '0:55', '1:15'],
            'FDNY_PICKUP': [None, None, None, '1:10', '1:05', None, None, None, None, None],
            'FDNY_JOB_CREATION': [None, None, None, '1:30', '1:25', None, None, None, None, None],
            'EMS_PICKUP': ['1:02', '1:05', '0:59', None, None, None, None, None, None, None],
            'AGENCY_JOB_CREATION': ['1:15', '1:20', '1:10', '1:32', '1:28', '1:30', '1:25', '1:28', '1:22', '1:40'],
            'AGENCY_DISPATCH': ['2:30', '2:45', '2:20', '2:05', '2:00', '3:10', '3:00', '3:05', '2:50', '3:30'],
            'AGENCY_ARRIVAL': ['8:30', '9:15', '7:45', '5:30', '6:15', '10:15', '9:45', '11:00', '9:20', '12:30'],
            'FIRST_ARRIVAL_MULTI_AGENCY': ['8:30', '9:15', '7:45', '5:30', '6:15', '10:15', '9:45', '11:00', '9:20', '12:30']
        }
        emergency_df = pd.DataFrame(emergency_data)
    except Exception as e:
        st.error(f"Error creating static Emergency Response data: {e}")
        emergency_df = pd.DataFrame()

    # --- Load 311 Requests Data (Live from Snowflake) ---
    # This calls the real function from utils, as requested
    try:
        requests_df = get_resilient_cities_data_by_view("311_REQUESTS")
    except Exception as e:
        st.error(f"Error fetching 311 data from Snowflake: {e}")
        requests_df = pd.DataFrame()
    
    return emergency_df, requests_df

# ==============================================================================
# 2. HELPER FUNCTIONS FOR DISPLAY
# ==============================================================================

def time_str_to_seconds(time_str):
    """Converts MM:SS or HH:MM:SS string to total seconds."""
    if not isinstance(time_str, str) or pd.isna(time_str) or time_str in [':', '']:
        return None
    try:
        parts = time_str.split(':')
        seconds = 0
        if len(parts) == 2: # MM:SS
            seconds = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3: # HH:MM:SS
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return seconds
    except (ValueError, TypeError):
        return None

def format_seconds_to_mm_ss(seconds):
    """Converts total seconds to a MM:SS string."""
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    seconds_rem = int(seconds % 60)
    return f"{minutes}:{seconds_rem:02d}"

def display_emergency_table(title, data, headers):
    """Helper function to render a formatted table section for Tab 1."""
    st.subheader(title)
    header_cols = st.columns(len(headers))
    for i, header in enumerate(headers):
        header_cols[i].markdown(f"**{header}**")
    st.markdown("<hr style='margin: 0.5em 0; border-color: #555;'>", unsafe_allow_html=True)
    for _, row in data.iterrows():
        row_cols = st.columns(len(headers))
        for i, item in enumerate(row):
            align = "left" if i == 0 else "center"
            row_cols[i].markdown(f"<div style='text-align: {align};'>{item or ':'}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# 3. STATIC UI & PLACEHOLDER SETUP
# ==============================================================================
st.title("🏙️ NYC Resilient Cities Dashboard")

# --- "About" section ---
with st.expander("ℹ️ About This Dashboard", expanded=False):
    st.markdown("""
    This dashboard provides a multi-faceted view of New York City's resilience and operational status,
    drawing live data from several city databases.
    * **Emergency Response Metrics:** Tracks weekly response times for 911 calls, segmented by agency (EMS, FDNY, NYPD).
    * **Capital Projects:** Shows future development projects for the city, rendered from an embedded dashboard.
    * **311 Service Requests:** Analyzes non-emergency 311 service requests, filterable by borough and status.
    """)
st.markdown("---")

# Create the three tabs
tab1, tab2, tab3 = st.tabs([
    "Emergency Response Metrics",
    "Capital Projects",
    "311 Service Requests"
])

# --- Content for TAB 1 ---
with tab1:
    st.header("Weekly Emergency Response Times")
    ph_tab1 = st.empty()
    ph_tab1.info("Loading Emergency Response data...")

# --- Content for TAB 2 (Embed) ---
with tab2:
    st.header("Future Development Projects")
    st.write("This interactive dashboard shows future development projects.")
    
    EMBED_CODE = """
    <iframe title="Future Development Projects New York"
    width="100%"
    height="750"
    src="https://app.powerbigov.us/view?r=eyJrIjoiMTkwYWMyNGEtMDNiZC00OTY4LTk4YjEtYzI0MzhlOTA3MzllIiwidCI6IjM1YzgyODE2LTZjNTYtNDQzYi1iYWY2LTgzMTIxNjNjYWRjMSJ9"
    frameborder="0"
    allowFullScreen="true">
    </iframe>
    """
    html(EMBED_CODE, height=670, scrolling=True)


# --- Placeholders for TAB 3 ---
with tab3:
    ph_tab3 = st.empty()
    ph_tab3.info("Loading 311 Service Requests data from Snowflake...")


# ==============================================================================
# 4. DATA FETCHING & PROCESSING
# ==============================================================================

# This single call now runs the combined data loading function
df_emergency, df_311 = load_data()


# ==============================================================================
# 5. POPULATE DYNAMIC TABS
# ==============================================================================

# --- Populate TAB 1 ---
ph_tab1.empty()
with ph_tab1.container():
    if df_emergency is not None and not df_emergency.empty:
        df_emergency.columns = [col.upper() for col in df_emergency.columns]
        time_cols_to_convert = [
            "FIRST_PICKUP", "CALLTAKER_HANDOFF", "FDNY_PICKUP", "FDNY_JOB_CREATION",
            "EMS_PICKUP", "AGENCY_JOB_CREATION", "AGENCY_DISPATCH", "AGENCY_ARRIVAL",
            "FIRST_ARRIVAL_MULTI_AGENCY"
        ]
        for col in time_cols_to_convert:
            if col in df_emergency.columns:
                df_emergency[f'{col}_SEC'] = df_emergency[col].apply(time_str_to_seconds)
            
        if 'NUMBER_OF_INCIDENTS' in df_emergency.columns:
            df_emergency['NUMBER_OF_INCIDENTS'] = pd.to_numeric(
                df_emergency['NUMBER_OF_INCIDENTS'], errors='coerce'
            ).fillna(0)
        else:
            st.error("Column 'NUMBER_OF_INCIDENTS' not found.")
            st.stop()
            
        table_headers = [
            "Final Incident Type", "# of Incidents", "First Pickup", "Calltaker Handoff",
            "FDNY Pickup", "FDNY Job Creation", "EMS Pickup", "Agency Job Creation",
            "Agency Dispatch", "Agency Arrival", "First Arrival (Multi-Agency)"
        ]
        table_data_cols = [
            "FINAL_INCIDENT_TYPE", "NUMBER_OF_INCIDENTS", "FIRST_PICKUP", "CALLTAKER_HANDOFF",
            "FDNY_PICKUP", "FDNY_JOB_CREATION", "EMS_PICKUP", "AGENCY_JOB_CREATION",
            "AGENCY_DISPATCH", "AGENCY_ARRIVAL", "FIRST_ARRIVAL_MULTI_AGENCY"
        ]
        
        sections = ['EMS', 'FDNY', 'NYPD', 'NYPD (Non-CIP)']
        for section in sections:
            section_data = df_emergency[df_emergency['SECTION'] == section].copy()
            if not section_data.empty:
                st.subheader(f"Performance Metrics: {section}")
                
                total_incidents = section_data['NUMBER_OF_INCIDENTS'].sum()
                avg_arrival_time_sec = section_data['AGENCY_ARRIVAL_SEC'].mean()
                avg_arrival_str = format_seconds_to_mm_ss(avg_arrival_time_sec)

                kpi_col1, kpi_col2 = st.columns(2)
                kpi_col1.metric("Total Incidents", f"{total_incidents:,.0f}")
                kpi_col2.metric("Avg. Agency Arrival Time", avg_arrival_str)

                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.markdown("Top 5 Incident Types by Volume")
                    volume_data = section_data.nlargest(5, 'NUMBER_OF_INCIDENTS')
                    chart_v = alt.Chart(volume_data).mark_bar().encode(
                        x=alt.X('NUMBER_OF_INCIDENTS:Q', title='Number of Incidents'),
                        y=alt.Y('FINAL_INCIDENT_TYPE:N', title='Incident Type', sort='-x'),
                        tooltip=['FINAL_INCIDENT_TYPE', 'NUMBER_OF_INCIDENTS']
                    ).interactive()
                    st.altair_chart(chart_v, use_container_width=True)

                with chart_col2:
                    st.markdown("Top 5 Slowest Avg. Arrival Times")
                    perf_data = section_data.nlargest(5, 'AGENCY_ARRIVAL_SEC')
                    chart_p = alt.Chart(perf_data).mark_bar(color='#d62728').encode(
                        x=alt.X('AGENCY_ARRIVAL_SEC:Q', title='Avg. Arrival (Seconds)'),
                        y=alt.Y('FINAL_INCIDENT_TYPE:N', title='Incident Type', sort='-x'),
                        tooltip=['FINAL_INCIDENT_TYPE', 'AGENCY_ARRIVAL']
                    ).interactive()
                    st.altair_chart(chart_p, use_container_width=True)

                with st.expander(f"View Raw Data Table for {section}"):
                    table_display_data = section_data[table_data_cols]
                    display_emergency_table(f"{section} Data", table_display_data, table_headers)

                st.markdown("---")
    else:
        st.error("Could not load Emergency Response data.")


# --- Populate TAB 3 (MODIFIED) ---
ph_tab3.empty()
with ph_tab3.container():
    if df_311 is None or df_311.empty:
        st.error("Could not load 311 Service Requests data from Snowflake.")
    else:
        df_311.columns = [col.upper() for col in df_311.columns]
        
        if 'AGENCY_NAME' not in df_311.columns or 'COMPLAINT_TYPE' not in df_311.columns:
            st.error("311 data is missing required columns: 'AGENCY_NAME' or 'COMPLAINT_TYPE'.")
        else:
            if 'CREATED_DATE' not in df_311.columns:
                st.warning("311 data missing 'CREATED_DATE'. Using current time as fallback.")
                df_311['CREATED_DATE'] = pd.to_datetime(pd.Timestamp.now())
            else:
                df_311['CREATED_DATE'] = pd.to_datetime(df_311['CREATED_DATE'])
                
            if 'BOROUGH' not in df_311.columns:
                df_311['BOROUGH'] = 'Unknown'
                
            df_311['AGENCY_SERVICE'] = df_311['AGENCY_NAME'] + ' - ' + df_311['COMPLAINT_TYPE']
            

            st.header("Monitoring Tool: Neighborhood")
            neighborhoods = ['All'] + sorted(df_311['BOROUGH'].unique())
            selected_neighborhood = st.selectbox("Neighborhood", neighborhoods)
            st.subheader("Top Five Service Requests in Selected Neighborhood")

            # --- Dynamic Date Logic ---
            latest_date = df_311['CREATED_DATE'].max()
            current_period = pd.Period(latest_date, 'M')
            previous_period = current_period - 1
            st.caption(f"Comparing {current_period.strftime('%B %Y')} to {previous_period.strftime('%B %Y')}")

            # --- Top 5 Table Logic (with previous month comparison) ---
            current_month_data = df_311[df_311['CREATED_DATE'].dt.to_period('M') == current_period]
            previous_month_data = df_311[df_311['CREATED_DATE'].dt.to_period('M') == previous_period]

            if selected_neighborhood != 'All':
                current_month_data = current_month_data[current_month_data['BOROUGH'] == selected_neighborhood]
                previous_month_data = previous_month_data[previous_month_data['BOROUGH'] == selected_neighborhood]

            current_counts = current_month_data['AGENCY_SERVICE'].value_counts().reset_index(name='Requests_Current')
            current_counts.columns = ['AGENCY_SERVICE', 'Requests_Current']
            previous_counts = previous_month_data['AGENCY_SERVICE'].value_counts().reset_index(name='Requests_Previous')
            previous_counts.columns = ['AGENCY_SERVICE', 'Requests_Previous']
            
            top_5_base = current_counts.nlargest(5, 'Requests_Current')
            top_5_df = pd.merge(top_5_base, previous_counts, on='AGENCY_SERVICE', how='left').fillna(0)
            
            # Calculate percentage change, handling division by zero
            top_5_df['% Change'] = ((top_5_df['Requests_Current'] - top_5_df['Requests_Previous']) / top_5_df['Requests_Previous'].replace(0, np.nan) * 100)
            
            # --- Display Table (with comparison) ---
            h_cols = st.columns([3, 1.5, 1.5, 1])
            h_cols[0].markdown("**Agency & Service Request**")
            h_cols[1].markdown(f"**Requests ({previous_period.strftime('%b %Y')})**")
            h_cols[2].markdown(f"**Requests ({current_period.strftime('%b %Y')})**")
            h_cols[3].markdown(f"**% Change**")
            st.markdown("---")

            for _, row in top_5_df.iterrows():
                r_cols = st.columns([3, 1.5, 1.5, 1])
                r_cols[0].write(row['AGENCY_SERVICE'])
                r_cols[1].markdown(f"<div style='text-align: center;'>{int(row['Requests_Previous']):,}</div>", unsafe_allow_html=True)
                r_cols[2].markdown(f"<div style='text-align: center;'>{int(row['Requests_Current']):,}</div>", unsafe_allow_html=True)
                
                change_val = row['% Change']
                # Determine color and text for % Change
                if pd.isna(change_val):
                    if row['Requests_Previous'] == 0 and row['Requests_Current'] > 0:
                        change_str = "<span style='color:red;'>New</span>"
                    else:
                        change_str = "-" # Should not happen if previous is 0, but as a fallback
                else:
                    color = 'red' if change_val > 0 else 'green'
                    change_str = f"<span style='color:{color}'>{change_val:+.1f}%</span>"
                
                r_cols[3].markdown(f"<div style='text-align: center;'>{change_str}</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            service_requests = ['All'] + sorted(df_311['AGENCY_SERVICE'].unique())
            selected_service_request = st.selectbox("Service Request", service_requests)
            
            # --- Time Series Chart ---
            st.subheader(f"Neighborhood: {selected_neighborhood} | Agency & Service Request: {selected_service_request}")
            ts_df = df_311.copy()
            if selected_neighborhood != 'All':
                ts_df = ts_df[ts_df['BOROUGH'] == selected_neighborhood]
            if selected_service_request != 'All':
                ts_df = ts_df[ts_df['AGENCY_SERVICE'] == selected_service_request]

            monthly_counts = ts_df.set_index('CREATED_DATE').resample('M').size().reset_index(name='Requests')
            monthly_counts['Date'] = monthly_counts['CREATED_DATE']
            monthly_counts['12-Month Moving Average'] = monthly_counts['Requests'].rolling(window=12).mean()

            bar = alt.Chart(monthly_counts).mark_bar().encode(
                x=alt.X('Date:T', title=''),
                y=alt.Y('Requests:Q', title='Number of Service Requests'),
                tooltip=['Date', 'Requests']
            )
            line = alt.Chart(monthly_counts).mark_line(color='orange').encode(
                x=alt.X('Date:T', title=''),
                y=alt.Y('12-Month Moving Average:Q', title='Moving Average'),
                tooltip=['Date', '12-Month Moving Average']
            )
            chart = (bar + line).interactive()
            st.altair_chart(chart, use_container_width=True)

            # --- Map Section ---
            st.subheader("Service Request Neighborhood Map")
            st.caption("Select a time period and filters to see requests on the map.")
            import datetime
            min_date = df_311['CREATED_DATE'].min().date()
            max_date = df_311['CREATED_DATE'].max().date()

            default_start = max(min_date, datetime.date(2025, 9, 1))
            default_end = min(max_date, datetime.date(2025, 9, 30))
            
            if default_start > default_end:
                default_start = min_date

            date_range = st.date_input(
                "Date Range",
                (default_start, default_end),
                min_value=min_date,
                max_value=max_date,
                format="MM.DD.YYYY",
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                start_datetime = pd.to_datetime(start_date)
                end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

                map_df = df_311.copy()
                map_df = map_df[
                    (map_df['CREATED_DATE'] >= start_datetime) &
                    (map_df['CREATED_DATE'] < end_datetime)
                ]
                
                if selected_neighborhood != 'All':
                    map_df = map_df[map_df['BOROUGH'] == selected_neighborhood]
                if selected_service_request != 'All':
                    map_df = map_df[map_df['AGENCY_SERVICE'] == selected_service_request]

                default_lat = 40.7580
                default_lon = -73.9855

                if 'LATITUDE' not in map_df.columns or 'LONGITUDE' not in map_df.columns:
                    st.error("Map cannot be displayed: Latitude/Longitude columns not found in 311 data.")
                elif map_df.empty:
                    st.info("No requests found for the selected filters. Showing default NYC location.")
                    map_df_display = pd.DataFrame([{'lat': default_lat, 'lon': default_lon}])
                    st.map(map_df_display)
                
                else:
                    map_df_display = map_df[['LATITUDE', 'LONGITUDE']].copy()
                    map_df_display.rename(columns={'LATITUDE': 'lat', 'LONGITUDE': 'lon'}, inplace=True)
                    map_df_display['lat'] = pd.to_numeric(map_df_display['lat'], errors='coerce')
                    map_df_display['lon'] = pd.to_numeric(map_df_display['lon'], errors='coerce')

                    # Fill NaNs with default NYC coords *after* coercion
                    map_df_display['lat'].fillna(default_lat, inplace=True)
                    map_df_display['lon'].fillna(default_lon, inplace=True)
                    
                    st.map(map_df_display)

            else:
                st.info("Please select a valid date range to display the map.")