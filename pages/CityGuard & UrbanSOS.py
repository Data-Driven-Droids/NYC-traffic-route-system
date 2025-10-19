# Save this file as app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
# Make sure your utils.py file is in the same directory
from utils import get_city_guard_data_by_view, get_emergency_contacts 

# --- Configuration ---
st.set_page_config(layout="wide", page_title="City Guard & Urban SOS")
if 'selected_crime' not in st.session_state:
    st.session_state.selected_crime = None

# ==============================================================================
#                     1. DATA LOADING & PROCESSING
# ==============================================================================

@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_all_data():
    """Loads and processes all data from Snowflake using the specific view function."""
    
    # print("--- Loading fresh data from Snowflake... ---")
    # Dispatch views (pre-aggregated in Snowflake)
    df_totals = get_city_guard_data_by_view("SERVICE_CALLS_TOTALS")
    df_cip_breakdown = get_city_guard_data_by_view("SERVICE_CALLS_CIP_BREAKDOWN")
    df_calls_by_type = get_city_guard_data_by_view("SERVICE_CALLS_BY_TYPE")
    df_calls_by_borough = get_city_guard_data_by_view("SERVICE_CALLS_BY_BOROUGH")

    # Force incidents (raw view still okay)
    df_use_of_force = get_city_guard_data_by_view("USE_OF_FORCE")
    
    processed_data = {
        "dispatch": {},
        "force": {}
    }

    # --- Process Data for Tab 1: Dispatch Activity (using pre-aggregated views) ---
    # Totals
    if df_totals is not None and not df_totals.empty:
        cols = [c.upper() for c in df_totals.columns]
        df_totals.columns = cols
        total_calls_val = None
        critical_serious_val = None
        # Flexible extraction
        for key in ['TOTAL_CALLS', 'TOTAL', 'COUNT', 'TOTAL_COUNT']:
            if key in cols:
                try:
                    total_calls_val = int(df_totals.iloc[0][key])
                    break
                except Exception:
                    pass
        for key in ['TOTAL_CRITICAL_SERIOUS', 'CRITICAL_SERIOUS', 'CRITICAL_SERIOUS_COUNT']:
            if key in cols:
                try:
                    critical_serious_val = int(df_totals.iloc[0][key])
                    break
                except Exception:
                    pass
        if total_calls_val is not None:
            processed_data["dispatch"]["total_calls"] = f"{total_calls_val:,}"
        if critical_serious_val is not None:
            processed_data["dispatch"]["total_critical_serious"] = f"{critical_serious_val:,}"

    # CIP vs Non CIP breakdown
    if df_cip_breakdown is not None and not df_cip_breakdown.empty:
        df_cip_breakdown.columns = [c.upper() for c in df_cip_breakdown.columns]
        # Try to normalize to Type, Count, Percentage
        type_col = next((c for c in df_cip_breakdown.columns if c in ['TYPE','CATEGORY']), None)
        count_col = next((c for c in df_cip_breakdown.columns if c in ['COUNT','CNT','TOTAL']), None)
        pct_col = next((c for c in df_cip_breakdown.columns if c in ['PERCENTAGE','PCT','PERCENT']), None)
        df_norm = df_cip_breakdown.copy()
        if type_col: df_norm = df_norm.rename(columns={type_col: 'Type'})
        if count_col: df_norm = df_norm.rename(columns={count_col: 'Count'})
        if pct_col: df_norm = df_norm.rename(columns={pct_col: 'Percentage'})
        keep_cols = [c for c in ['Type','Count','Percentage'] if c in df_norm.columns]
        processed_data["dispatch"]["df_cip"] = df_norm[keep_cols]

    # Calls by Type
    if df_calls_by_type is not None and not df_calls_by_type.empty:
        df_calls_by_type.columns = [c.upper() for c in df_calls_by_type.columns]
        cat_col = next((c for c in df_calls_by_type.columns if c in ['CATEGORY','TYPE','CIP_JOBS']), None)
        calls_col = next((c for c in df_calls_by_type.columns if c in ['CALLS','COUNT','CNT','TOTAL']), None)
        df_norm = df_calls_by_type.copy()
        if cat_col: df_norm = df_norm.rename(columns={cat_col: 'Category'})
        if calls_col: df_norm = df_norm.rename(columns={calls_col: 'Calls'})
        processed_data["dispatch"]["df_calls"] = df_norm[["Category","Calls"]]

    # Calls by Borough
    if df_calls_by_borough is not None and not df_calls_by_borough.empty:
        df_calls_by_borough.columns = [c.upper() for c in df_calls_by_borough.columns]
        b_col = next((c for c in df_calls_by_borough.columns if c in ['BOROUGH','BORO_NM','BORO']), None)
        pct_col = next((c for c in df_calls_by_borough.columns if c in ['PERCENTAGE','PCT','PERCENT']), None)
        df_norm = df_calls_by_borough.copy()
        if b_col: df_norm = df_norm.rename(columns={b_col: 'Borough'})
        if pct_col: df_norm = df_norm.rename(columns={pct_col: 'Percentage'})
        processed_data["dispatch"]["df_borough"] = df_norm[["Borough","Percentage"]]
    
    # --- Process Data for Tab 2: Force Dashboard ---
    if df_use_of_force is not None and not df_use_of_force.empty:
        df_use_of_force.columns = [col.upper() for col in df_use_of_force.columns]
        processed_data["force"]["total_incidents"] = f"{df_use_of_force['TRI_INCIDENT_NUMBER'].nunique():,}"
        
        df_incidents_month = df_use_of_force.groupby('YEARMONTHSHORT')['TRI_INCIDENT_NUMBER'].nunique().reset_index()
        df_incidents_month.columns = ['Month', 'Incidents']
        # Ensure chronological sorting for labels like '2025 APR', '2025 FEB', etc.
        month_parsed = pd.to_datetime(df_incidents_month['Month'].astype(str).str.title(), format='%Y %b', errors='coerce')
        df_incidents_month['MonthParsed'] = month_parsed
        df_incidents_month = df_incidents_month.sort_values('MonthParsed')
        # Standardize month label to 'YYYY Mon'
        df_incidents_month['Month'] = df_incidents_month['MonthParsed'].dt.strftime('%Y %b')
        df_incidents_month = df_incidents_month.drop(columns=['MonthParsed']).reset_index(drop=True)
        processed_data["force"]["df_incidents_month"] = df_incidents_month
        
        processed_data["force"]["df_force_type"] = df_use_of_force['FORCETYPE'].value_counts(normalize=True).mul(100).rename_axis('Type').reset_index(name='Percentage')
        processed_data["force"]["df_basis"] = df_use_of_force['BASISFORENCOUNTER'].value_counts(normalize=True).mul(100).rename_axis('Basis').reset_index(name='Percentage')
        processed_data["force"]["row_count"] = f"{len(df_use_of_force):,}"
        processed_data["force"]["df_rank_grouped"] = (
            df_use_of_force['RANK_GROUPED']
            .fillna('Unknown')
            .value_counts()
            .rename_axis('Rank')
            .reset_index(name='Count')
        )
        processed_data["force"]["df_race"] = (
            df_use_of_force['RACE']
            .fillna('Unknown')
            .value_counts(normalize=True)
            .mul(100)
            .rename_axis('Race')
            .reset_index(name='Percentage')
        )

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
df_final_display = df_final_display[df_final_display["CompStat Book"] != "Total"].reset_index(drop=True)


# Load the live data
all_data = load_all_data()
dispatch_data = all_data.get("dispatch", {})
force_data = all_data.get("force", {})


# ==============================================================================
#                     CHART PLOTTING FUNCTIONS
# ==============================================================================

# --- Standard Plotly Config ---
# This dictionary holds Plotly-specific configuration options.
# The warning about "keyword arguments" refers to passing these options
# directly to st.plotly_chart (e.g., st.plotly_chart(fig, displayModeBar=False)).
# The correct way is to pass them inside this 'config' dictionary.
# The 'width' argument is a Streamlit argument, not a Plotly config, so it stays separate.
PLOTLY_CONFIG = {
    'displayModeBar': True,  # Show the mode bar (zoom, pan, etc.)
    'displaylogo': False,    # Hide the Plotly logo
    'scrollZoom': True,      # Allow zooming with the mouse wheel
    'width': 'stretch'
}

def plot_cip_vs_non_cip(df):
    if df is None or df.empty:
        return st.warning("CIP data not available.")
    # Ensure expected columns
    has_count = 'Count' in df.columns
    colors = ['#10b981', '#f59e0b', '#6b7280']  # CIP, Non CIP, Unknown
    fig = px.pie(
        df, values='Percentage', names='Type',
        title='CIP vs Non CIP Calls For Service',
        color='Type',
        color_discrete_map={'CIP': colors[0], 'Non CIP': colors[1]},
        hole=0.6
    )
    # Add better labels and hover
    if has_count:
        fig.update_traces(
            textposition='inside', textinfo='percent+label',
            customdata=df[['Count']],
            hovertemplate='%{label}: %{value:.2f}%<br>Count: %{customdata[0]:,}'
        )
    else:
        fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5),
        margin=dict(t=60, b=10, l=10, r=10),
        height=360
    )
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_cip_calls_by_type(df):
    if df is None or df.empty:
        return st.warning("Call type data not available.")
    df_sorted = df.sort_values('Calls', ascending=True).reset_index(drop=True)
    fig_height = 360
    fig = px.bar(
        df_sorted, y='Category', x='Calls', orientation='h',
        title='CIP Calls by Type', color_discrete_sequence=['#2563eb']
    )
    fig.update_traces(
        text=df_sorted['Calls'].map(lambda v: f"{int(v):,}"), textposition='outside', cliponaxis=False
    )
    fig.update_layout(height=fig_height, margin=dict(l=10, r=10, t=60, b=10), xaxis=dict(showgrid=True, gridcolor='#eef2f7'), yaxis=dict(title=None))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_calls_by_borough(df):
    if df is None or df.empty:
        return st.warning("Borough data not available.")
    df_sorted = df.sort_values('Percentage', ascending=False)
    fig = px.pie(
        df_sorted, values='Percentage', names='Borough',
        title='Calls by Borough', hole=.6, color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(t=60, b=10, l=10, r=10), height=360)
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_incidents_by_month(df):
    if df is None or df.empty:
        return st.warning("Monthly incident data not available.")
    fig = px.bar(df, x='Month', y='Incidents', title='Incidents by Month', color_discrete_sequence=['#2563eb'])
    fig.update_xaxes(categoryorder='array', categoryarray=df['Month'].tolist())
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_type_of_force(df):
    if df is None or df.empty:
        return st.warning("Use of force type data not available.")
    df_sorted = df.sort_values('Percentage', ascending=False).reset_index(drop=True)
    fig = px.bar(
        df_sorted, y='Type', x='Percentage', orientation='h', title='Type of Force',
        color_discrete_sequence=['#10b981']
    )
    fig.update_yaxes(categoryorder='array', categoryarray=df_sorted['Type'].tolist())
    fig.update_traces(text=df_sorted['Percentage'].map(lambda v: f"{v:.1f}%"), textposition='outside', cliponaxis=False)
    max_val = float(df_sorted['Percentage'].max()) if not df_sorted.empty else 100
    fig.update_layout(template='plotly_white', xaxis=dict(title='Percentage', ticksuffix='%', range=[0, max_val * 1.15]), yaxis_title=None, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_basis_for_encounter(df):
    if df is None or df.empty:
        return st.warning("Basis for encounter data not available.")
    df_sorted = df.sort_values('Percentage', ascending=True).reset_index(drop=True)
    fig = px.bar(
        df_sorted, y='Basis', x='Percentage', orientation='h', title='Basis for Encounter',
        color_discrete_sequence=['#2563eb']
    )
    fig.update_yaxes(categoryorder='array', categoryarray=df_sorted['Basis'].tolist())
    fig.update_traces(text=df_sorted['Percentage'].map(lambda v: f"{v:.1f}%"), textposition='outside', cliponaxis=False)
    max_val = float(df_sorted['Percentage'].max()) if not df_sorted.empty else 100
    fig.update_layout(template='plotly_white', xaxis=dict(title='Percentage', ticksuffix='%', range=[0, max_val * 1.15]), yaxis_title=None, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_rank_treemap(df):
    if df is None or df.empty:
        return st.warning("Rank data not available.")
    fig = px.treemap(df, path=['Rank'], values='Count', title='Members of Service by Rank', color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textinfo='label+value')
    fig.update_layout(margin=dict(l=0, r=0, t=60, b=0), template='plotly_white')
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_race_donut(df):
    if df is None or df.empty:
        return st.warning("Race data not available.")
    fig = px.pie(df, names='Race', values='Percentage', hole=0.6, title='Incidents by Race', color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_incident_bar_chart(crime_name):
    df = pd.DataFrame({'Borough': ['PBBN', 'PBBS', 'PBBX', 'PBSI'], 'Incidents': [1, 1, 2, 1]})
    fig = px.bar(df, x='Borough', y='Incidents', title=f'Patrol Borough - Week to Date<br>{crime_name}', color_discrete_sequence=['#2563eb'])
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED

def plot_incident_line_chart(crime_name):
    df = pd.DataFrame({'Date': pd.to_datetime(['10/06/25', '10/07/25', '10/08/25', '10/09/25', '10/10/25', '10/11/25', '10/12/25']), 'Value': [1.5, 1.2, 0.8, 0.5, 1.0, 0.9, 1.1]})
    fig = px.line(df, x='Date', y='Value', title=f'Timeline - Week to Date<br>{crime_name}', markers=True, color_discrete_sequence=['#ef4444'])
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, config=PLOTLY_CONFIG) # <-- MODIFIED


# ==============================================================================
#                     STREAMLIT APPLICATION LAYOUT
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

tab_dispatch, tab_force, tab_compstat, tab_emergency_contacts = st.tabs(["Dispatch Activity", "Force Dashboard", "CompStat 2.0", "Emergency Contacts"])

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
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col1:
        plot_cip_vs_non_cip(dispatch_data.get("df_cip"))
    with col2:
        plot_cip_calls_by_type(dispatch_data.get("df_calls"))
    with col3:
        plot_calls_by_borough(dispatch_data.get("df_borough"))

# ------------------------------------------------------------------------------
# --- TAB 2: FORCE DASHBOARD (Live Data) ---
# ------------------------------------------------------------------------------
with tab_force:
    st.subheader("NYPD Use of Force Incidents (2025)")
    col_metric_1, col_metric_2 = st.columns(2)
    col_metric_1.metric(label="Total Incidents", value=force_data.get("total_incidents", "N/A"))
    col_metric_2.metric(label="Members of Service", value=force_data.get("row_count", "N/A"))
    st.markdown("---")
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        plot_incidents_by_month(force_data.get("df_incidents_month"))
    with r1c2:
        plot_race_donut(force_data.get("df_race"))

    st.markdown("---")
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        plot_type_of_force(force_data.get("df_force_type"))
    with r2c2:
        plot_basis_for_encounter(force_data.get("df_basis"))

    st.markdown("---")
    plot_rank_treemap(force_data.get("df_rank_grouped"))

# ------------------------------------------------------------------------------
# --- TAB 3: COMPSTAT 2.0 (Static Data, Interactive) ---
# ------------------------------------------------------------------------------
with tab_compstat:
    col_menu, col_logo, col_title_img, col_sort = st.columns([2, 1, 6, 2])
    with col_menu: st.selectbox("Patrol Borough", ['Citywide'], label_visibility="collapsed")
    with col_title_img: st.markdown("<h1 style='text-align: center; color: #337ab7;'>NYPD CompStat 2.0</h1>", unsafe_allow_html=True)
    with col_sort:
        st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown("---")

    # Row 1: Full-width CompStat table with row selection
    with st.container():
        st.markdown("<h4>CompStat Book</h4>", unsafe_allow_html=True)
        if not st.session_state.selected_crime:
            st.session_state.selected_crime = df_final_display['CompStat Book'].iloc[0]
        h_cols = st.columns([2.5, 3.5, 3.5, 1])
        h_cols[1].markdown("<div style='text-align: center; font-weight: bold;'>Week of 10/06 - 10/12/25</div>", unsafe_allow_html=True)
        h_cols[2].markdown("<div style='text-align: center; font-weight: bold;'>28 Day</div>", unsafe_allow_html=True)
        sh_cols = st.columns([2.5, 1, 1, 1.5, 1, 1, 1.5, 1])
        sh_cols[1].markdown("<div style='text-align: right; font-weight: bold;'>2025</div>", unsafe_allow_html=True); sh_cols[2].markdown("<div style='text-align: right; font-weight: bold;'>2024</div>", unsafe_allow_html=True); sh_cols[3].markdown("<div style='text-align: right; font-weight: bold;'>% Chg</div>", unsafe_allow_html=True)
        sh_cols[4].markdown("<div style='text-align: right; font-weight: bold;'>2025</div>", unsafe_allow_html=True); sh_cols[5].markdown("<div style='text-align: right; font-weight: bold;'>2024</div>", unsafe_allow_html=True); sh_cols[6].markdown("<div style='text-align: right; font-weight: bold;'>% Chg</div>", unsafe_allow_html=True); sh_cols[7].markdown("<div style='text-align: right; font-weight: bold;'>YTD</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:0'>", unsafe_allow_html=True)
        order_crimes = df_final_display['CompStat Book'].tolist()
        display_df = df_final_display.set_index('CompStat Book').loc[order_crimes].reset_index()
        display_df.insert(0, 'Select', display_df['CompStat Book'] == st.session_state.selected_crime)
        prev_selected = st.session_state.selected_crime
        edited_df = st.data_editor(
            display_df,
            width='stretch',
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(required=False),
                "CompStat Book": st.column_config.TextColumn(disabled=True),
                "Wk 2025": st.column_config.TextColumn(disabled=True),
                "Wk 2024": st.column_config.TextColumn(disabled=True),
                "Wk % Chg": st.column_config.TextColumn(disabled=True),
                "28D 2025": st.column_config.TextColumn(disabled=True),
                "28D 2024": st.column_config.TextColumn(disabled=True),
                "28D % Chg": st.column_config.TextColumn(disabled=True),
                "YTD Total": st.column_config.TextColumn(disabled=True),
            },
            disabled=["CompStat Book", "Wk 2025", "Wk 2024", "Wk % Chg", "28D 2025", "28D 2024", "28D % Chg", "YTD Total"],
            key="compstat_table_editor"
        )
        selected_rows = edited_df[edited_df['Select']]
        if len(selected_rows) > 1:
            first_choice = selected_rows.iloc[0]['CompStat Book']
            if first_choice != prev_selected:
                st.session_state.selected_crime = first_choice
                st.rerun()
        elif len(selected_rows) == 1:
            new_selected = selected_rows.iloc[0]['CompStat Book']
            if new_selected != prev_selected:
                st.session_state.selected_crime = new_selected
                st.rerun()
        else:
            pass
        st.caption("- All figures are preliminary and subject to further analysis...")

    # Row 2: Three visuals in a single row (Map, Bar, Line)
    st.markdown("---")
    c_map, c_bar, c_line = st.columns([1, 1, 1])
    with c_map:
        st.markdown("<h4>Incident Map</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            st.map(pd.DataFrame({'lat': [40.78], 'lon': [-73.96]}), zoom=10)
        else:
            st.markdown("<div style='height: 350px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)

    with c_bar:
        st.markdown("<h4>Bar</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            plot_incident_bar_chart(st.session_state.selected_crime)
        else:
            st.markdown("<div style='height: 300px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)

    with c_line:
        st.markdown("<h4>Timeline</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            plot_incident_line_chart(st.session_state.selected_crime)
        else:
            st.markdown("<div style='height: 300px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# --- TAB 4: EMERGENCY CONTACTS ---
# ------------------------------------------------------------------------------
with tab_emergency_contacts:
    st.subheader("Emergency Contacts")
    contacts = get_emergency_contacts()
    if not contacts:
        contacts = [
            {"service": "Emergency (Police, Fire, Medical)", "phone": "911", "fax": "N/A - Voice call required"},
            {"service": "Suicide & Crisis Lifeline", "phone": "988", "fax": "N/A - Voice call/text required"},
            {"service": "Poison Control (National)", "phone": "(800) 222-1222", "fax": "N/A - Voice call required"},
            {"service": "City Services & Information", "phone": "311", "fax": "N/A - Use website or phone"},
            {"service": "NYPD General Non-Emergency", "phone": "(646) 610-5000", "fax": "(646) 610-5324 (Admin only)"},
            {"service": "FDNY General Non-Emergency", "phone": "(718) 999-2000", "fax": "(718) 999-0679 (Admin only)"},
            {"service": "NYC Domestic Violence Hotline", "phone": "(800) 621-4673", "fax": "N/A - Voice call required"},
            {"service": "Con Edison (Gas/Electric Emergency)", "phone": "(800) 752-6633", "fax": "N/A - Voice call required"},
            {"service": "National Grid (Gas Emergency)", "phone": "(718) 643-4050", "fax": "N/A - Voice call required"},
            {"service": "ASPCA Animal Poison Control", "phone": "(888) 426-4435", "fax": "N/A - Voice call required"}
        ]

    table_css = """
    <style>
    .contacts-table { width: 100%; border-collapse: separate; border-spacing: 0; }
    .contacts-table th, .contacts-table td { padding: 10px 12px; }
    .contacts-table th { background: #f5f7fb; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb; color: #111827; }
    .contacts-table tr { background: #ffffff; color: #111827; }
    .contacts-table tr:nth-child(even) { background: #fafafb; }
    .contacts-table td { border-bottom: 1px solid #f0f2f5; }
    .contacts-wrapper { border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .contacts-table a { color: #2563eb; text-decoration: none; }
    .contacts-table a:hover { text-decoration: underline; }

    @media (prefers-color-scheme: dark) {
      .contacts-table th { background: #111827; border-bottom: 1px solid #374151; color: #e5e7eb; }
      .contacts-table tr { background: #0b1220; color: #e5e7eb; }
      .contacts-table tr:nth-child(even) { background: #0e1626; }
      .contacts-table td { border-bottom: 1px solid #1f2937; }
      .contacts-wrapper { border: 1px solid #374151; box-shadow: 0 1px 3px rgba(0,0,0,0.6); }
      .contacts-table a { color: #93c5fd; }
      .contacts-table a:hover { color: #bfdbfe; }
    }
    </style>
    """

    def _safe_tel(phone: str) -> str:
        return phone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')

    rows_html = "".join([
        f"<tr><td>{c.get('service','')}</td>"
        f"<td><a href='tel:{_safe_tel(str(c.get('phone','')))}'>{c.get('phone','')}</a></td>"
        f"<td>{c.get('fax','')}</td></tr>" for c in contacts
    ])

    table_html = f"""
    {table_css}
    <div class='contacts-wrapper'>
      <table class='contacts-table'>
        <thead>
          <tr>
            <th>Service</th>
            <th>Phone</th>
            <th>Fax</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)