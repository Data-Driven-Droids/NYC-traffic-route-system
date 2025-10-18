# Save this file as app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
# Make sure your utils.py file is in the same directory
from utils import get_city_guard_data_by_view 

# --- Configuration ---
st.set_page_config(layout="wide", page_title="City Guard & Urban SOS")
if 'selected_crime' not in st.session_state:
    st.session_state.selected_crime = None

# ==============================================================================
#                       1. DATA LOADING & PROCESSING
# ==============================================================================

@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_all_data():
    """Loads and processes all data from Snowflake using the specific view function."""
    
    print("--- Loading fresh data from Snowflake... ---")
    df_service_calls = get_city_guard_data_by_view("SERVICE_CALLS")
    df_use_of_force = get_city_guard_data_by_view("USE_OF_FORCE")
    
    processed_data = {
        "dispatch": {},
        "force": {}
    }

    # --- Process Data for Tab 1: Dispatch Activity ---
    if df_service_calls is not None and not df_service_calls.empty:
        df_service_calls.columns = [col.upper() for col in df_service_calls.columns]
        processed_data["dispatch"]["total_calls"] = f"{len(df_service_calls):,}"
        
        cip_counts = df_service_calls['CIP_JOBS'].value_counts(normalize=True).mul(100).rename_axis('Type').reset_index(name='Percentage')
        cip_counts['Type'] = cip_counts['Type'].map({'Y': 'CIP', 'N': 'Non CIP'})
        processed_data["dispatch"]["df_cip"] = cip_counts
        
        processed_data["dispatch"]["df_calls"] = df_service_calls['TYP_DESC'].value_counts().rename_axis('Category').reset_index(name='Calls')
        processed_data["dispatch"]["df_borough"] = df_service_calls['BORO_NM'].value_counts(normalize=True).mul(100).rename_axis('Borough').reset_index(name='Percentage')
        
        critical_serious_count = df_service_calls[df_service_calls['TYP_DESC'].isin(['CRITICAL', 'SERIOUS'])].shape[0]
        processed_data["dispatch"]["total_critical_serious"] = f"{critical_serious_count:,}"
    
    # --- Process Data for Tab 2: Force Dashboard ---
    if df_use_of_force is not None and not df_use_of_force.empty:
        df_use_of_force.columns = [col.upper() for col in df_use_of_force.columns]
        processed_data["force"]["total_incidents"] = f"{df_use_of_force['TRI_INCIDENT_NUMBER'].nunique():,}"
        
        df_incidents_month = df_use_of_force.groupby('YEARMONTHSHORT')['TRI_INCIDENT_NUMBER'].nunique().reset_index()
        df_incidents_month.columns = ['Month', 'Incidents']
        processed_data["force"]["df_incidents_month"] = df_incidents_month
        
        processed_data["force"]["df_force_type"] = df_use_of_force['FORCETYPE'].value_counts(normalize=True).mul(100).rename_axis('Type').reset_index(name='Percentage')
        processed_data["force"]["df_basis"] = df_use_of_force['BASISFORENCOUNTER'].value_counts(normalize=True).mul(100).rename_axis('Basis').reset_index(name='Percentage')

    return processed_data

# --- Static Data for Tab 3: CompStat ---
COMPSTAT_DATA = [
    ["Murder", 5, 4, 25.0, 18, 24, -25.0, 255], ["Rape", 44, 33, 33.3, 152, 155, -1.9, 1694], ["Robbery", 284, 328, -13.4, 1231, 1322, -6.9, 11921], ["Felony Assault", 562, 560, -12.1, 2243, 2324, -3.5, 23397],
    ["Burglary", 233, 258, -9.7, 912, 1070, -14.8, 9842], ["Grand Larceny", 917, 924, -0.8, 3864, 3812, 1.3, 37269], ["Grand Larceny Auto", 274, 302, -9.3, 1116, 1232, -9.4, 10849], ["Total", 2409, 2409, -6.6, 9636, 10039, -4.0, 95127],
    ["Patrol", 2113, 2266, -6.8, 9058, 9430, -3.9, 88933], ["Transit", 35, 37, -5.4, 119, 167, -28.7, 1639], ["Housing", 101, 106, -4.7, 459, 442, 3.8, 4555],
    ["Shooting Victims", 9, 18, -50.0, 61, 93, -34.4, 715], ["Shooting Incidents", 9, 16, -43.8, 50, 73, -31.5, 571], ["UCR Rape*", 61, 43, 41.9, 198, 209, -5.3, 1975], ["Other Sex Crimes", 128, 118, 8.5, 442, 467, -5.4, 4346]
]
df_compstat = pd.DataFrame(COMPSTAT_DATA, columns=["Crime", "2025", "2024", "% Chg", "2025_28Day", "2024_28Day", "% Chg_28Day", "Total"])
df_display = df_compstat.copy()
for col in ["2025", "2024", "2025_28Day", "2024_28Day", "Total", "% Chg", "% Chg_28Day"]:
    df_display[col] = df_display[col].apply(lambda x: f"{x:,.1f}%" if "%" in col else f"{x:,.0f}")
df_final_display = pd.DataFrame({
    "CompStat Book": df_display["Crime"], "Wk 2025": df_display["2025"], "Wk 2024": df_display["2024"], 
    "Wk % Chg": df_display["% Chg"], "28D 2025": df_display["2025_28Day"], "28D 2024": df_display["2024_28Day"], 
    "28D % Chg": df_display["% Chg_28Day"], "YTD Total": df_display["Total"]
})


# Load the live data
all_data = load_all_data()
dispatch_data = all_data.get("dispatch", {})
force_data = all_data.get("force", {})


# ==============================================================================
#                       CHART PLOTTING FUNCTIONS
# ==============================================================================
def plot_cip_vs_non_cip(df):
    if df is None or df.empty: return st.warning("CIP data not available.")
    fig = px.pie(df, values='Percentage', names='Type', title='CIP vs Non CIP Calls For Service', color_discrete_sequence=['#ff4b4b', '#3182bd'], hole=0.5)
    st.plotly_chart(fig, use_container_width=True)

def plot_cip_calls_by_type(df):
    if df is None or df.empty: return st.warning("Call type data not available.")
    fig = px.bar(df, x='Category', y='Calls', title='Calls by Type')
    st.plotly_chart(fig, use_container_width=True)

def plot_calls_by_borough(df):
    if df is None or df.empty: return st.warning("Borough data not available.")
    fig = px.pie(df, values='Percentage', names='Borough', title='Calls by Borough', hole=.4)
    st.plotly_chart(fig, use_container_width=True)

def plot_incidents_by_month(df):
    if df is None or df.empty: return st.warning("Monthly incident data not available.")
    fig = px.bar(df, x='Month', y='Incidents', title='Incidents by Month')
    st.plotly_chart(fig, use_container_width=True)

def plot_type_of_force(df):
    if df is None or df.empty: return st.warning("Use of force type data not available.")
    fig = px.bar(df, x='Type', y='Percentage', title='Type of Force')
    st.plotly_chart(fig, use_container_width=True)

def plot_basis_for_encounter(df):
    if df is None or df.empty: return st.warning("Basis for encounter data not available.")
    fig = px.bar(df, y='Basis', x='Percentage', orientation='h', title='Basis for Encounter')
    st.plotly_chart(fig, use_container_width=True)

def plot_incident_bar_chart(crime_name):
    df = pd.DataFrame({'Borough': ['PBBN', 'PBBS', 'PBBX', 'PBSI'], 'Incidents': [1, 1, 2, 1]})
    fig = px.bar(df, x='Borough', y='Incidents', title=f'Patrol Borough - Week to Date<br>{crime_name}', color_discrete_sequence=['#3182bd'])
    st.plotly_chart(fig, use_container_width=True)

def plot_incident_line_chart(crime_name):
    df = pd.DataFrame({'Date': pd.to_datetime(['10/06/25', '10/07/25', '10/08/25', '10/09/25', '10/10/25', '10/11/25', '10/12/25']), 'Value': [1.5, 1.2, 0.8, 0.5, 1.0, 0.9, 1.1]})
    fig = px.line(df, x='Date', y='Value', title=f'Timeline - Week to Date<br>{crime_name}', markers=True, color_discrete_sequence=['#ff4b4b'])
    st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
#                       STREAMLIT APPLICATION LAYOUT
# ==============================================================================

st.title("NYPD Dashboards")

# --- MODIFICATION: ADDED "ABOUT THIS PAGE" SECTION ---
with st.expander("ℹ️ About This Page", expanded=True):
    st.markdown("""
    This application provides a comprehensive overview of New York City Police Department (NYPD) operations, 
    visualized across three main dashboards.
    
    * **Dispatch Activity:** Displays live metrics on service calls (CIP vs. Non-CIP), 
        call types, and borough distribution. This data is fetched live from the `SERVICE_CALLS` view.
    * **Force Dashboard:** Shows live data on use-of-force incidents, including monthly trends, 
        types of force used, and the basis for the encounter. This data comes from the `USE_OF_FORCE` view.
    * **CompStat 2.0:** An interactive replica of the official CompStat report. Click on any 
        crime row (e.g., "Murder", "Robbery") to populate the map and trend charts with (static) sample data.
    
    **Data Source:** Live data for the 'Dispatch' and 'Force' tabs is fetched from Snowflake 
    and cached for 1 hour to ensure performance.
    """)
st.markdown("---") # Add a separator
# --- END MODIFICATION ---

tab_dispatch, tab_force, tab_compstat = st.tabs(["Dispatch Activity", "Force Dashboard", "CompStat 2.0"])

# --- Custom CSS for CompStat Row Clickability ---
st.markdown("""
<style>
div.row-button button {
    background-color: transparent !important; border: none !important; padding: 0 !important; margin: 0 !important;
    text-align: left !important; width: 100%; height: 100%; color: transparent !important; position: absolute; z-index: 10;
}
div[data-testid*="stHorizontalBlock"] > div.compstat-row:hover {
    background-color: #33333315 !important; cursor: pointer !important;
}
.compstat-row { position: relative; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# --- TAB 1: DISPATCH ACTIVITY (Live Data) ---
# ------------------------------------------------------------------------------
with tab_dispatch:
    st.subheader("NYPD Dispatch Activity")
    col_metric_1, col_metric_2 = st.columns(2)
    col_metric_1.metric(label="Total Calls for Service (Last Year)", value=dispatch_data.get("total_calls", "N/A"))
    col_metric_2.metric(label="Critical & Serious Calls", value=dispatch_data.get("total_critical_serious", "N/A"))
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1: plot_cip_vs_non_cip(dispatch_data.get("df_cip"))
    with col2: plot_cip_calls_by_type(dispatch_data.get("df_calls"))
    with col3: plot_calls_by_borough(dispatch_data.get("df_borough"))

# ------------------------------------------------------------------------------
# --- TAB 2: FORCE DASHBOARD (Live Data) ---
# ------------------------------------------------------------------------------
with tab_force:
    st.subheader("NYPD Use of Force Incidents")
    st.metric(label="Total Incidents (Last Year)", value=force_data.get("total_incidents", "N/A"))
    st.markdown("---")
    col4, col5 = st.columns(2)
    with col4:
        plot_incidents_by_month(force_data.get("df_incidents_month"))
        plot_type_of_force(force_data.get("df_force_type"))
    with col5:
        plot_basis_for_encounter(force_data.get("df_basis"))

# ------------------------------------------------------------------------------
# --- TAB 3: COMPSTAT 2.0 (Static Data, Interactive) ---
# ------------------------------------------------------------------------------
with tab_compstat:
    col_menu, col_logo, col_title_img, col_sort = st.columns([2, 1, 6, 2])
    with col_menu: st.selectbox("Patrol Borough", ['Citywide'], label_visibility="collapsed")
    with col_title_img: st.markdown("<h1 style='text-align: center; color: #337ab7;'>NYPD CompStat 2.0</h1>", unsafe_allow_html=True)
    with col_sort:
        st.markdown("<div style='text-align: right;'>Sort:</div>", unsafe_allow_html=True)
        s1 = st.container()
        s1.selectbox("Sort", ['Patrol Borough'], label_visibility="collapsed", key='s1');
    st.markdown("---")

    col_compstat, col_map, col_charts = st.columns([4, 4, 3])
    with col_compstat:
        st.markdown("<h4>CompStat Book</h4>", unsafe_allow_html=True)
        h_cols = st.columns([2.5, 3.5, 3.5, 1])
        h_cols[1].markdown("<div style='text-align: center; font-weight: bold;'>Week of 10/06 - 10/12/25</div>", unsafe_allow_html=True)
        h_cols[2].markdown("<div style='text-align: center; font-weight: bold;'>28 Day</div>", unsafe_allow_html=True)
        sh_cols = st.columns([2.5, 1, 1, 1.5, 1, 1, 1.5, 1])
        sh_cols[1].markdown("<div style='text-align: right; font-weight: bold;'>2025</div>", unsafe_allow_html=True); sh_cols[2].markdown("<div style='text-align: right; font-weight: bold;'>2024</div>", unsafe_allow_html=True); sh_cols[3].markdown("<div style='text-align: right; font-weight: bold;'>% Chg</div>", unsafe_allow_html=True)
        sh_cols[4].markdown("<div style='text-align: right; font-weight: bold;'>2025</div>", unsafe_allow_html=True); sh_cols[5].markdown("<div style='text-align: right; font-weight: bold;'>2024</div>", unsafe_allow_html=True); sh_cols[6].markdown("<div style='text-align: right; font-weight: bold;'>% Chg</div>", unsafe_allow_html=True); sh_cols[7].markdown("<div style='text-align: right; font-weight: bold;'>YTD</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:0'>", unsafe_allow_html=True)

        for index, row in df_final_display.iterrows():
            crime_name = row['CompStat Book']
            with st.container():
                st.markdown('<div class="compstat-row">', unsafe_allow_html=True)
                with st.form(key=f"row_{index}"):
                    cols = st.columns([2.5, 1, 1, 1.5, 1, 1, 1.5, 1])
                    btn_cols = st.columns([6, 4])
                    with btn_cols[0]:
                        st.markdown('<div class="row-button">', unsafe_allow_html=True)
                        submitted = st.form_submit_button(f"select_{crime_name}", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    style = "font-size: 14px; color: inherit;"
                    cols[0].markdown(f"<div style='{style}'>{crime_name}</div>", unsafe_allow_html=True)
                    cols[1].markdown(f"<div style='text-align: right; {style}'>{row['Wk 2025']}</div>", unsafe_allow_html=True)
                    cols[2].markdown(f"<div style='text-align: right; {style}'>{row['Wk 2024']}</div>", unsafe_allow_html=True)
                    cols[3].markdown(f"<div style='text-align: right; {style}'>{row['Wk % Chg']}</div>", unsafe_allow_html=True)
                    cols[4].markdown(f"<div style='text-align: right; {style}'>{row['28D 2025']}</div>", unsafe_allow_html=True)
                    cols[5].markdown(f"<div style='text-align: right; {style}'>{row['28D 2024']}</div>", unsafe_allow_html=True)
                    cols[6].markdown(f"<div style='text-align: right; {style}'>{row['28D % Chg']}</div>", unsafe_allow_html=True)
                    cols[7].markdown(f"<div style='text-align: right; {style}'>{row['YTD Total']}</div>", unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)
                if submitted:
                    st.session_state.selected_crime = crime_name
                    st.rerun()
                st.markdown("<hr style='margin:0'>", unsafe_allow_html=True)
        st.caption("- All figures are preliminary and subject to further analysis...")

    with col_map:
        st.markdown("<h4>Incident Map</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            st.map(pd.DataFrame({'lat': [40.78], 'lon': [-73.96]}), zoom=10)
        else:
            st.markdown("<div style='height: 350px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)
    
    with col_charts:
        st.markdown("<h4>&nbsp;</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            plot_incident_bar_chart(st.session_state.selected_crime)
            plot_incident_line_chart(st.session_state.selected_crime)
        else:
            st.markdown("<div style='height: 300px; border: 1px solid #ccc; margin-bottom: 20px;'>[Select Metric]</div>", unsafe_allow_html=True)
            st.markdown("<div style='height: 300px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)