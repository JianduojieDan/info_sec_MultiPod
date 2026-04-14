import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import os
import plotly.express as px


st.set_page_config(page_title="Multi-Pod Security Center", layout="wide")

#backend api adress
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Multi-Pod Security Command Center")
st.markdown("---")

st.sidebar.header("Settings")
limit = st.sidebar.number_input("Reports Limit", min_value=1, max_value=1000, value=50)
request_timeout = st.sidebar.slider("Request Timeout (seconds)", min_value=1, max_value=15, value=5)
if st.sidebar.button("Manual Refresh"):
    st.rerun()


def request_json(url: str, fallback):
    try:
        res = requests.get(url, timeout=request_timeout)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        st.warning(f"Backend request failed: {e}")
        return fallback

# get statistics from backend api
def get_stats():
    return request_json(
        f"{BACKEND_URL}/stats",
        {
            "total_reports": 0,
            "critical_reports": 0,
            "critical_rate_percent": 0.0,
            "latest_timestamp": None,
        },
    )

# get detailed data from backend api
def fetch_data():
    return request_json(f"{BACKEND_URL}/get_latest_reports?limit={limit}", [])

# show statistics panel
stats = get_stats()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Reports", stats['total_reports'])
with col2:
    st.metric("Critical Alerts", stats['critical_reports'], delta_color="inverse")
with col3:
    data = fetch_data()
    active_nodes = len({r['hostname'] for r in data}) if data else 0
    st.metric("Active Nodes (Latest)", active_nodes)
with col4:
    st.metric("Last Sync", datetime.now().strftime("%H:%M:%S"), f"{stats['critical_rate_percent']}% Critical")

if not data:
    st.info("📡 No security reports found. Waiting for incoming data...")
else:
    # convert to DataFrame
    df_list = []
    for report in data:
        for item in report['items']:
            df_list.append({
                "Node Name": report['hostname'],
                "Event Time": report['timestamp'],
                "Risk Level": report['alert_level'],
                "Target Path": item['folder_path'],
                "Size (GB)": item['size_gb']
            })
    
    df = pd.DataFrame(df_list)

    # filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    node_filter = st.sidebar.multiselect("Select Nodes", options=df['Node Name'].unique())
    level_filter = st.sidebar.multiselect("Risk Levels", options=df['Risk Level'].unique())

    if node_filter:
        df = df[df['Node Name'].isin(node_filter)]
    if level_filter:
        df = df[df['Risk Level'].isin(level_filter)]

    if df.empty:
        st.info("No data matches the current filters. Please adjust Filters.")
        st.stop()

    # core data
    tab1, tab2 = st.tabs(["📊 Live Feed", "📈 Analytics"])
    
    with tab1:
        st.markdown("### Security Event Stream")
        def color_status(val):
            return 'color: red; font-weight: bold' if val == 'CRITICAL' else 'color: green'
        
        st.dataframe(
            df.style.map(color_status, subset=['Risk Level']),
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.markdown("### Threat Analysis")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # risk distribution
            fig_pie = px.pie(df, names='Risk Level', title='Alert Level Distribution', color='Risk Level',
                           color_discrete_map={'CRITICAL': 'red', 'NORMAL': 'green'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_c2:
            # node storage risk analysis
            fig_bar = px.bar(df, x='Node Name', y='Size (GB)', color='Risk Level', title='Node Storage Risk Analysis')
            st.plotly_chart(fig_bar, use_container_width=True)

st.caption(f"Backend URL: {BACKEND_URL}")
