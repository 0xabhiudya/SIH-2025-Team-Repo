import streamlit as st
import pandas as pd
import tempfile
import os
import nest_asyncio
import altair as alt
import ipaddress
from detector import AttackDetector

# Apply nest_asyncio for Scapy compatibility
nest_asyncio.apply()

# --- 1. Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="ENIGMA: UBAD",
    page_icon="🛡️"
)

# --- 2. Caching & Helper Functions ---

@st.cache_data(show_spinner=False)
def run_analysis(uploaded_file):
    with st.spinner(f"ENIGMA is analyzing packets from `{uploaded_file.name}`... This may take a moment."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcapng") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        try:
            detector = AttackDetector()
            results_df, packet_count = detector.analyze_pcap(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)
    if not results_df.empty and 'Timestamp' in results_df.columns:
        results_df['Timestamp'] = pd.to_datetime(results_df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    return results_df, packet_count

@st.cache_data
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def convert_df_to_json(df: pd.DataFrame) -> bytes:
    return df.to_json(orient='records', indent=4).encode('utf-8')

def filter_by_ip(df: pd.DataFrame, ip_filter: str) -> pd.DataFrame:
    if not ip_filter: return df
    try:
        if '/' in ip_filter:
            target_network = ipaddress.ip_network(ip_filter, strict=False)
            ip_column = pd.to_numeric(df['SourceIP'].apply(lambda ip: ipaddress.ip_address(ip)), errors='coerce')
            return df[ip_column.between(int(target_network.network_address), int(target_network.broadcast_address))]
        elif '-' in ip_filter:
            start_ip_str, end_ip_str = ip_filter.split('-')
            start_ip = int(ipaddress.ip_address(start_ip_str.strip()))
            end_ip = int(ipaddress.ip_address(end_ip_str.strip()))
            ip_column = pd.to_numeric(df['SourceIP'].apply(lambda ip: ipaddress.ip_address(ip)), errors='coerce')
            return df[ip_column.between(start_ip, end_ip)]
        else:
            target_ip = ipaddress.ip_address(ip_filter.strip())
            return df[df['SourceIP'] == str(target_ip)]
    except ValueError:
        st.sidebar.warning("Invalid IP or range format.")
        return df

# --- 3. UI Rendering Functions ---

def display_sidebar(df: pd.DataFrame) -> tuple:
    st.sidebar.title("🔬 Analysis & Filters")
    if st.sidebar.button("Start New Analysis", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.sidebar.header("Filter Detections")
    status_options = ["All", "Successful", "Attempted", "Brute Force Detected"]
    status_filter = st.sidebar.radio("Filter by Status:", options=status_options, index=0, horizontal=True)
    attack_types = sorted(df['AttackType'].unique())
    selected_attacks = st.sidebar.multiselect("Filter by Attack Type:", options=attack_types, default=attack_types)
    source_ip_filter = st.sidebar.text_input("Filter by Source IP / Range:", placeholder="e.g., 192.168.1.0/24")
    return selected_attacks, source_ip_filter, status_filter

def display_metrics(df: pd.DataFrame, packet_count: int):
    st.subheader("Analysis Summary")
    successful_attacks = df[df['AttackStatus'] == 'Successful']
    brute_force_attacks = df[df['AttackStatus'] == 'Brute Force Detected']
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Packets Scanned", f"{packet_count:,}")
    with col2: st.metric("🚨 Total Detections", f"{len(df):,}")
    with col3: st.metric("✅ Successful Attacks", f"{len(successful_attacks):,}")
    with col4: st.metric("🔥 Brute Force Events", f"{len(brute_force_attacks):,}")

def display_dashboard(filtered_df: pd.DataFrame, packet_count: int):
    st.header("📊 Analysis Results")
    tab1, tab2 = st.tabs(["📈 Dashboard", "📜 Detailed Logs"])
    with tab1:
        display_metrics(filtered_df, packet_count)
        st.subheader("Attack Type Distribution by Status")
        color_scale = alt.Scale(domain=['Successful', 'Attempted', 'Brute Force Detected'], range=['#28a745', '#ffc107', '#dc3545'])
        chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X('AttackType:N', title='Attack Type', sort='-y'),
            y=alt.Y('count():Q', title='Number of Detections'),
            color=alt.Color('AttackStatus:N', scale=color_scale),
            tooltip=['AttackType', 'AttackStatus', 'count()']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    with tab2:
        st.subheader("Detailed Attack Logs")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        st.subheader("Export Results")
        col1, col2 = st.columns(2)
        with col1:
            csv_data = convert_df_to_csv(filtered_df)
            st.download_button("📥 Download as CSV", csv_data, "enigma_report.csv", "text/csv", key="download_csv", use_container_width=True)
        with col2:
            json_data = convert_df_to_json(filtered_df)
            st.download_button("📥 Download as JSON", json_data, "enigma_report.json", "application/json", key="download_json", use_container_width=True)

def display_welcome_page():
    st.title("🛡️ ENIGMA: URL Based Attack Detector (UBAD)")
    st.write("Welcome to **ENIGMA**! This tool analyzes network traffic to detect URL-based cyber attacks by correlating requests and responses.")
    with st.container(border=True):
        st.subheader("Get Started")
        uploaded_file = st.file_uploader("Upload a `.pcap` or `.pcapng` file", type=['pcap', 'pcapng'], label_visibility="collapsed")
        if uploaded_file:
            results_df, packet_count = run_analysis(uploaded_file)
            st.session_state['analysis_results'] = (results_df, packet_count)
            st.rerun()

# --- 4. Main Application ---
def main():
    if 'analysis_results' not in st.session_state:
        display_welcome_page()
    else:
        st.title("🛡️ ENIGMA Analysis Dashboard")
        df_results, packet_count = st.session_state['analysis_results']
        if df_results.empty:
            st.success("✅ Analysis complete. No URL-based attacks were detected.", icon="🎉")
            if st.button("Analyze Another File"): st.session_state.clear(); st.rerun()
            return

        selected_attacks, source_ip, status_filter = display_sidebar(df_results)
        
        filtered_df = df_results[df_results['AttackType'].isin(selected_attacks)]
        filtered_df = filter_by_ip(filtered_df, source_ip)
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['AttackStatus'] == status_filter]
        
        if filtered_df.empty:
            st.warning("No data matches the current filter criteria.", icon="⚠️")
        else:
            display_dashboard(filtered_df, packet_count)

if __name__ == "__main__":
    main()