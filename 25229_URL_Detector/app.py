# app.py
import streamlit as st
import pandas as pd
import tempfile
import os
import nest_asyncio
import altair as alt
import ipaddress  # For robust IP/CIDR filtering
from detector import AttackDetector

# Apply nest_asyncio for Scapy compatibility in some environments
nest_asyncio.apply()

# --- 1. Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="SIREN: URL Attack Detector (11 Attack Types)",
    page_icon="🚨"
)

# --- 2. Caching & Helper Functions ---

@st.cache_data(show_spinner=False)
def run_analysis(uploaded_file):
    """
    Saves the uploaded file to a temporary location and runs the
    AttackDetector analysis on it. Returns DataFrame and packet count.
    """
    spinner_text = f"SIREN is performing a comprehensive single-pass analysis on `{uploaded_file.name}`... This may take a moment."
    with st.spinner(spinner_text):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcapng") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            detector = AttackDetector()
            results_df, packet_count = detector.analyze_pcap(tmp_file_path)
        finally:
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass

    # Ensure timestamp is in a readable format (if still datetime)
    if not results_df.empty and 'Timestamp' in results_df.columns:
        results_df['Timestamp'] = pd.to_datetime(results_df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

    return results_df, packet_count

@st.cache_data
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Converts DataFrame to a CSV string for download with UTF-8-SIG encoding for better compatibility."""
    # The fix is changing 'utf-8' to 'utf-8-sig'
    return df.to_csv(index=False).encode('utf-8-sig')

@st.cache_data
def convert_df_to_json(df: pd.DataFrame) -> bytes:
    """Converts DataFrame to a JSON string for download."""
    return df.to_json(orient='records', indent=4).encode('utf-8')

# --- IP Range Filtering Function ---
def filter_by_ip_range(df: pd.DataFrame, ip_filter: str) -> pd.DataFrame:
    """Filters DataFrame by a single IP, a partial IP match, or a CIDR range."""
    if not ip_filter:
        return df

    ip_filter = ip_filter.strip()

    try:
        network = ipaddress.ip_network(ip_filter, strict=False)
        in_range = df['SourceIP'].apply(lambda ip: ipaddress.ip_address(ip) in network if pd.notna(ip) else False)
        return df[in_range]

    except ValueError:
        return df[df['SourceIP'].str.contains(ip_filter, case=False, na=False)]


# --- 3. UI Rendering Functions ---

def display_sidebar(df: pd.DataFrame) -> tuple:
    """Renders the sidebar with filters and returns the user's selections."""
    st.sidebar.title("🔬 Analysis & Filters")

    if st.sidebar.button("Start New Analysis", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.sidebar.header("Filter Detections")

    # Filter by attack status (Restores Brute Force Detected)
    status_options = ["All", "Successful", "Attempted", "Brute Force Detected"]
    status_filter = st.sidebar.radio(
        "Filter by Status:",
        options=status_options,
        index=0,
        horizontal=True
    )

    # Filter by attack type
    attack_types = sorted(df['AttackType'].unique()) if not df.empty else []
    selected_attacks = st.sidebar.multiselect(
        "Filter by Attack Type:",
        options=attack_types,
        default=attack_types
    )

    # Filter by source IP
    source_ip_filter = st.sidebar.text_input(
        "Filter by Source IP (CIDR or partial match):",
        placeholder="e.g., 192.168.1.1 or 10.0.0.0/8"
    )

    return selected_attacks, source_ip_filter, status_filter


def display_metrics(df: pd.DataFrame, packet_count: int):
    """Displays the key metrics in a 4-column layout."""
    st.subheader("Analysis Summary")

    successful_attacks = df[df['AttackStatus'] == 'Successful']
    attempted_attacks = df[df['AttackStatus'] == 'Attempted']
    brute_force_attacks = df[df['AttackStatus'] == 'Brute Force Detected']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Packets Scanned", f"{packet_count:,}")
    with col2:
        st.metric("🚨 Total Detections", f"{len(df):,}")
    with col3:
        st.metric("✅ Successful Attacks", f"{len(successful_attacks):,}")
    with col4:
        st.metric("🔥 Brute Force Detected", f"{len(brute_force_attacks):,}")


def display_dashboard(filtered_df: pd.DataFrame, packet_count: int):
    """Renders the main dashboard using tabs."""
    st.header("📊 Analysis Results (All 11 Attack Types)")
    tab1, tab2 = st.tabs(["📈 Dashboard", "📜 Detailed Logs"])

    with tab1:
        display_metrics(filtered_df, packet_count)
        st.subheader("Attack Type Distribution by Status")

        # Define color scale (Green/Yellow/Red for Brute Force)
        color_scale = alt.Scale(
            domain=['Successful', 'Attempted', 'Brute Force Detected'],
            range=['#28a745', '#ffc107', '#dc3545']
        )

        # Create a stacked bar chart
        chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X('AttackType:N', title='Attack Type', sort='-y'),
            y=alt.Y('count():Q', title='Number of Detections'),
            color=alt.Color('AttackStatus:N', scale=color_scale),
            tooltip=['AttackType', 'AttackStatus', 'count()']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

    with tab2:
        st.subheader("Detailed Attack Logs")
        st.write("Results consolidated from detection runs. Each matched attack is shown as its own row.")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        st.subheader("Export Results")
        col1, col2 = st.columns(2)
        with col1:
            csv_data = convert_df_to_csv(filtered_df)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data, file_name="siren_report.csv", mime="text/csv",
                key="download_csv", use_container_width=True
            )
        with col2:
            json_data = convert_df_to_json(filtered_df)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data, file_name="siren_report.json", mime="application/json",
                key="download_json", use_container_width=True
            )


# --- 4. Main Application ---
def main():
    """Main function to run the Streamlit app."""
    if 'analysis_results' not in st.session_state:
        # Initial Welcome Page Logic
        st.title("🚨 SIREN: URL-Based Cyber Attack Detection System")
        st.write("Focus: All 11 URL-based attack types from the problem statement.")

        with st.container():
            st.subheader("Get Started")
            st.write("Upload a `.pcap` or `.pcapng` file to begin analysis.")
            uploaded_file = st.file_uploader(
                "Upload a network traffic file",
                type=['pcap', 'pcapng'],
                label_visibility="collapsed"
            )
            if uploaded_file:
                results_df, packet_count = run_analysis(uploaded_file)
                st.session_state['analysis_results'] = (results_df, packet_count)
                st.rerun()

    else:
        # Dashboard Logic
        st.title("🚨 SIREN Analysis Dashboard")
        df_results, packet_count = st.session_state['analysis_results']

        if df_results.empty:
            st.success("✅ Analysis complete. No attacks were detected.", icon="🎉")
            if st.button("Analyze Another File"):
                st.session_state.clear()
                st.rerun()
            return

        # Get filter values from the sidebar
        selected_attacks, source_ip, status_filter = display_sidebar(df_results)
        
        # This single line handles the multiselect filter correctly.
        # If nothing is selected, the dataframe will be empty.
        filtered_df = df_results[df_results['AttackType'].isin(selected_attacks)]

        # 2. Apply Attack Status filter
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['AttackStatus'] == status_filter]

        # 3. Apply the IP range filter
        filtered_df = filter_by_ip_range(filtered_df, source_ip)

        if filtered_df.empty:
            st.warning("No data matches the current filter criteria.", icon="⚠️")
        else:
            display_dashboard(filtered_df, packet_count)


if __name__ == "__main__":
    main()
