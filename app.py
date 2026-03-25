import streamlit as st
import pandas as pd
import os

# --- CONFIG ---
ADMIN_PASSWORD = "your_secret_password" 
TEAM_MEMBERS = ["Anosh", "Haris", "Somma", "Ifrah", "Nadia", "Hassaan", "Faizan"]
LEAVE_DB = "leave_data.csv"

# --- SELF-HEALING DATA LOADER ---
def load_data():
    cols = ["Name", "Date", "Status"]
    if os.path.exists(LEAVE_DB):
        try:
            df = pd.read_csv(LEAVE_DB)
            # Check if any required column is missing
            for col in cols:
                if col not in df.columns:
                    df[col] = "Approved" # Default for old data
            return df[cols] # Only return the columns we need
        except Exception:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

# Load the data safely
df_leave = load_data()

# --- SIDEBAR AUTH ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])

authenticated = False
if access_mode == "Manager/Admin":
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    if pwd == abc123
        authenticated = True
    elif pwd != "":
        st.sidebar.error("Incorrect Password")

st.title("🛡️ QA & Publishing Team Leave Manager")

# --- 1. MANAGER VIEW ---
if access_mode == "Manager/Admin" and authenticated:
    st.header("🔑 Manager Dashboard")
    pending = df_leave[df_leave["Status"] == "Pending Approval"]
    
    if not pending.empty:
        for idx, row in pending.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{row['Name']}** requested **{row['Date']}**")
            if c2.button("Approve ✅", key=f"app_{idx}"):
                df_leave.at[idx, "Status"] = "Approved"
                df_leave.to_csv(LEAVE_DB, index=False)
                st.rerun()
            if c3.button("Deny ❌", key=f"den_{idx}"):
                df_leave = df_leave.drop(idx)
                df_leave.to_csv(LEAVE_DB, index=False)
                st.rerun()
    else:
        st.info("No pending requests.")

# --- 2. TEAM MEMBER VIEW ---
elif access_mode == "Team Member":
    st.header("📝 Request Leave")
    with st.form("leave_entry"):
        name = st.selectbox("Your Name", TEAM_MEMBERS)
        date = st.date_input("Choose Date")
        if st.form_submit_button("Submit Request"):
            # Ensure we use the exact column names
            new_row = pd.DataFrame([[name, str(date), "Pending Approval"]], 
                                  columns=["Name", "Date", "Status"])
            df_leave = pd.concat([df_leave, new_row], ignore_index=True)
            df_leave.to_csv(LEAVE_DB, index=False)
            st.success("Sent for approval!")
            st.rerun()

# --- 3. PUBLIC CALENDAR (THE "ERROR" SECTION) ---
st.divider()
st.header("📅 Confirmed Team Schedule")

# We use .get() or a safe check to ensure the app never crashes here
if "Status" in df_leave.columns:
    confirmed = df_leave[df_leave["Status"] == "Approved"]
    if not confirmed.empty:
        st.table(confirmed.sort_values("Date"))
    else:
        st.info("No approved leaves yet.")
else:
    st.warning("Data structure initializing... please refresh.")
