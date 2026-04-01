import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
ADMIN_PASSWORD = "abc123" 
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3

# 🚨 PASTE YOUR LINKS HERE
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7iiQmtnEj3GVbT1IhajMd3bndS1S9_HTrCn1cwqF9ZefnUwnvSX3WyBRSEdSGwtUTpqy1TRpTe3n8/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyNdpfKKPcHtGKLddWl1GvaFwLgw09ujDZrRBoVWhm2h8Us9cpEoQ7a3QQ7x9-QJP4/exec"

st.set_page_config(page_title="QA & Publishing Leave Manager", layout="wide")

# --- DATA LOADER ---
@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_data()

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- SIDEBAR ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])
authenticated = False
if access_mode == "Manager/Admin":
    if st.sidebar.text_input("Admin Password", type="password") == ADMIN_PASSWORD:
        authenticated = True

# --- 1. TEAM MEMBER VIEW (The Request Form) ---
if access_mode == "Team Member":
    st.header("📝 Submit Leave Request")
    with st.form("request_form", clear_on_submit=True):
        u_name = st.selectbox("Your Name", TEAM_MEMBERS)
        u_date = st.date_input("Date Requested", datetime.now())
        
        if st.form_submit_button("Submit to Sheet"):
            payload = {
                "name": u_name,
                "date": str(u_date),
                "status": "Pending Approval",
                "action": "add"
            }
            try:
                response = requests.post(SCRIPT_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"✅ Success! Request for {u_name} on {u_date} has been logged.")
                    st.balloons()
                    st.cache_data.clear() # Clear cache to show new data
                else:
                    st.error("Submission failed.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 2. MANAGER APPROVAL VIEW ---
if authenticated:
    st.divider()
    st.header("🔑 Manager Approval Queue")
    
    pending_df = df_leave[df_leave["Status"] == "Pending Approval"]
    
    if not pending_df.empty:
        for index, row in pending_df.iterrows():
            col_name, col_date, col_btn = st.columns([2, 2, 1])
            col_name.write(f"👤 {row['Name']}")
            col_date.write(f"📅 {row['Date']}")
            
            if col_btn.button("Approve ✅", key=f"btn_{index}"):
                approval_payload = {
                    "name": row['Name'],
                    "date": row['Date'],
                    "action": "approve"
                }
                with st.spinner("Updating Sheet..."):
                    res = requests.post(SCRIPT_URL, json=approval_payload)
                    if res.status_code == 200:
                        st.success(f"Approved {row['Name']}")
                        st.cache_data.clear() # Force refresh
                        st.rerun()
                    else:
                        st.error("Approval failed.")
    else:
        st.info("No pending requests to approve.")

# --- 3. ATTENDANCE CHECK & CALENDAR ---
st.divider()
st.header("📊 Real-Time Coverage")

check_date = st.date_input("Check staffing for:", datetime.now())
date_str = str(check_date)

# Fix for potential data type mismatch in CSV dates
df_leave['Date'] = df_leave['Date'].astype(str)
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
    st.info("No approved leaves found.")
