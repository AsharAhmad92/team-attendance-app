import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
TEAM_MEMBERS = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
MIN_STAFF_REQUIRED = 3
DB_FILE = "leave_data.csv"

# Load or create the database
try:
    df = pd.read_csv(DB_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Name", "Date", "Type"])

st.set_page_config(page_title="Team Coverage Tracker", layout="wide")
st.title("📅 Team Leave & Coverage Tool")

# --- SIDEBAR: LOG NEW LEAVE ---
st.sidebar.header("Log/Request Leave")
with st.sidebar.form("leave_form"):
    user = st.selectbox("Who are you?", TEAM_MEMBERS)
    leave_date = st.date_input("Select Date")
    submit = st.form_submit_button("Submit Leave")

    if submit:
        new_data = pd.DataFrame([[user, str(leave_date), "Planned"]], columns=["Name", "Date", "Type"])
        df = pd.concat([df, new_data], ignore_index=True).drop_duplicates()
        df.to_csv(DB_FILE, index=False)
        st.success(f"Leave logged for {user} on {leave_date}")

# --- MAIN PANEL: COVERAGE CHECK ---
st.subheader("Monthly Coverage Overview")
selected_month = st.date_input("Check coverage for date:", datetime.now())
day_str = str(selected_month)

# Filter data for the selected day
absent_today = df[df['Date'] == day_str]['Name'].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_today)

# Visual Indicators
col1, col2 = st.columns(2)
with col1:
    st.metric("Team Members Present", f"{present_count} / {len(TEAM_MEMBERS)}")
    
with col2:
    if present_count < MIN_STAFF_REQUIRED:
        st.error("⚠️ CRITICAL: Understaffed! Swaps required.")
    else:
        st.success("✅ Coverage is sufficient.")

# Show list of absences
if absent_today:
    st.write(f"**Absent on {day_str}:** {', '.join(absent_today)}")
else:
    st.write(f"**Everyone is present on {day_str}!**")

# --- SWAP BOARD ---
st.divider()
st.subheader("🔄 Swap Marketplace")
st.info("Need to swap? Post a message here so a teammate can 'trade' dates with you.")
swap_msg = st.text_input("Post a swap request (e.g., 'Alice: Trading Friday for next Monday')")
if st.button("Post Request"):
    st.toast("Request posted to the team!") # In a full app, you'd save this to a 'swaps.csv'

# --- DATA TABLE ---
with st.expander("View Full Leave Table"):
    st.dataframe(df, use_container_width=True)