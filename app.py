import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIG ---
ADMIN_PASSWORD = st.secrets["abc123"]
TEAM_MEMBERS = ["Haris", "Anosh", "Hassaan", "Somma", "Ifrah", "Nadia", "Faizan"]

st.title("☁️ Google-Synced Team Tracker")

# --- CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch existing data
df_leave = conn.read(worksheet="Leaves", ttl="0") # ttl="0" ensures live data

# --- SIDEBAR AUTH ---
access_mode = st.sidebar.selectbox("Mode", ["Team Member", "Manager"])
is_admin = False
if access_mode == "Manager":
    if st.sidebar.text_input("Password", type="password") == ADMIN_PASSWORD:
        is_admin = True

# --- LOGIC: SUBMIT LEAVE ---
if access_mode == "Team Member":
    with st.form("request_form"):
        name = st.selectbox("Name", TEAM_MEMBERS)
        date = st.date_input("Date")
        if st.form_submit_button("Submit"):
            new_data = pd.DataFrame([[name, str(date), "Pending"]], 
                                    columns=["Name", "Date", "Status"])
            updated_df = pd.concat([df_leave, new_data])
            conn.update(worksheet="Leaves", data=updated_df)
            st.success("Synced to Google Sheets!")
            st.rerun()

# --- LOGIC: MANAGER APPROVAL ---
if is_admin:
    st.subheader("Pending Approvals")
    pending = df_leave[df_leave["Status"] == "Pending"]
    
    for idx, row in pending.iterrows():
        col1, col2 = st.columns([3, 1])
        col1.write(f"{row['Name']} - {row['Date']}")
        if col2.button("Approve", key=idx):
            df_leave.at[idx, "Status"] = "Approved"
            conn.update(worksheet="Leaves", data=df_leave)
            st.rerun()

# --- DISPLAY ---
st.divider()
st.subheader("📅 Confirmed Schedule")
st.dataframe(df_leave[df_leave["Status"] == "Approved"])
