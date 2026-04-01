import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIG ---
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]
MIN_STAFF_REQUIRED = 3
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7iiQmtnEj3GVbT1IhajMd3bndS1S9_HTrCn1cwqF9ZefnUwnvSX3WyBRSEdSGwtUTpqy1TRpTe3n8/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxzetxYGd7Zj02BgP-bC8nou6k9HM-SQYkAiY_yJbvc37FJzuaUbF3h6Qz0GTFi9u3C/exec"

st.set_page_config(page_title="Team Leave Manager", layout="wide")

@st.cache_data(ttl=2)
def load_data():
    try:
        fresh_url = f"{SHEET_CSV_URL}&cache_buster={time.time()}"
        return pd.read_csv(fresh_url)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_data()
if not df_leave.empty:
    df_leave['Date'] = df_leave['Date'].astype(str)

st.title("🛡️ QA & Publishing Team Leave Manager")

tab1, tab2 = st.tabs(["📝 Log Leave", "🔄 Swap Marketplace"])

with tab1:
    st.header("Log Your Leave")
    with st.form("request_form", clear_on_submit=True):
        u_name = st.selectbox("Your Name", TEAM_MEMBERS)
        u_date = st.date_input("Date of Leave", datetime.now())
        if st.form_submit_button("Submit and Approve"):
            payload = {"name": u_name, "date": str(u_date), "action": "add"}
            requests.post(SCRIPT_URL, json=payload)
            time.sleep(2)
            st.cache_data.clear()
            st.success(f"Leave logged for {u_name}")
            st.rerun()

with tab2:
    st.header("Peer-to-Peer Swap")
    st.info("This will swap your approved date with a teammate's approved date.")
    
    with st.form("swap_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            my_name = st.selectbox("Your Name (Requester)", TEAM_MEMBERS)
            my_approved = df_leave[(df_leave["Name"] == my_name) & (df_leave["Status"] == "Approved")]
            old_date = st.selectbox("Your Date to Give Up", my_approved["Date"].tolist() if not my_approved.empty else ["No dates found"])
            
        with col_b:
            partner_name = st.selectbox("Swap Partner", [t for t in TEAM_MEMBERS if t != my_name])
            partner_approved = df_leave[(df_leave["Name"] == partner_name) & (df_leave["Status"] == "Approved")]
            new_date = st.selectbox("Partner's Date You Want", partner_approved["Date"].tolist() if not partner_approved.empty else ["Partner has no dates"])

        if st.form_submit_button("Execute Swap"):
            if old_date != "No dates found" and new_date != "Partner has no dates":
                payload = {
                    "name": my_name,
                    "partner_name": partner_name,
                    "old_date": str(old_date),
                    "new_date": str(new_date),
                    "action": "swap"
                }
                with st.spinner("Updating both schedules..."):
                    requests.post(SCRIPT_URL, json=payload)
                    time.sleep(2.5)
                    st.cache_data.clear()
                    st.success(f"Successfully swapped {my_name}'s {old_date} with {partner_name}'s {new_date}!")
                    st.rerun()
            else:
                st.error("Both users must have approved leaves in the system to perform a swap.")

# --- CALENDAR & COVERAGE ---
st.divider()
st.header("📊 Coverage & Calendar")
check_date = st.date_input("Check staffing for:", datetime.now(), key="check_date")
date_str = str(check_date)

absent_list = df_leave[(df_leave["Date"] == date_str) & (df_leave["Status"] == "Approved")]["Name"].tolist()
present_count = len(TEAM_MEMBERS) - len(absent_list)

c1, c2 = st.columns(2)
c1.metric("Staff Present", f"{present_count} / {len(TEAM_MEMBERS)}")
if present_count < MIN_STAFF_REQUIRED:
    c2.error(f"⚠️ UNDERSTAFFED!")
else:
    c2.success("✅ Staffing OK.")

st.dataframe(df_leave[df_leave["Status"] == "Approved"].sort_values("Date"), use_container_width=True)
