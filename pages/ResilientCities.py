import streamlit as st
import pandas as pd
import re # For parsing location data

# Import your new utility function
from utils import get_resilient_cities_data_by_view

# --- Page Configuration ---
st.set_page_config(page_title="Resilient Cities Dashboard", layout="wide")


# ==============================================================================
#                 1. DATA LOADING DEFINITION
# ==============================================================================
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data():
    """Loads all data for the Resilient Cities dashboard from Snowflake."""
    emergency_df = get_resilient_cities_data_by_view("EMERGENCY_RESPONSE")
    projects_df = get_resilient_cities_data_by_view("CAPITAL_PROJECTS")
    requests_df = get_resilient_cities_data_by_view("311_REQUESTS")
    return emergency_df, projects_df, requests_df

# ==============================================================================
#                 2. HELPER FUNCTIONS FOR DISPLAY
# ==============================================================================
def display_emergency_table(title, data, headers):
    """Helper function to render a formatted table section for Tab 1."""
    # This helper writes to the current 'st' context,
    # so we'll call it inside a container.
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

def parse_geom(geom_str):
    """Parses a WKT string like 'POINT (-73.9 40.7)' into lat/lon."""
    if not isinstance(geom_str, str):
        return None, None
    match = re.search(r"POINT\s*\(\s*(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*\)", geom_str)
    if match:
        return float(match.group(2)), float(match.group(1)) # lat, lon
    return None, None

# ==============================================================================
#                 3. STATIC UI & PLACEHOLDER SETUP
# ==============================================================================
st.title("City Scope 360 Dashboard")
st.markdown("""This is just a prototype for New York City.""")

st.title("🏙️ NYC Resilient Cities Dashboard")

# --- "About" section ---
with st.expander("ℹ️ About This Dashboard", expanded=False):
    st.markdown("""
    This dashboard provides a multi-faceted view of New York City's resilience and operational status, 
    drawing live data from several city databases.
    
    * **Emergency Response Metrics:** Tracks weekly response times for 911 calls, segmented by agency (EMS, FDNY, NYPD).
    * **Capital Projects:** Shows the locations and financial commitments for major city capital projects.
    * **311 Service Requests:** Analyzes non-emergency 311 service requests, filterable by borough and status.
    
    All data is fetched from Snowflake views and cached for one hour.
    """)
st.markdown("---")

# Create the three tabs
tab1, tab2, tab3 = st.tabs([
    "Emergency Response Metrics", 
    "Capital Projects", 
    "311 Service Requests"
])

# --- Placeholders for TAB 1 ---
with tab1:
    st.header("Weekly Emergency Response Times")
    # A single placeholder for the whole tab's content
    ph_tab1 = st.empty()
    ph_tab1.info("Loading Emergency Response data from Snowflake...")

# --- Placeholders for TAB 2 ---
with tab2:
    st.header("NYC Capital Projects Overview")
    
    # Placeholders for metrics
    m1, m2 = st.columns(2)
    ph_m1 = m1.empty()
    ph_m2 = m2.empty()
    ph_m1.info("Loading metrics...")
    ph_m2.info("Loading metrics...")
    st.markdown("---")

    # Placeholder for map
    st.subheader("Project Locations")
    ph_map = st.empty()
    ph_map.info("Loading project locations map...")

# --- Placeholders for TAB 3 ---
with tab3:
    st.header("311 Service Requests Analysis")
    
    # Sidebar placeholder
    st.sidebar.header("311 Filters")
    ph_sidebar_filter = st.sidebar.empty()
    ph_sidebar_filter.info("Loading filters...")

    # Placeholders for KPIs
    kpi1, kpi2 = st.columns(2)
    ph_kpi1 = kpi1.empty()
    ph_kpi2 = kpi2.empty()
    ph_kpi1.info("Loading KPIs...")
    ph_kpi2.info("Loading KPIs...")
    st.markdown("---")

    # Placeholder for chart
    st.subheader("Top 5 Complaint Types")
    ph_chart_311 = st.empty()
    ph_chart_311.info("Loading chart data...")

    # Placeholder for data table
    with st.expander("View Filtered Data Table"):
        ph_table_311 = st.empty()
        ph_table_311.info("Loading data table...")


# ==============================================================================
#                 4. DATA FETCHING & PROCESSING
# ==============================================================================

# This is the main blocking call. It runs AFTER all placeholders are drawn.
df_emergency, df_projects, df_311 = load_data()


# ==============================================================================
#                 5. POPULATE PLACEHOLDERS
# ==============================================================================

# --- Populate TAB 1 ---
ph_tab1.empty() # Clear the "Loading..." message
with ph_tab1.container(): # Use a container to write content into the cleared space
    if df_emergency is not None and not df_emergency.empty:
        df_emergency.columns = [col.upper() for col in df_emergency.columns]
        
        headers = [
            "Final Incident Type", "# of Incidents", "First Pickup", "Calltaker Handoff", 
            "FDNY Pickup", "FDNY Job Creation", "EMS Pickup", "Agency Job Creation", 
            "Agency Dispatch", "Agency Arrival", "First Arrival (Multi-Agency)"
        ]
        
        data_cols = [
            "FINAL_INCIDENT_TYPE", "NUMBER_OF_INCIDENTS", "FIRST_PICKUP", "CALLTAKER_HANDOFF",
            "FDNY_PICKUP", "FDNY_JOB_CREATION", "EMS_PICKUP", "AGENCY_JOB_CREATION",
            "AGENCY_DISPATCH", "AGENCY_ARRIVAL", "FIRST_ARRIVAL_MULTI_AGENCY"
        ]

        sections = ['EMS', 'FDNY', 'NYPD', 'NYPD (Non-CIP)']
        for section in sections:
            section_data = df_emergency[df_emergency['SECTION'] == section][data_cols]
            if not section_data.empty:
                # Call the helper function, which writes to the current context (this container)
                display_emergency_table(section, section_data, headers)
    else:
        st.error("Could not load Emergency Response data from Snowflake.")


# --- Populate TAB 2 ---
if df_projects is not None and not df_projects.empty:
    df_projects.columns = [col.upper() for col in df_projects.columns]

    # Process data
    df_projects['PLANNEDCOMMIT_TOTAL'] = pd.to_numeric(
        df_projects['PLANNEDCOMMIT_TOTAL'], errors='coerce'
    )
    total_projects = df_projects['PROJECTID'].nunique()
    total_commitment = df_projects['PLANNEDCOMMIT_TOTAL'].sum()
    
    # Populate metrics
    ph_m1.metric("Total Unique Projects", f"{total_projects:,}")
    ph_m2.metric("Total Planned Commitment", f"${total_commitment:,.0f}")

    # Process and populate map
    df_projects[['lat', 'lon']] = df_projects['THE_GEOM'].apply(parse_geom).apply(pd.Series)
    map_data = df_projects.dropna(subset=['lat', 'lon'])
    
    if not map_data.empty:
        ph_map.map(map_data, zoom=10)
    else:
        ph_map.warning("No valid location data found to display on the map.")
else:
    # Handle data load failure for Tab 2
    ph_m1.error("Data load failed")
    ph_m2.error("Data load failed")
    ph_map.error("Could not load Capital Projects data from Snowflake.")


# --- Populate TAB 3 ---
if df_311 is not None and not df_311.empty:
    df_311.columns = [col.upper() for col in df_311.columns]

    # Populate Sidebar Filter
    ph_sidebar_filter.empty() # Clear "Loading..."
    boroughs = ['ALL'] + sorted(df_311['BOROUGH'].dropna().unique().tolist())
    selected_borough = ph_sidebar_filter.selectbox("Select a Borough", boroughs)

    # Filter data based on selection
    if selected_borough != 'ALL':
        df_filtered = df_311[df_311['BOROUGH'] == selected_borough]
    else:
        df_filtered = df_311

    # Populate KPIs
    ph_kpi1.metric("Total Requests Displayed", f"{len(df_filtered):,}")
    ph_kpi2.metric("Open Requests", f"{len(df_filtered[df_filtered['STATUS'] == 'Open']):,}")

    # Populate Chart
    top_complaints = df_filtered['COMPLAINT_TYPE'].value_counts().nlargest(5)
    ph_chart_311.bar_chart(top_complaints)

    # Populate Data Table
    ph_table_311.dataframe(df_filtered.head(1000))
else:
    # Handle data load failure for Tab 3
    ph_sidebar_filter.error("Data failed")
    ph_kpi1.error("Data load failed")
    ph_kpi2.error("Data load failed")
    ph_chart_311.error("Data load failed")
    ph_table_311.error("Could not load 311 Service Requests data from Snowflake.")