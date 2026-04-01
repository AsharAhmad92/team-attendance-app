import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

# 🚨 LINKS
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7iiQmtnEj3GVbT1IhajMd3bndS1S9_HTrCn1cwqF9ZefnUwnvSX3WyBRSEdSGwtUTpqy1TRpTe3n8/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwV7q7iDx6WfGhKh5rpnDJXLlkh8Z9yCU4q2yzGPGSH39bMLO2MT1ak234-CXfUci_R/exec"

st.set_page_config(page_title="QA & Publishing Leave Manager", layout="wide")

# --- DATA LOADER ---
@st.cache_data(ttl=2)
def load_data():
    try:
        sep = "&" if "?" in SHEET_CSV_URL else "?"
        fresh_url = f"{SHEET_CSV_URL}{sep}cache_buster={time.time()}"
        return pd.read_csv(fresh_url)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_data()
if not df_leave.empty:
    df_leave['Date'] = df_leave['Date'].astype(str)

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- 1. TEAM MEMBER VIEW ---
tab1, tab2 = st.tabs(["📝 Log Leave", "🔄 Swap Marketplace"])

with tab1:
    st.header("Log Your Leave")
    st.info("Leaves logged here are automatically approved and updated on the calendar.")
    with st.form("request_form", clear_on_submit=True):
        u_name = st.selectbox("Your Name", TEAM_MEMBERS)
        u_date = st.date_input("Date of Leave", datetime.now())
        if st.form_submit_button("Submit and Approve"):
            payload = {"name": u_name, "date": str(u_date), "action": "add"}
            with st.spinner("Updating Calendar..."):
                requests.post(SCRIPT_URL, json=payload)
                time.sleep(2) # Give Google time to sync
                st.cache_data.clear()
                st.success(f"Confirmed: Leave logged for {u_name} on {u_date}")
                st.rerun()

with tab2:
    st.header("Swap Your Leave")
    my_name = st.selectbox("Who are you?", TEAM_MEMBERS, key="swap_name")
    my_approved = df_leave[(df_leave["Name"] == my_name) & (df_leave["Status"] == "Approved")]
    
    if not my_approved.empty:
        with st.form("swap_form"):
            old_date = st.selectbox("Select Leave to Give Up", my_approved["Date"].tolist())
            new_date = st.date_input("Select New Date You Want")
            if st.form_submit_button("Confirm Swap"):
                payload = {
                    "name": my_name,
                    "old_date": str(old_date),
                    "new_date": str(new_date),
                    "action": "swap"
                }
                requests.post(SCRIPT_URL, json=payload)
                time.sleep(2)
                st.cache_data.clear()
                st.success("Swap processed and calendar updated.")
                st.rerun()
    else:
        st.warning("No logged leaves found to swap.")

# --- 2. ATTENDANCE CHECK & CALENDAR ---
st.divider()
st.header("📊 Real-Time Coverage Check")

check_date = st.date_input("Check staffing for:", datetime.now(), key="check_date")
date_str = str(check_date)

absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_list)

col1, col2 = st.columns(2)
col1.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")
if present_count < MIN_STAFF_REQUIRED:
    col2.error(f"⚠️ UNDERSTAFFED! (Min: {MIN_STAFF_REQUIRED})")
else:
    col2.success("✅ Staffing is sufficient.")

st.subheader("📅 Confirmed Approved Leaves")
approved_df = df_leave[df_leave["Status"] == "Approved"]
if not approved_df.empty:
    st.dataframe(approved_df.sort_values("Date"), use_container_width=True)
else:
    st.info("No leaves logged in the system yet.")
