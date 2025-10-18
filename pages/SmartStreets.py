import streamlit as st
import sys, os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from collections import Counter
import re

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.maps.directions import DirectionsAPI
from src.traffic.traffic_api import NYTrafficAPI
from src.ui.map_display import MapDisplay
from src.ui.components import RouteDisplay
from config.settings import Config

# 511NY API Key
API_KEY_511 = "fd7bd4600ee94588be5a28d448666112"

def get_severity_color(severity):
    """Return color based on severity level"""
    severity_map = {
        "Critical": "#dc2626",
        "Major": "#ea580c",
        "Moderate": "#f59e0b",
        "Minor": "#84cc16",
        "Unknown": "#6b7280"
    }
    return severity_map.get(severity, "#6b7280")

def get_severity_emoji(severity):
    """Return emoji based on severity level"""
    severity_map = {
        "Critical": "🔴",
        "Major": "🟠",
        "Moderate": "🟡",
        "Minor": "🟢",
        "Unknown": "⚪"
    }
    return severity_map.get(severity, "⚪")

def strip_html_tags(text):
    """Remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
 
def render_congestion_card(event, index):
    """Render a modern card for each congestion event"""
    severity = event.get("severity", "Unknown")
    color = get_severity_color(severity)
    emoji = get_severity_emoji(severity)
    
    # Build location string with light colors
    location_str = ""
    if event.get("latitude") and event.get("longitude"):
        location_str = f'<div style="margin-top: 0.75rem; font-size: 0.85rem; color: #d1d5db;">📍 Location: {event.get("latitude")}, {event.get("longitude")}</div>'
    
    # Single HTML block - all in one to avoid rendering issues
    # Using light colors for dark theme compatibility
    html = f'''
<div style="background: linear-gradient(135deg, {color}25 0%, {color}15 100%); border-left: 4px solid {color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
        <div style="flex: 1;">
            <div style="font-size: 0.85rem; color: #9ca3af; font-weight: 500; margin-bottom: 0.25rem;">#{index + 1} • CONGESTION ALERT</div>
            <h3 style="margin: 0; color: #f3f4f6; font-size: 1.25rem; font-weight: 700;">{emoji} {event.get("road", "Unknown Road")}</h3>
        </div>
        <div style="background-color: {color}; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{severity}</div>
    </div>
    <div style="color: #e5e7eb; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">{event.get("description", "No description available")}</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
        <div style="background-color: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.7rem; color: #9ca3af; font-weight: 600; margin-bottom: 0.25rem;">START TIME</div>
            <div style="font-size: 0.9rem; color: #f3f4f6; font-weight: 600;">⏰ {event.get("startTime", "N/A")}</div>
        </div>
        <div style="background-color: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.7rem; color: #9ca3af; font-weight: 600; margin-bottom: 0.25rem;">END TIME</div>
            <div style="font-size: 0.9rem; color: #f3f4f6; font-weight: 600;">⏱️ {event.get("endTime", "N/A")}</div>
        </div>
    </div>
    {location_str}
</div>
'''
    
    st.markdown(html, unsafe_allow_html=True)

def create_severity_chart(data):
    """Create a donut chart for severity distribution"""
    severity_counts = Counter([event.get("severity", "Unknown") for event in data])
    
    colors = {
        "Critical": "#dc2626",
        "Major": "#ea580c",
        "Moderate": "#f59e0b",
        "Minor": "#84cc16",
        "Unknown": "#6b7280"
    }
    
    df = pd.DataFrame({
        'Severity': list(severity_counts.keys()),
        'Count': list(severity_counts.values())
    })
    
    fig = go.Figure(data=[go.Pie(
        labels=df['Severity'],
        values=df['Count'],
        hole=0.4,
        marker=dict(colors=[colors.get(s, "#6b7280") for s in df['Severity']]),
        textinfo='label+percent',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text="<b>Severity Distribution</b>",
            font=dict(size=18, color='white'),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=12, color='white'),
            bgcolor='rgba(0,0,0,0.3)',
            bordercolor='white',
            borderwidth=1
        ),
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(t=60, b=30, l=20, r=150)
    )
    
    return fig

def create_event_type_chart(data):
    """Create a bar chart for event types"""
    event_counts = Counter([event.get("eventType", "Unknown") for event in data])
    
    df = pd.DataFrame({
        'Event Type': list(event_counts.keys()),
        'Count': list(event_counts.values())
    }).sort_values('Count', ascending=False).head(10)
    
    fig = px.bar(
        df,
        x='Event Type',
        y='Count',
        title='Top 10 Event Types',
        color='Count',
        color_continuous_scale='Viridis',
        text='Count'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(showgrid=False, color='white'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    return fig

def create_county_chart(data):
    """Create a horizontal bar chart for county distribution"""
    county_counts = Counter([event.get("county", "Unknown") for event in data if event.get("county")])
    
    df = pd.DataFrame({
        'County': list(county_counts.keys()),
        'Count': list(county_counts.values())
    }).sort_values('Count', ascending=True).tail(15)
    
    fig = px.bar(
        df,
        y='County',
        x='Count',
        orientation='h',
        title='Top 15 Counties by Traffic Events',
        color='Count',
        color_continuous_scale='Plasma',
        text='Count'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
        yaxis=dict(showgrid=False, color='white'),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    return fig

def create_severity_by_type_chart(data):
    """Create a stacked bar chart showing severity distribution by event type"""
    # Prepare data
    event_severity_data = []
    for event in data:
        event_severity_data.append({
            'Event Type': event.get('eventType', 'Unknown'),
            'Severity': event.get('severity', 'Unknown')
        })
    
    df = pd.DataFrame(event_severity_data)
    
    # Get top event types
    top_types = df['Event Type'].value_counts().head(8).index
    df_filtered = df[df['Event Type'].isin(top_types)]
    
    # Create pivot table
    pivot_df = df_filtered.groupby(['Event Type', 'Severity']).size().unstack(fill_value=0)
    
    colors_map = {
        "Critical": "#dc2626",
        "Major": "#ea580c",
        "Moderate": "#f59e0b",
        "Minor": "#84cc16",
        "Unknown": "#6b7280"
    }
    
    fig = go.Figure()
    
    for severity in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=severity,
            x=pivot_df.index,
            y=pivot_df[severity],
            marker_color=colors_map.get(severity, "#6b7280"),
            hovertemplate='<b>%{x}</b><br>%{y} events<extra></extra>'
        ))
    
    fig.update_layout(
        title='Severity Distribution by Event Type',
        barmode='stack',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(showgrid=False, color='white', tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white', title='Number of Events'),
        legend=dict(bgcolor='rgba(0,0,0,0.3)', bordercolor='white', borderwidth=1),
        margin=dict(t=50, b=100, l=50, r=20)
    )
    
    return fig

def create_summary_metrics(data):
    """Create summary statistics"""
    total_events = len(data)
    
    # Calculate average events per county
    counties = [e.get('county') for e in data if e.get('county')]
    unique_counties = len(set(counties))
    avg_per_county = total_events / unique_counties if unique_counties > 0 else 0
    
    # Most problematic event type
    event_types = Counter([e.get('eventType', 'Unknown') for e in data])
    top_event = event_types.most_common(1)[0] if event_types else ('Unknown', 0)
    
    # Severity breakdown percentages
    severities = Counter([e.get('severity', 'Unknown') for e in data])
    critical_pct = (severities.get('Critical', 0) / total_events * 100) if total_events > 0 else 0
    
    return {
        'total': total_events,
        'unique_counties': unique_counties,
        'avg_per_county': avg_per_county,
        'top_event': top_event,
        'critical_pct': critical_pct
    }

def main():
    st.set_page_config(page_title="Smart Streets | NYC Traffic", layout="wide", page_icon="🚦")

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #0e4d92 0%, #1e3a8a 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 2rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 800;">🚦 NYC Traffic Congestion Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95;">Real-time Congestion Monitoring • Live Traffic Events • Smart Analytics</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize components
    traffic_api = NYTrafficAPI(API_KEY_511)
    directions_api = DirectionsAPI()
    map_display = MapDisplay()

    # Sidebar Controls
    st.sidebar.markdown("### ⚙️ Dashboard Controls")
    refresh_btn = st.sidebar.button("🔄 Refresh Traffic Data", use_container_width=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Filters")
    
    # Fetch traffic data
    try:
        if refresh_btn or "congestion_data" not in st.session_state:
            with st.spinner("🔍 Fetching live congestion data..."):
                st.session_state["congestion_data"] = traffic_api.get_congestion_data()
                st.session_state["traffic_events"] = traffic_api.get_events()
        
        congestion_data = st.session_state.get("congestion_data", [])
        traffic_events = st.session_state.get("traffic_events", [])
        
        # Severity filter
        all_severities = list(set([event.get("severity", "Unknown") for event in congestion_data]))
        selected_severities = st.sidebar.multiselect(
            "Severity Level",
            options=all_severities,
            default=all_severities
        )
        
        # Limit results for performance
        max_results = st.sidebar.slider(
            "Max Results to Display",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            help="Limit the number of results to improve performance"
        )
        
        # Filter data
        filtered_data = [event for event in congestion_data if event.get("severity", "Unknown") in selected_severities]
        
        # Apply max results limit
        total_filtered = len(filtered_data)
        
        # Sort options
        sort_by = st.sidebar.selectbox(
            "Sort By",
            ["Severity (High to Low)", "Severity (Low to High)", "Road Name", "Start Time"]
        )
        
        # Apply sorting
        severity_order = {"Critical": 0, "Major": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
        if sort_by == "Severity (High to Low)":
            filtered_data.sort(key=lambda x: severity_order.get(x.get("severity", "Unknown"), 4))
        elif sort_by == "Severity (Low to High)":
            filtered_data.sort(key=lambda x: severity_order.get(x.get("severity", "Unknown"), 4), reverse=True)
        elif sort_by == "Road Name":
            filtered_data.sort(key=lambda x: x.get("road", ""))
        elif sort_by == "Start Time":
            filtered_data.sort(key=lambda x: x.get("startTime", ""))
        
        # Limit results after sorting
        filtered_data = filtered_data[:max_results]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Statistics")
        st.sidebar.metric("Total Congestion Spots", len(congestion_data))
        st.sidebar.metric("After Filters", total_filtered)
        st.sidebar.metric("Displaying", len(filtered_data))
        st.sidebar.metric("Total Traffic Events", len(traffic_events))
        
        # Main Dashboard
        # KPI Metrics
        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        critical_count = len([e for e in congestion_data if e.get("severity") == "Critical"])
        major_count = len([e for e in congestion_data if e.get("severity") == "Major"])
        moderate_count = len([e for e in congestion_data if e.get("severity") == "Moderate"])
        minor_count = len([e for e in congestion_data if e.get("severity") == "Minor"])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc262615 0%, #dc262605 100%); 
                        border-left: 4px solid #dc2626; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #dc2626;">{critical_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🔴 CRITICAL</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ea580c15 0%, #ea580c05 100%); 
                        border-left: 4px solid #ea580c; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #ea580c;">{major_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🟠 MAJOR</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f59e0b15 0%, #f59e0b05 100%); 
                        border-left: 4px solid #f59e0b; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #f59e0b;">{moderate_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🟡 MODERATE</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #84cc1615 0%, #84cc1605 100%); 
                        border-left: 4px solid #84cc16; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 800; color: #84cc16;">{minor_count}</div>
                <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600; margin-top: 0.5rem;">🟢 MINOR</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Calculate metrics before tabs (needed in multiple tabs)
        metrics = create_summary_metrics(congestion_data) if congestion_data else None
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Live Insights", "📊 Analytics Dashboard", "🗺️ Congestion Map", "📋 Congestion Hotspots", "🚨 Traffic Events"])
        
        with tab1:
            st.markdown("### 🎯 Live Traffic Insights")
            st.markdown("*Real-time traffic monitoring and event tracking*")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if congestion_data and metrics:
                # Top Row: Real-time Metrics
                metric_row1, metric_row2 = st.columns(2)
                
                with metric_row1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-size: 1.2rem;">🚗</span>
                                <span style="font-weight: 600; color: #f3f4f6;">Active Events</span>
                            </div>
                            <span style="color: #9ca3af; font-size: 0.85rem;">Last update: Now</span>
                        </div>
                        <div style="font-size: 3rem; font-weight: 800; color: #84cc16; margin-bottom: 0.5rem;">{len(congestion_data)}</div>
                        <div style="color: #d1d5db; font-size: 0.9rem;">Total traffic events</div>
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                            <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                                <span style="color: #d1d5db;">• Critical: <strong style="color: #dc2626;">{critical_count}</strong></span>
                                <span style="color: #d1d5db;">• Major: <strong style="color: #ea580c;">{major_count}</strong></span>
                                <span style="color: #d1d5db;">• Minor: <strong style="color: #84cc16;">{minor_count}</strong></span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row2:
                    regions_count = len(set([e.get('region') for e in congestion_data if e.get('region')]))
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-size: 1.2rem;">📍</span>
                                <span style="font-weight: 600; color: #f3f4f6;">Coverage Area</span>
                            </div>
                            <span style="color: #9ca3af; font-size: 0.85rem;">Last update: Now</span>
                        </div>
                        <div style="font-size: 3rem; font-weight: 800; color: #3b82f6; margin-bottom: 0.5rem;">{metrics['unique_counties']}</div>
                        <div style="color: #d1d5db; font-size: 0.9rem;">Counties affected</div>
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                            <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                                <span style="color: #d1d5db;">• Regions: <strong style="color: #3b82f6;">{regions_count}</strong></span>
                                <span style="color: #d1d5db;">• Avg/County: <strong style="color: #8b5cf6;">{metrics['avg_per_county']:.0f}</strong></span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Event Details and Status Cards
                event_col, status_col = st.columns([1.2, 1])
                
                with event_col:
                    # Get most recent critical event
                    critical_events = [e for e in congestion_data if e.get('severity') == 'Critical']
                    recent_event = critical_events[0] if critical_events else congestion_data[0]
                    
                    severity = recent_event.get('severity', 'Unknown')
                    severity_color = get_severity_color(severity)
                    
                    # Emergency level bars - build properly
                    severity_level = {'Critical': 5, 'Major': 4, 'Moderate': 3, 'Minor': 2, 'Unknown': 1}.get(severity, 1)
                    
                    # Build bars inline
                    bar1_color = severity_color if 0 < severity_level else 'rgba(255,255,255,0.1)'
                    bar2_color = severity_color if 1 < severity_level else 'rgba(255,255,255,0.1)'
                    bar3_color = severity_color if 2 < severity_level else 'rgba(255,255,255,0.1)'
                    bar4_color = severity_color if 3 < severity_level else 'rgba(255,255,255,0.1)'
                    bar5_color = severity_color if 4 < severity_level else 'rgba(255,255,255,0.1)'
                    
                    st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;"><div style="display: flex; align-items: center; gap: 0.5rem;"><span style="font-size: 1.2rem;">⚠️</span><span style="font-weight: 600; color: #f3f4f6;">Latest Priority Event</span></div><span style="color: #9ca3af; font-size: 0.85rem;">Event ID: {recent_event.get('eventType', 'N/A')[:10]}</span></div><div style="font-size: 1.3rem; font-weight: 700; color: #f3f4f6; margin-bottom: 0.75rem;">{recent_event.get('eventType', 'Unknown').title()} Detected</div><div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;"><div style="width: 16%; height: 20px; background: {bar1_color}; margin-right: 2%; border-radius: 4px;"></div><div style="width: 16%; height: 20px; background: {bar2_color}; margin-right: 2%; border-radius: 4px;"></div><div style="width: 16%; height: 20px; background: {bar3_color}; margin-right: 2%; border-radius: 4px;"></div><div style="width: 16%; height: 20px; background: {bar4_color}; margin-right: 2%; border-radius: 4px;"></div><div style="width: 16%; height: 20px; background: {bar5_color}; border-radius: 4px;"></div></div><div style="font-size: 0.85rem; color: #d1d5db; margin-bottom: 0.5rem;">Emergency Level: <strong style="color: {severity_color};">{severity}</strong></div><div style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">{strip_html_tags(recent_event.get('description', 'No description available'))}</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.85rem; color: #d1d5db;"><div>• <strong>Location:</strong> {recent_event.get('county', 'Unknown')}</div><div>• <strong>Road:</strong> {recent_event.get('road', 'N/A')[:30]}</div><div>• <strong>Started:</strong> {recent_event.get('startTime', 'N/A')[:10]}</div><div>• <strong>Region:</strong> {recent_event.get('region', 'N/A')[:20]}</div></div></div>""", unsafe_allow_html=True)
                
                with status_col:
                    # Department/System Status - build all HTML at once inline
                    st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;"><div style="display: flex; align-items: center; gap: 0.5rem;"><span style="font-size: 1.2rem;">🔔</span><span style="font-weight: 600; color: #f3f4f6;">System Status</span></div></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><span style="color: #e5e7eb; font-size: 0.9rem;">Traffic Monitoring</span><span style="background: #10b98130; color: #10b981; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">Active</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><span style="color: #e5e7eb; font-size: 0.9rem;">Data Collection</span><span style="background: #10b98130; color: #10b981; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">Active</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><span style="color: #e5e7eb; font-size: 0.9rem;">Alert System</span><span style="background: #10b98130; color: #10b981; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">Active</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><span style="color: #e5e7eb; font-size: 0.9rem;">API Connection</span><span style="background: #10b98130; color: #10b981; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">Connected</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><span style="color: #e5e7eb; font-size: 0.9rem;">Map Services</span><span style="background: #10b98130; color: #10b981; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">Online</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><span style="color: #e5e7eb; font-size: 0.9rem;">Analytics Engine</span><span style="background: #f59e0b30; color: #f59e0b; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">Processing</span></div></div>""", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Key Metrics Grid
                st.markdown("### 📊 Key Metrics")
                st.markdown("<div style='font-size: 0.9rem; color: #6b7280; margin-bottom: 1rem;'>Last 24 Hours Overview</div>", unsafe_allow_html=True)
                
                key_col1, key_col2, key_col3 = st.columns(3)
                
                event_types = Counter([e.get('eventType', 'Unknown') for e in congestion_data])
                top_3_events = event_types.most_common(3)
                
                with key_col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 10px; padding: 1.25rem; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                            <div style="background: rgba(59, 130, 246, 0.2); padding: 0.75rem; border-radius: 8px;">
                                <span style="font-size: 1.5rem; color: #3b82f6;">🚧</span>
                            </div>
                            <div>
                                <div style="color: #9ca3af; font-size: 0.8rem;">Roadwork Events</div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #f3f4f6;">{event_types.get('roadwork', 0)}</div>
                            </div>
                        </div>
                        <div style="color: #9ca3af; font-size: 0.75rem;">/ Last 24 Hrs</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with key_col2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 10px; padding: 1.25rem; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                            <div style="background: rgba(239, 68, 68, 0.2); padding: 0.75rem; border-radius: 8px;">
                                <span style="font-size: 1.5rem; color: #ef4444;">🚨</span>
                            </div>
                            <div>
                                <div style="color: #9ca3af; font-size: 0.8rem;">Critical Events</div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #f3f4f6;">{critical_count}</div>
                            </div>
                        </div>
                        <div style="color: #9ca3af; font-size: 0.75rem;">/ Requires Attention</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with key_col3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 10px; padding: 1.25rem; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                            <div style="background: rgba(16, 185, 129, 0.2); padding: 0.75rem; border-radius: 8px;">
                                <span style="font-size: 1.5rem; color: #10b981;">📍</span>
                            </div>
                            <div>
                                <div style="color: #9ca3af; font-size: 0.8rem;">Active Regions</div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #f3f4f6;">{regions_count}</div>
                            </div>
                        </div>
                        <div style="color: #9ca3af; font-size: 0.75rem;">/ Across NY State</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No live data available.")
        
        with tab2:
            st.markdown("### 📊 Traffic Analytics Dashboard")
            st.markdown("*Comprehensive visual analysis of traffic events across New York State*")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if congestion_data:
                # Row 1: Severity Distribution and Event Types
                col1, col2 = st.columns(2)
                
                with col1:
                    severity_fig = create_severity_chart(congestion_data)
                    st.plotly_chart(severity_fig, use_container_width=True)
                
                with col2:
                    event_type_fig = create_event_type_chart(congestion_data)
                    st.plotly_chart(event_type_fig, use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Row 2: Severity by Type and County Distribution
                col3, col4 = st.columns(2)
                
                with col3:
                    severity_by_type_fig = create_severity_by_type_chart(congestion_data)
                    st.plotly_chart(severity_by_type_fig, use_container_width=True)
                
                with col4:
                    county_fig = create_county_chart(congestion_data)
                    st.plotly_chart(county_fig, use_container_width=True)
                
                # Additional Insights
                st.markdown("---")
                st.markdown("### 🔍 Key Insights")
                
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    most_common_type = Counter([e.get('eventType', 'Unknown') for e in congestion_data]).most_common(1)[0]
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #3b82f615 0%, #3b82f605 100%); 
                                border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 8px;">
                        <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.5rem;">MOST COMMON EVENT</div>
                        <div style="font-size: 1.5rem; color: #f3f4f6; font-weight: 700;">{most_common_type[0]}</div>
                        <div style="font-size: 0.9rem; color: #d1d5db; margin-top: 0.25rem;">{most_common_type[1]} occurrences</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with insight_col2:
                    most_affected_county = Counter([e.get('county', 'Unknown') for e in congestion_data if e.get('county')]).most_common(1)
                    if most_affected_county:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #8b5cf615 0%, #8b5cf605 100%); 
                                    border-left: 4px solid #8b5cf6; padding: 1rem; border-radius: 8px;">
                            <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.5rem;">MOST AFFECTED COUNTY</div>
                            <div style="font-size: 1.5rem; color: #f3f4f6; font-weight: 700;">{most_affected_county[0][0]}</div>
                            <div style="font-size: 0.9rem; color: #d1d5db; margin-top: 0.25rem;">{most_affected_county[0][1]} events</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with insight_col3:
                    high_severity = len([e for e in congestion_data if e.get('severity') in ['Critical', 'Major']])
                    severity_pct = (high_severity / len(congestion_data) * 100) if congestion_data else 0
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ef444415 0%, #ef444405 100%); 
                                border-left: 4px solid #ef4444; padding: 1rem; border-radius: 8px;">
                        <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.5rem;">HIGH SEVERITY EVENTS</div>
                        <div style="font-size: 1.5rem; color: #f3f4f6; font-weight: 700;">{high_severity}</div>
                        <div style="font-size: 0.9rem; color: #d1d5db; margin-top: 0.25rem;">{severity_pct:.1f}% of total</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No data available for analytics.")
        
        with tab3:
            st.markdown("### 🗺️ Live Congestion Map")
            if congestion_data:
                center_location = {"lat": 40.7128, "lng": -74.0060}
                map_display.render_traffic_overlay_map(center_location)
            else:
                st.info("No congestion data available to display on map.")
        
        with tab4:
            st.markdown("### 📋 Active Congestion Hotspots")
            
            # Filter for congestion-specific events (construction, roadwork)
            congestion_types = ['roadwork', 'construction', 'road_closure', 'lane_closure']
            congestion_filtered = [e for e in filtered_data if e.get('eventType', '').lower() in congestion_types]
            
            if congestion_filtered:
                st.markdown(f"**Showing {len(congestion_filtered)} congestion hotspots (roadwork, construction, closures)**")
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Render cards
                for idx, event in enumerate(congestion_filtered):
                    render_congestion_card(event, idx)
            else:
                st.info("🎉 No congestion hotspots found. These include roadwork, construction, and road closures.")
        
        with tab5:
            st.markdown("### 🚨 All Traffic Events & Incidents")
            
            # Filter for incident-related events (accidents, incidents, weather, etc.)
            # Show everything that's NOT roadwork/construction
            congestion_types = ['roadwork', 'construction', 'road_closure', 'lane_closure']
            incidents_filtered = [e for e in traffic_events if e.get('eventType', '').lower() not in congestion_types]
            
            if incidents_filtered:
                # Limit traffic events too
                limited_events = incidents_filtered[:max_results]
                
                if len(incidents_filtered) > len(limited_events):
                    st.info(f"ℹ️ Showing top {len(limited_events)} of {len(incidents_filtered)} traffic incidents. Adjust the 'Max Results' slider to see more.")
                else:
                    st.markdown(f"**{len(incidents_filtered)} active traffic incidents (accidents, weather, special events)**")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                for idx, event in enumerate(limited_events):
                    render_congestion_card(event, idx)
            else:
                st.info("✅ No active traffic incidents at this time.")
        
        # Route Planning Section
        st.markdown("---")
        st.markdown("### 🚗 Route Planning")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start = st.text_input("🟢 Start Address", "Times Square, NYC")
        with col2:
            end = st.text_input("🔴 Destination", "Central Park, NYC")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            route_btn = st.button("🚦 Get Route", use_container_width=True)
        
        if route_btn:
            try:
                with st.spinner("🔍 Finding optimal route..."):
                    routes_data = directions_api.get_routes(start, end)
                    st.session_state["routes_data"] = routes_data
            except Exception as e:
                st.error(f"❌ Error fetching route: {e}")
        
        # Routes section
        if "routes_data" in st.session_state:
            st.markdown("### 🗺️ Route Visualization")
            routes_data = st.session_state["routes_data"]
            
            map_display.render_route_map(routes_data)
            RouteDisplay.render_route_comparison(routes_data)
            
            if len(routes_data.get("routes", [])) > 1:
                best = routes_data["best_route"]
                alternate = routes_data["routes"][1]
                time_diff = (alternate["duration_in_traffic"]["value"] - best["duration_in_traffic"]["value"]) / 60
                
                st.info(f"💡 **Alternate Route Insight:** The alternate route may take **{time_diff:.1f} minutes** longer due to current traffic conditions.")
    
    except Exception as e:
        st.error(f"❌ Unable to fetch traffic data: {e}")
        st.info("Please try refreshing the page or check your API connection.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#888; padding: 1rem;">
        <strong>NYC Smart Streets Dashboard</strong> | Powered by 511NY & Google Maps | Auto-refresh every 5 minutes<br>
        <small>Data updated in real-time from NYC traffic monitoring systems</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
