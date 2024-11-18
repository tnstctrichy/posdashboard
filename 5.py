import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

# Streamlit configuration
st.set_page_config(page_title="POS Dashboard - T.N.S.T.C. Trichy Region", layout="wide")

# Get yesterday's date
yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")

# Session state for uploaded data
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# Title with enhanced styling
st.markdown(f"""
    <h1 style="color: #4CAF50; text-align: center; font-family: 'Segoe UI', sans-serif; font-size: 40px; margin-bottom: 5px;">
        POS Dashboard - T.N.S.T.C. Trichy Region
    </h1>
    <h2 style="color: #FF5722; text-align: center; font-family: 'Arial', sans-serif; font-size: 24px;">
        Data as of {yesterday_date}
    </h2>
    """, unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose an option", ["View Dashboard", "Upload Data"])

# Password-protected upload section
if page == "Upload Data":
    if "upload_authenticated" not in st.session_state:
        st.session_state.upload_authenticated = False

    if not st.session_state.upload_authenticated:
        password = st.text_input("Enter the admin password for upload:", type="password")
        if password == "admin123":
            st.session_state.upload_authenticated = True
            st.success("Password correct! You can now upload data.")
        else:
            st.stop()

    st.markdown("### Upload POS Excel File")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if uploaded_file:
        try:
            data = pd.read_excel(uploaded_file)
            required_columns = ["SNO", "BRANCH", "RTNO", "VHNO", "ROUTE", "TYPE", "OPKM", "COLLECT", "EPKM", "REMARKS"]

            # Validate columns
            if all(col in data.columns for col in required_columns):
                st.session_state.uploaded_data = data
                st.success("File uploaded successfully! Switch to 'View Dashboard' to see the data.")
            else:
                st.error(f"The file must contain the required columns: {', '.join(required_columns)}")
        except Exception as e:
            st.error(f"Error processing the file: {e}")

# View Dashboard (Default Page)
if page == "View Dashboard":
    if st.session_state.uploaded_data is None:
        st.warning("No data uploaded yet. Please upload an Excel file in the 'Upload Data' section.")
    else:
        data = st.session_state.uploaded_data

        # Display POS data
        st.markdown("### POS Data Dashboard")
        st.dataframe(data)

        # Threshold Settings
        st.sidebar.markdown("### Threshold Settings")
        epkm_threshold = st.sidebar.number_input("Set Threshold EPKM", value=30, step=1)

        # Identify rows below threshold
        below_threshold = data[data["EPKM"] < epkm_threshold]

        # Highlight blinking rows below the threshold
        st.markdown(f"### Vehicles Below EPKM Threshold (Rs. {epkm_threshold:.2f})")
        if not below_threshold.empty:
            st.dataframe(below_threshold.style.applymap(
                lambda v: "background-color: #FFD700; color: black; font-weight: bold; animation: blink 1s infinite;"
                if v < epkm_threshold else "",
                subset=["EPKM"]
            ))
        else:
            st.success(f"All vehicles have EPKM above Rs. {epkm_threshold:.2f}!")

        # EPKM Distribution Visualization
        st.markdown("### EPKM Distribution Across Branches and Routes")
        
        # Branch-wise Aggregation
        branch_summary = data.groupby("BRANCH")["RTNO"].count().reset_index()
        branch_summary.rename(columns={"RTNO": "Route Count"}, inplace=True)
        
        fig_branch = px.bar(branch_summary, x="BRANCH", y="Route Count", color="Route Count",
                            title="Route Count by Branch",
                            labels={"BRANCH": "Branch", "Route Count": "Number of Routes"},
                            color_continuous_scale=px.colors.sequential.Plasma)
        st.plotly_chart(fig_branch, use_container_width=True)

        # Route-wise Visualization
        fig_route = px.bar(data, x="RTNO", y="EPKM", color="EPKM",
                           title="EPKM by Route Code",
                           labels={"RTNO": "Route Code", "EPKM": "EPKM (Rs.)"},
                           color_continuous_scale=["red", "yellow", "green"])
        st.plotly_chart(fig_route, use_container_width=True)

        # Search Filters
        st.sidebar.markdown("### Search Filters")
        search_route = st.sidebar.text_input("Search by Route Code or Route Name")
        search_branch = st.sidebar.text_input("Search by Branch")

        if search_route or search_branch:
            filtered_data = data[
                (data["RTNO"].astype(str).str.contains(search_route, case=False, na=False) if search_route else True) &
                (data["BRANCH"].astype(str).str.contains(search_branch, case=False, na=False) if search_branch else True)
            ]
            st.markdown(f"### Search Results for Route '{search_route}' and Branch '{search_branch}'")
            st.dataframe(filtered_data)

# Add CSS for blinking effect
st.markdown("""
<style>
@keyframes blink {
  50% { background-color: transparent; }
}
</style>
""", unsafe_allow_html=True)
