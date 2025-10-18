# Save this file as app.py
import streamlit as st
import pandas as pd
import re # For parsing location data

# Import your new utility function
from utils import get_resilient_cities_data_by_view

# --- Page Configuration ---
st.set_page_config(page_title="Resilient Cities Dashboard", layout="wide")


# ==============================================================================
#                      1. DATA LOADING & PROCESSING
# ==============================================================================
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data():
    """Loads all data for the Resilient Cities dashboard from Snowflake."""
    emergency_df = get_resilient_cities_data_by_view("EMERGENCY_RESPONSE")
    projects_df = get_resilient_cities_data_by_view("CAPITAL_PROJECTS")
    requests_df = get_resilient_cities_data_by_view("311_REQUESTS")
    return emergency_df, projects_df, requests_df

# Load all the data
df_emergency, df_projects, df_311 = load_data()


# ==============================================================================
#                      2. HELPER FUNCTIONS FOR DISPLAY
# ==============================================================================
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

def parse_geom(geom_str):
    """Parses a WKT string like 'POINT (-73.9 40.7)' into lat/lon."""
    if not isinstance(geom_str, str):
        return None, None
    match = re.search(r"POINT\s*\(\s*(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*\)", geom_str)
    if match:
        return float(match.group(2)), float(match.group(1)) # lat, lon
    return None, None

# ==============================================================================
#                      3. STREAMLIT APP LAYOUT
# ==============================================================================

st.title("🏙️ NYC Resilient Cities Dashboard")

# Create the three tabs
tab1, tab2, tab3 = st.tabs([
    "Emergency Response Metrics", 
    "Capital Projects", 
    "311 Service Requests"
])


# ------------------------------------------------------------------------------
# --- TAB 1: EMERGENCY RESPONSE METRICS ---
# ------------------------------------------------------------------------------
with tab1:
    st.header("Weekly Emergency Response Times")
    if df_emergency is not None and not df_emergency.empty:
        # Normalize column names to uppercase for consistency
        df_emergency.columns = [col.upper() for col in df_emergency.columns]
        
        # Headers for the table display (excluding the grouping columns)
        headers = [
            "Final Incident Type", "# of Incidents", "First Pickup", "Calltaker Handoff", 
            "FDNY Pickup", "FDNY Job Creation", "EMS Pickup", "Agency Job Creation", 
            "Agency Dispatch", "Agency Arrival", "First Arrival (Multi-Agency)"
        ]
        
        # Data columns that correspond to the headers
        data_cols = [
            "FINAL_INCIDENT_TYPE", "NUMBER_OF_INCIDENTS", "FIRST_PICKUP", "CALLTAKER_HANDOFF",
            "FDNY_PICKUP", "FDNY_JOB_CREATION", "EMS_PICKUP", "AGENCY_JOB_CREATION",
            "AGENCY_DISPATCH", "AGENCY_ARRIVAL", "FIRST_ARRIVAL_MULTI_AGENCY"
        ]

        # Filter and display data for each section
        sections = ['EMS', 'FDNY', 'NYPD', 'NYPD (Non-CIP)']
        for section in sections:
            section_data = df_emergency[df_emergency['SECTION'] == section][data_cols]
            if not section_data.empty:
                display_emergency_table(section, section_data, headers)
    else:
        st.error("Could not load Emergency Response data from Snowflake.")


# ------------------------------------------------------------------------------
# --- TAB 2: CAPITAL PROJECTS ---
# ------------------------------------------------------------------------------
with tab2:
    st.header("NYC Capital Projects Overview")
    if df_projects is not None and not df_projects.empty:
        df_projects.columns = [col.upper() for col in df_projects.columns]

        # Show key metrics
        total_projects = df_projects['PROJECTID'].nunique()
        total_commitment = df_projects['PLANNEDCOMMIT_TOTAL'].sum()
        m1, m2 = st.columns(2)
        m1.metric("Total Unique Projects", f"{total_projects:,}")
        m2.metric("Total Planned Commitment", f"${total_commitment:,.0f}")
        st.markdown("---")

        # Map of project locations
        st.subheader("Project Locations")
        df_projects[['lat', 'lon']] = df_projects['THE_GEOM'].apply(parse_geom).apply(pd.Series)
        map_data = df_projects.dropna(subset=['lat', 'lon'])
        if not map_data.empty:
            st.map(map_data, zoom=10)
        else:
            st.warning("No valid location data found to display on the map.")
    else:
        st.error("Could not load Capital Projects data from Snowflake.")


# ------------------------------------------------------------------------------
# --- TAB 3: 311 SERVICE REQUESTS ---
# ------------------------------------------------------------------------------
with tab3:
    st.header("311 Service Requests Analysis")
    if df_311 is not None and not df_311.empty:
        df_311.columns = [col.upper() for col in df_311.columns]

        # Sidebar Filters
        st.sidebar.header("311 Filters")
        boroughs = ['ALL'] + sorted(df_311['BOROUGH'].dropna().unique().tolist())
        selected_borough = st.sidebar.selectbox("Select a Borough", boroughs)

        if selected_borough != 'ALL':
            df_filtered = df_311[df_311['BOROUGH'] == selected_borough]
        else:
            df_filtered = df_311

        # Display KPIs
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Total Requests Displayed", f"{len(df_filtered):,}")
        kpi2.metric("Open Requests", f"{len(df_filtered[df_filtered['STATUS'] == 'Open']):,}")
        st.markdown("---")

        # Charts
        st.subheader("Top 5 Complaint Types")
        top_complaints = df_filtered['COMPLAINT_TYPE'].value_counts().nlargest(5)
        st.bar_chart(top_complaints)

        with st.expander("View Filtered Data Table"):
            st.dataframe(df_filtered.head(1000))
    else:
        st.error("Could not load 311 Service Requests data from Snowflake.")