# Save this file as app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import pydeck as pdk
import re # Added for the parse_geom function from previous scripts, though not used here, good practice.

# Make sure your utils.py file is in the same directory
from utils import get_city_guard_data_by_view, get_emergency_contacts 

# --- Configuration ---
st.set_page_config(layout="wide", page_title="City Guard & Urban SOS")
if 'selected_crime' not in st.session_state:
    st.session_state.selected_crime = None

# ==============================================================================
#                 1. DATA LOADING & PROCESSING (Definitions)
# ==============================================================================

@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_all_data():
    """Loads and processes all data from Snowflake using the specific view function."""
    
    # Dispatch views (pre-aggregated in Snowflake)
    df_totals = get_city_guard_data_by_view("SERVICE_CALLS_TOTALS")
    df_cip_breakdown = get_city_guard_data_by_view("SERVICE_CALLS_CIP_BREAKDOWN")
    df_calls_by_type = get_city_guard_data_by_view("SERVICE_CALLS_BY_TYPE")
    df_calls_by_type_non_cip = get_city_guard_data_by_view("SERVICE_CALLS_BY_TYPE_NON_CIP")
    df_calls_by_borough = get_city_guard_data_by_view("SERVICE_CALLS_BY_BOROUGH")
    df_calls_by_borough_cip = get_city_guard_data_by_view("SERVICE_CALLS_BY_BOROUGH_CIP")
    df_calls_by_borough_non_cip = get_city_guard_data_by_view("SERVICE_CALLS_BY_BOROUGH_NON_CIP")

    # Force incidents (raw view still okay)
    df_use_of_force = get_city_guard_data_by_view("USE_OF_FORCE")
    # Service calls (for map) - fetch and trim client-side to recent 10k
    df_service_calls = get_city_guard_data_by_view("SERVICE_CALLS")
    
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
            processed_data["dispatch"]["total_calls_raw"] = total_calls_val
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

    # Calls by Type (Non-CIP)
    if df_calls_by_type_non_cip is not None and not df_calls_by_type_non_cip.empty:
        df_calls_by_type_non_cip.columns = [c.upper() for c in df_calls_by_type_non_cip.columns]
        cat_col = next((c for c in df_calls_by_type_non_cip.columns if c in ['CATEGORY','TYPE','CIP_JOBS']), None)
        calls_col = next((c for c in df_calls_by_type_non_cip.columns if c in ['CALLS','COUNT','CNT','TOTAL']), None)
        df_norm = df_calls_by_type_non_cip.copy()
        if cat_col: df_norm = df_norm.rename(columns={cat_col: 'Category'})
        if calls_col: df_norm = df_norm.rename(columns={calls_col: 'Calls'})
        processed_data["dispatch"]["df_calls_non_cip"] = df_norm[["Category","Calls"]]

    # Calls by Borough
    if df_calls_by_borough is not None and not df_calls_by_borough.empty:
        df_calls_by_borough.columns = [c.upper() for c in df_calls_by_borough.columns]
        b_col = next((c for c in df_calls_by_borough.columns if c in ['BOROUGH','BORO_NM','BORO']), None)
        pct_col = next((c for c in df_calls_by_borough.columns if c in ['PERCENTAGE','PCT','PERCENT']), None)
        cnt_col = next((c for c in df_calls_by_borough.columns if c in ['COUNT','CNT','TOTAL']), None)
        df_norm = df_calls_by_borough.copy()
        if b_col: df_norm = df_norm.rename(columns={b_col: 'Borough'})
        if pct_col:
            df_norm = df_norm.rename(columns={pct_col: 'Percentage'})
        elif cnt_col:
            # Compute percentage from counts
            total_cnt = pd.to_numeric(df_norm[cnt_col], errors='coerce').sum()
            if total_cnt and total_cnt > 0:
                df_norm['Percentage'] = (pd.to_numeric(df_norm[cnt_col], errors='coerce') / total_cnt * 100).round(2)
        processed_data["dispatch"]["df_borough"] = df_norm[["Borough","Percentage"]]

    # Calls by Borough (CIP-only)
    if df_calls_by_borough_cip is not None and not df_calls_by_borough_cip.empty:
        df_calls_by_borough_cip.columns = [c.upper() for c in df_calls_by_borough_cip.columns]
        b_col = next((c for c in df_calls_by_borough_cip.columns if c in ['BOROUGH','BORO_NM','BORO']), None)
        pct_col = next((c for c in df_calls_by_borough_cip.columns if c in ['PERCENTAGE','PCT','PERCENT']), None)
        cnt_col = next((c for c in df_calls_by_borough_cip.columns if c in ['COUNT','CNT','TOTAL']), None)
        df_norm = df_calls_by_borough_cip.copy()
        if b_col: df_norm = df_norm.rename(columns={b_col: 'Borough'})
        if pct_col:
            df_norm = df_norm.rename(columns={pct_col: 'Percentage'})
        elif cnt_col:
            total_cnt = pd.to_numeric(df_norm[cnt_col], errors='coerce').sum()
            if total_cnt and total_cnt > 0:
                df_norm['Percentage'] = (pd.to_numeric(df_norm[cnt_col], errors='coerce') / total_cnt * 100).round(2)
        processed_data["dispatch"]["df_borough_cip"] = df_norm[["Borough","Percentage"]]

    # Calls by Borough (Non-CIP)
    if df_calls_by_borough_non_cip is not None and not df_calls_by_borough_non_cip.empty:
        df_calls_by_borough_non_cip.columns = [c.upper() for c in df_calls_by_borough_non_cip.columns]
        b_col = next((c for c in df_calls_by_borough_non_cip.columns if c in ['BOROUGH','BORO_NM','BORO']), None)
        pct_col = next((c for c in df_calls_by_borough_non_cip.columns if c in ['PERCENTAGE','PCT','PERCENT']), None)
        cnt_col = next((c for c in df_calls_by_borough_non_cip.columns if c in ['COUNT','CNT','TOTAL']), None)
        df_norm = df_calls_by_borough_non_cip.copy()
        if b_col: df_norm = df_norm.rename(columns={b_col: 'Borough'})
        if pct_col:
            df_norm = df_norm.rename(columns={pct_col: 'Percentage'})
        elif cnt_col:
            total_cnt = pd.to_numeric(df_norm[cnt_col], errors='coerce').sum()
            if total_cnt and total_cnt > 0:
                df_norm['Percentage'] = (pd.to_numeric(df_norm[cnt_col], errors='coerce') / total_cnt * 100).round(2)
        processed_data["dispatch"]["df_borough_non_cip"] = df_norm[["Borough","Percentage"]]
    
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

    # --- Prepare data for Dispatch Map ---
    if df_service_calls is not None and not df_service_calls.empty:
        df_sc = df_service_calls.copy()
        df_sc.columns = [c.upper() for c in df_sc.columns]
        # Ensure required columns
        req_cols = ['LATITUDE','LONGITUDE','CIP_JOBS','TYP_DESC','RADIO_CODE','BORO_NM','CREATE_DATE','CAD_EVNT_ID']
        missing = [c for c in req_cols if c not in df_sc.columns]
        if not missing:
            # Clean coordinates
            df_sc = df_sc[pd.to_numeric(df_sc['LATITUDE'], errors='coerce').notna() & pd.to_numeric(df_sc['LONGITUDE'], errors='coerce').notna()]
            df_sc['LATITUDE'] = df_sc['LATITUDE'].astype(float)
            df_sc['LONGITUDE'] = df_sc['LONGITUDE'].astype(float)
            df_sc = df_sc[(df_sc['LATITUDE'].between(40.3, 41.0)) & (df_sc['LONGITUDE'].between(-74.3, -73.5))]
            # Sort recent and cap to 10k
            try:
                df_sc['CREATE_DATE_PARSED'] = pd.to_datetime(df_sc['CREATE_DATE'])
            except Exception:
                df_sc['CREATE_DATE_PARSED'] = pd.to_datetime(df_sc['CREATE_DATE'], errors='coerce')
            df_sc = df_sc.sort_values('CREATE_DATE_PARSED', ascending=False).head(10000).reset_index(drop=True)
            # Rename for pydeck
            df_sc = df_sc.rename(columns={'LATITUDE':'lat','LONGITUDE':'lon','CIP_JOBS':'CIP','TYP_DESC':'TYPE','RADIO_CODE':'CODE','BORO_NM':'BOROUGH','CREATE_DATE':'CREATE_TS','CAD_EVNT_ID':'EVENT_ID'})
            processed_data['dispatch']['df_calls_map'] = df_sc[['lat','lon','CIP','TYPE','CODE','BOROUGH','CREATE_TS','EVENT_ID']]

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


# ==============================================================================
#                 CHART PLOTTING FUNCTIONS (Definitions)
# ==============================================================================

# --- Standard Plotly Config ---
PLOTLY_CONFIG = {
    'displayModeBar': True,   'displaylogo': False,   'scrollZoom': True,
}

def plot_cip_vs_non_cip(df):
    if df is None or df.empty:
        st.warning("CIP data not available.")
        return
    # ... (rest of function unchanged)
    has_count = 'Count' in df.columns
    colors = ['#10b981', '#f59e0b', '#6b7280']  # CIP, Non CIP, Unknown
    fig = px.pie(
        df, values='Percentage', names='Type',
        title='CIP vs Non CIP Calls For Service',
        color='Type',
        color_discrete_map={'CIP': colors[0], 'Non CIP': colors[1]},
        hole=0.6
    )
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
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_dispatch_map(df, filter_choice: str):
    if df is None or df.empty:
        st.warning("Service calls map data not available.")
        return
    df_map = df.copy()
    if filter_choice == 'CIP':
        df_map = df_map[df_map['CIP'].str.upper().isin(['CRITICAL','SERIOUS','NON CRITICAL'])]
    elif filter_choice == 'Non CIP':
        df_map = df_map[df_map['CIP'].str.upper() == 'NON CIP']
    if df_map.empty:
        st.info("No calls to display for this filter.")
        return
    
    color_map = {
        'CRITICAL': [239, 68, 68],     # red
        'SERIOUS': [245, 158, 11],     # amber
        'NON CRITICAL': [16, 185, 129], # emerald
        'NON CIP': [99, 102, 241]       # indigo
    }
    def _get_color(row):
        key = str(row.get('CIP','')).upper()
        return color_map.get(key, [107,114,128])
    df_map = df_map.assign(color=df_map.apply(_get_color, axis=1))
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=45,
        pickable=True,
        opacity=0.6,
    )
    # Initialize view from session (persisted across reruns)
    mv = st.session_state.get('map_view', { 'lat': 40.7128, 'lon': -74.0060, 'zoom': 9.5 })
    view_state = pdk.ViewState(latitude=mv.get('lat', 40.7128), longitude=mv.get('lon', -74.0060), zoom=mv.get('zoom', 9.5), min_zoom=8, max_zoom=16)
    tooltip = {
        "html": """
            <div>
              <b>Event:</b> {EVENT_ID}<br/>
              <b>Created:</b> {CREATE_TS}<br/>
              <b>Radio Code:</b> {CODE}<br/>
              <b>Type:</b> {TYPE}<br/>
              <b>Borough:</b> {BOROUGH}<br/>
              <b>Call Class:</b> {CIP}
            </div>
        """,
        "style": {"backgroundColor": "#111827", "color": "white"}
    }
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style=None)
    st.pydeck_chart(r, use_container_width=True)

def plot_cip_calls_by_type(df):
    if df is None or df.empty:
        st.warning("CIP calls by type data not available.")
        return
    # ... (rest of function unchanged)
    if 'Category' not in df.columns or 'Calls' not in df.columns:
        st.warning("Type data missing expected columns.")
        return
    df_work = df.copy()
    df_work['Calls'] = pd.to_numeric(df_work['Calls'], errors='coerce').fillna(0).astype(int)
    df_sorted = df_work.sort_values('Calls', ascending=True).reset_index(drop=True)
    fig = px.bar(
        df_sorted, y='Category', x='Calls', orientation='h',
        title='Calls by Type', color_discrete_sequence=['#2563eb']
    )
    fig.update_traces(text=df_sorted['Calls'].map(lambda v: f"{int(v):,}"), textposition='outside', cliponaxis=False)
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=60, b=10), xaxis=dict(showgrid=True, gridcolor='#eef2f7'), yaxis=dict(title=None), template='plotly_white')
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_calls_by_borough(df):
    if df is None or df.empty:
        st.warning("Borough data not available.")
        return
    # ... (rest of function unchanged)
    df_sorted = df.sort_values('Percentage', ascending=False)
    fig = px.pie(
        df_sorted, values='Percentage', names='Borough',
        title='Calls by Borough', hole=.6, color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(t=60, b=10, l=10, r=10), height=360)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_incidents_by_month(df):
    if df is None or df.empty:
        st.warning("Monthly incident data not available.")
        return
    # ... (rest of function unchanged)
    fig = px.bar(df, x='Month', y='Incidents', title='Incidents by Month', color_discrete_sequence=['#2563eb'])
    fig.update_xaxes(categoryorder='array', categoryarray=df['Month'].tolist())
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_type_of_force(df):
    if df is None or df.empty:
        st.warning("Use of force type data not available.")
        return
    # ... (rest of function unchanged)
    df_sorted = df.sort_values('Percentage', ascending=False).reset_index(drop=True)
    fig = px.bar(
        df_sorted, y='Type', x='Percentage', orientation='h', title='Type of Force',
        color_discrete_sequence=['#10b981']
    )
    fig.update_yaxes(categoryorder='array', categoryarray=df_sorted['Type'].tolist())
    fig.update_traces(text=df_sorted['Percentage'].map(lambda v: f"{v:.1f}%"), textposition='outside', cliponaxis=False)
    max_val = float(df_sorted['Percentage'].max()) if not df_sorted.empty else 100
    fig.update_layout(template='plotly_white', xaxis=dict(title='Percentage', ticksuffix='%', range=[0, max_val * 1.15]), yaxis_title=None, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_basis_for_encounter(df):
    if df is None or df.empty:
        st.warning("Basis for encounter data not available.")
        return
    # ... (rest of function unchanged)
    df_sorted = df.sort_values('Percentage', ascending=True).reset_index(drop=True)
    fig = px.bar(
        df_sorted, y='Basis', x='Percentage', orientation='h', title='Basis for Encounter',
        color_discrete_sequence=['#2563eb']
    )
    fig.update_yaxes(categoryorder='array', categoryarray=df_sorted['Basis'].tolist())
    fig.update_traces(text=df_sorted['Percentage'].map(lambda v: f"{v:.1f}%"), textposition='outside', cliponaxis=False)
    max_val = float(df_sorted['Percentage'].max()) if not df_sorted.empty else 100
    fig.update_layout(template='plotly_white', xaxis=dict(title='Percentage', ticksuffix='%', range=[0, max_val * 1.15]), yaxis_title=None, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_rank_treemap(df):
    if df is None or df.empty:
        st.warning("Rank data not available.")
        return
    # ... (rest of function unchanged)
    fig = px.treemap(df, path=['Rank'], values='Count', title='Members of Service by Rank', color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textinfo='label+value')
    fig.update_layout(margin=dict(l=0, r=0, t=60, b=0), template='plotly_white')
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_race_donut(df):
    if df is None or df.empty:
        st.warning("Race data not available.")
        return
    # ... (rest of function unchanged)
    fig = px.pie(df, names='Race', values='Percentage', hole=0.6, title='Incidents by Race', color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_incident_bar_chart(crime_name):
    df = pd.DataFrame({'Borough': ['PBBN', 'PBBS', 'PBBX', 'PBSI'], 'Incidents': [1, 1, 2, 1]})
    fig = px.bar(df, x='Borough', y='Incidents', title=f'Patrol Borough - Week to Date<br>{crime_name}', color_discrete_sequence=['#2563eb'])
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def plot_incident_line_chart(crime_name):
    df = pd.DataFrame({'Date': pd.to_datetime(['10/06/25', '10/07/25', '10/08/25', '10/09/25', '10/10/25', '10/11/25', '10/12/25']), 'Value': [1.5, 1.2, 0.8, 0.5, 1.0, 0.9, 1.1]})
    fig = px.line(df, x='Date', y='Value', title=f'Timeline - Week to Date<br>{crime_name}', markers=True, color_discrete_sequence=['#ef4444'])
    fig.update_layout(template='plotly_white', margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


# ==============================================================================
#                 3. STATIC UI & PLACEHOLDER SETUP
# ==============================================================================
st.title("City Scope 360 Dashboard")
st.markdown("""This is just a prototype for New York City.""")

st.title("NYPD Dashboards")

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

tab_dispatch, tab_force, tab_compstat, tab_emergency_contacts = st.tabs(["Dispatch Activity", "Force Dashboard", "CompStat 2.0", "Emergency Contacts"])

# --- Custom CSS for CompStat Row Clickability ---
st.markdown("""
<style>
/* ... (your CSS is unchanged) ... */
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# --- TAB 1: DISPATCH ACTIVITY (Placeholders) ---
# ------------------------------------------------------------------------------
with tab_dispatch:
    st.subheader("NYPD Dispatch Activity (Jan-Jun 2025)")

    # Master filter is a UI element, so it's rendered immediately
    filter_choice = st.selectbox("Filter display by call types:", ["All", "CIP", "Non CIP"], index=0, key="dispatch_filter_select")

    # Metric placeholders
    col_metric_1, col_metric_2 = st.columns(2)
    ph_metric_1 = col_metric_1.empty()
    ph_metric_2 = col_metric_2.empty()
    ph_metric_1.info("Loading total calls...")
    ph_metric_2.info("Loading critical calls...")
    st.markdown("---")

    # Chart placeholders
    col1, col2, col3 = st.columns([1, 1.2, 1])
    ph_chart_cip = col1.empty()
    ph_chart_calls = col2.empty()
    ph_chart_borough = col3.empty()
    ph_chart_cip.info("Loading CIP breakdown...")
    ph_chart_calls.info("Loading calls by type...")
    ph_chart_borough.info("Loading calls by borough...")

    # Map & Glossary placeholders
    st.markdown("---")
    c_map, c_gloss = st.columns([2, 1])
    with c_map:
        st.subheader("Service Calls Map (most recent 10,000)")
        # ... (Your static map legend HTML/CSS is fine here) ...
        legend_css = """<style> ... </style>""" # (shortened for brevity)
        legend_html = """<div class="map-legend"> ... </div>""" # (shortened for brevity)
        st.markdown(legend_css + legend_html, unsafe_allow_html=True)
        
        ph_dispatch_map = st.empty()
        ph_dispatch_map.info("Loading map data...")
        
    with c_gloss:
        st.subheader("Reference")
        with st.expander("📘 Glossary: About Call Types", expanded=True):
            glossary_css_inline = """
            <style>
              .glossary-card-inline { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px 18px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.06); overflow: hidden; box-sizing: border-box; max-width: 100%; }
              .glossary-card-inline h4 { margin: 0 0 8px 0; font-size: 1rem; color: #111827; }
              .glossary-card-inline p, .glossary-card-inline ul { margin: 6px 0; color: #374151; }
              .glossary-card-inline ul { padding-left: 18px; list-style-position: outside; overflow-wrap: anywhere; }
              .glossary-card-inline li { margin: 4px 0; line-height: 1.35; }
              .glossary-card-inline a { word-break: break-word; }
              .legend { display: grid; grid-template-columns: 12px 1fr; align-items: start; row-gap: 6px; column-gap: 10px; margin: 10px 0 4px 0; }
              .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-top: 0; }
              .dot-critical { background: rgb(239,68,68); }
              .dot-serious { background: rgb(245,158,11); }
              .dot-noncritical { background: rgb(16,185,129); }
              .dot-noncip { background: rgb(99,102,241); }
              .glossary-footer-inline { margin-top: 8px; color: #6b7280; font-size: 0.85rem; }
              @media (prefers-color-scheme: dark) {
                .glossary-card-inline { background: #0b1220; border-color: #374151; box-shadow: 0 1px 3px rgba(0,0,0,0.5); }
                .glossary-card-inline h4 { color: #e5e7eb; }
                .glossary-card-inline p, .glossary-card-inline ul { color: #cbd5e1; }
                .glossary-footer-inline { color: #9ca3af; }
              }
            </style>
            """
            glossary_html_inline = """
            <div class="glossary-card-inline">
              <h4>About Call Types</h4>
              <p>This dashboard classifies NYPD Calls for Service into two broad groups:</p>
              <p><strong>Crime in Progress (CIP)</strong> calls include incidents flagged as:</p>
              <div class="legend">
                <span class="dot dot-critical"></span><span><strong>Critical</strong> – Immediate danger to life or property (e.g., shots fired, armed robbery)</span>
                <span class="dot dot-serious"></span><span><strong>Serious</strong> – Significant public safety concerns (e.g., assault in progress, burglary)</span>
                <span class="dot dot-noncritical"></span><span><strong>Non Critical</strong> – Lower-priority in-progress events (e.g., trespassing, disorderly group)</span>
              </div>
              <p><strong>NON CIP</strong> calls are routine or administrative in nature. These include:</p>
              <ul>
                <li>Noise complaints</li>
                <li>Vehicle accidents</li>
                <li>Welfare checks</li>
                <li>Public assistance or non-urgent reports</li>
              </ul>
              <div class="glossary-footer-inline">
                <div>Dashboard created by <strong>Brendan Lambert</strong></div>
                <div>All data was obtained from <a href="https://data.cityofnewyork.us/Public-Safety/NYPD-Calls-for-Service-Year-to-Date-/n2zq-pubd/about_data" target="_blank">NYC Open Data – NYPD Calls for Service</a></div>
              </div>
            </div>
            """
            st.markdown(glossary_css_inline + glossary_html_inline, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# --- TAB 2: FORCE DASHBOARD (Placeholders) ---
# ------------------------------------------------------------------------------
with tab_force:
    st.subheader("NYPD Use of Force Incidents (Jan-Jun 2025)")
    
    # Metric placeholders
    col_metric_1_f, col_metric_2_f = st.columns(2)
    ph_force_metric_1 = col_metric_1_f.empty()
    ph_force_metric_2 = col_metric_2_f.empty()
    ph_force_metric_1.info("Loading total incidents...")
    ph_force_metric_2.info("Loading members of service...")
    st.markdown("---")

    # Chart placeholders
    r1c1, r1c2 = st.columns(2)
    ph_force_r1c1 = r1c1.empty()
    ph_force_r1c2 = r1c2.empty()
    ph_force_r1c1.info("Loading monthly incidents...")
    ph_force_r1c2.info("Loading race data...")
    st.markdown("---")
    
    r2c1, r2c2 = st.columns(2)
    ph_force_r2c1 = r2c1.empty()
    ph_force_r2c2 = r2c2.empty()
    ph_force_r2c1.info("Loading force types...")
    ph_force_r2c2.info("Loading encounter basis...")
    st.markdown("---")
    
    ph_force_treemap = st.empty()
    ph_force_treemap.info("Loading rank data...")

# ------------------------------------------------------------------------------
# --- TAB 3: COMPSTAT 2.0 (Static + Placeholders) ---
# ------------------------------------------------------------------------------
with tab_compstat:
    # This UI is static or depends on pre-defined data (df_final_display)
    col_menu, col_logo, col_title_img, col_sort = st.columns([2, 1, 6, 2])
    with col_menu: st.selectbox("Patrol Borough", ['Citywide'], label_visibility="collapsed")
    with col_title_img: st.markdown("<h1 style='text-align: center; color: #337ab7;'>NYPD CompStat 2.0</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Data editor uses static df_final_display, so it renders immediately
    with st.container():
        st.markdown("<h4>CompStat Book</h4>", unsafe_allow_html=True)
        if not st.session_state.selected_crime:
            st.session_state.selected_crime = df_final_display['CompStat Book'].iloc[0]
        # ... (All your column header markdown) ...
        h_cols = st.columns([2.5, 3.5, 3.5, 1]); h_cols[1].markdown("..."); h_cols[2].markdown("...")
        sh_cols = st.columns([2.5, 1, 1, 1.5, 1, 1, 1.5, 1]); sh_cols[1].markdown("..."); # (shortened)
        st.markdown("<hr style='margin:0'>", unsafe_allow_html=True)
        
        # ... (Your st.data_editor logic is unchanged) ...
        order_crimes = df_final_display['CompStat Book'].tolist()
        display_df = df_final_display.set_index('CompStat Book').loc[order_crimes].reset_index()
        display_df.insert(0, 'Select', display_df['CompStat Book'] == st.session_state.selected_crime)
        prev_selected = st.session_state.selected_crime
        edited_df = st.data_editor(
            display_df, width='stretch', hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(required=False),
                # ... (all other configs) ...
            },
            disabled=["CompStat Book", "Wk 2025", "Wk 2024", "Wk % Chg", "28D 2025", "28D 2024", "28D % Chg", "YTD Total"],
            key="compstat_table_editor"
        )
        # ... (Your selection logic for rerun is unchanged) ...
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
        
        st.caption("- All figures are preliminary and subject to further analysis...")

    # Placeholders for the charts *below* the table
    st.markdown("---")
    c_map, c_bar, c_line = st.columns([1, 1, 1])
    ph_compstat_map = c_map.empty()
    ph_compstat_bar = c_bar.empty()
    ph_compstat_line = c_line.empty()
    
    # Pre-fill placeholders based on selection (which is static)
    with ph_compstat_map.container():
        st.markdown("<h4>Incident Map</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            st.map(pd.DataFrame({'lat': [40.78], 'lon': [-73.96]}), zoom=10)
        else:
            st.markdown("<div style='height: 350px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)

    with ph_compstat_bar.container():
        st.markdown("<h4>Bar</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            plot_incident_bar_chart(st.session_state.selected_crime)
        else:
            st.markdown("<div style='height: 300px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)

    with ph_compstat_line.container():
        st.markdown("<h4>Timeline</h4>", unsafe_allow_html=True)
        if st.session_state.selected_crime:
            plot_incident_line_chart(st.session_state.selected_crime)
        else:
            st.markdown("<div style='height: 300px; border: 1px solid #ccc;'>[Select Metric]</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# --- TAB 4: EMERGENCY CONTACTS (Placeholders) ---
# ------------------------------------------------------------------------------
with tab_emergency_contacts:
    st.subheader("Emergency Contacts")
    ph_contacts_table = st.empty()
    ph_contacts_table.info("Loading emergency contacts...")


# ==============================================================================
#                 4. DATA FETCHING (The blocking call)
# ==============================================================================

# This runs AFTER all placeholders are drawn
all_data = load_all_data()
dispatch_data = all_data.get("dispatch", {})
force_data = all_data.get("force", {})

# Load contacts data
contacts = get_emergency_contacts()

# Persist map data and view state in session
if 'df_calls_map' not in st.session_state and dispatch_data.get('df_calls_map') is not None:
    st.session_state['df_calls_map'] = dispatch_data.get('df_calls_map')
if 'map_view' not in st.session_state:
    st.session_state['map_view'] = { 'lat': 40.7128, 'lon': -74.0060, 'zoom': 9.5 }


# ==============================================================================
#                 5. POPULATE PLACEHOLDERS
# ==============================================================================

# --- Populate TAB 1 ---
# Recalculate display data based on filter_choice (which is already set)
total_calls_val = dispatch_data.get("total_calls")
total_crit_ser_val = dispatch_data.get("total_critical_serious")
df_cip_meta = dispatch_data.get("df_cip")

if isinstance(df_cip_meta, pd.DataFrame) and not df_cip_meta.empty and 'Type' in df_cip_meta.columns:
    if 'Count' in df_cip_meta.columns:
        try:
            cip_count = int(df_cip_meta.loc[df_cip_meta['Type'].str.upper() == 'CIP', 'Count'].iloc[0])
        except Exception:
            cip_count = None
        try:
            non_count = int(df_cip_meta.loc[df_cip_meta['Type'].str.upper() == 'NON CIP', 'Count'].iloc[0])
        except Exception:
            non_count = None
            
        if filter_choice == 'CIP' and cip_count is not None:
            total_calls_val = f"{cip_count:,}"
        elif filter_choice == 'Non CIP' and non_count is not None:
            total_calls_val = f"{non_count:,}"
            total_crit_ser_val = f"{0:,}"

# Fill metrics
ph_metric_1.metric(label="Total Calls for Service", value=total_calls_val or "N/A")
ph_metric_2.metric(label="Critical & Serious Calls", value=total_crit_ser_val or "N/A")

# Prepare dataframes for charts
donut_df = df_cip_meta
if filter_choice in ("CIP", "Non CIP") and isinstance(df_cip_meta, pd.DataFrame) and not df_cip_meta.empty:
    if filter_choice == "CIP":
        count_val = cip_count
        donut_df = pd.DataFrame([{ 'Type': 'CIP', 'Percentage': 100.0, **({'Count': count_val} if count_val is not None else {}) }])
    else:
        count_val = non_count
        donut_df = pd.DataFrame([{ 'Type': 'Non CIP', 'Percentage': 100.0, **({'Count': count_val} if count_val is not None else {}) }])

calls_df = dispatch_data.get("df_calls")
if filter_choice == 'Non CIP':
    calls_df = dispatch_data.get("df_calls_non_cip")

borough_df = dispatch_data.get("df_borough")
if filter_choice == 'CIP' and dispatch_data.get("df_borough_cip") is not None:
    borough_df = dispatch_data.get("df_borough_cip")
elif filter_choice == 'Non CIP' and dispatch_data.get("df_borough_non_cip") is not None:
    borough_df = dispatch_data.get("df_borough_non_cip")

# Fill charts
with ph_chart_cip.container():
    plot_cip_vs_non_cip(donut_df)
with ph_chart_calls.container():
    plot_cip_calls_by_type(calls_df)
with ph_chart_borough.container():
    plot_calls_by_borough(borough_df)

# Fill map
with ph_dispatch_map.container():
    plot_dispatch_map(st.session_state.get("df_calls_map", dispatch_data.get("df_calls_map")), filter_choice)


# --- Populate TAB 2 ---
ph_force_metric_1.metric(label="Total Incidents", value=force_data.get("total_incidents", "N/A"))
ph_force_metric_2.metric(label="Members of Service", value=force_data.get("row_count", "N/A"))

with ph_force_r1c1.container():
    plot_incidents_by_month(force_data.get("df_incidents_month"))
with ph_force_r1c2.container():
    plot_race_donut(force_data.get("df_race"))
with ph_force_r2c1.container():
    plot_type_of_force(force_data.get("df_force_type"))
with ph_force_r2c2.container():
    plot_basis_for_encounter(force_data.get("df_basis"))
with ph_force_treemap.container():
    plot_rank_treemap(force_data.get("df_rank_grouped"))


# --- Populate TAB 4 ---
if not contacts:
    contacts = [
        {"service": "Emergency (Police, Fire, Medical)", "phone": "911", "fax": "N/A - Voice call required"},
        # ... (rest of your fallback data) ...
        {"service": "ASPCA Animal Poison Control", "phone": "(888) 426-4435", "fax": "N/A - Voice call required"}
    ]

table_css = """<style> ... </style>""" # (shortened for brevity)

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
        <thead>...</thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>
""" # (shortened for brevity)

ph_contacts_table.markdown(table_html, unsafe_allow_html=True)