import streamlit as st
import pandas as pd
import os

# --- SECURE CONFIG ---
ADMIN_PASSWORD = "your_secret_password"  # Change this!
TEAM_MEMBERS = ["Somma", "Haris", "Anosh", "Ifrah", "Nadia", "Hassaan", "Faizan"]
LEAVE_DB = "leave_data.csv"

# --- DATA PERSISTENCE ---
def load_data():
    if os.path.exists(LEAVE_DB):
        return pd.read_csv(LEAVE_DB)
    return pd.DataFrame(columns=["Name", "Date", "Status"])

df_leave = load_data()

# --- SIDEBAR AUTHENTICATION ---
st.sidebar.title("🔐 Access Control")
access_mode = st.sidebar.selectbox("Select Mode", ["Team Member", "Manager/Admin"])

authenticated = False
if access_mode == "Manager/Admin":
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        authenticated = True
    elif pwd != "":
        st.sidebar.error("Incorrect Password")

# --- APP LAYOUT ---
st.title("🛡️ Content Team Leave Manager")

# 1. MANAGER VIEW (Conditional)
if access_mode == "Manager/Admin" and authenticated:
    st.header("🔑 Manager Dashboard")
    pending = df_leave[df_leave["Status"] == "Pending Approval"]
    
    if not pending.empty:
        for idx, row in pending.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{row['Name']}** requested **{row['Date']}**")
            if c2.button("Approve ✅", key=f"a_{idx}"):
                df_leave.at[idx, "Status"] = "Approved"
                df_leave.to_csv(LEAVE_DB, index=False)
                st.rerun()
            if c3.button("Deny ❌", key=f"d_{idx}"):
                df_leave = df_leave.drop(idx)
                df_leave.to_csv(LEAVE_DB, index=False)
                st.rerun()
    else:
        st.info("No pending requests to review.")

# 2. TEAM MEMBER VIEW
elif access_mode == "Team Member":
    st.header("📝 Request Leave")
    with st.form("leave_entry"):
        name = st.selectbox("Your Name", TEAM_MEMBERS)
        date = st.date_input("Choose Date")
        if st.form_submit_button("Submit Request"):
            new_row = pd.DataFrame([[name, str(date), "Pending Approval"]], 
                                  columns=["Name", "Date", "Status"])
            df_leave = pd.concat([df_leave, new_row]).drop_duplicates()
            df_leave.to_csv(LEAVE_DB, index=False)
            st.success("Sent for approval!")

# 3. PUBLIC CALENDAR (Always Visible)
st.divider()
st.header("📅 Confirmed Team Schedule")
# Show only approved leaves so the team knows who is ACTUALLY out.
confirmed = df_leave[df_leave["Status"] == "Approved"]
if not confirmed.empty:
    st.dataframe(confirmed.sort_values("Date"), use_container_width=True)
else:
    st.write("No leaves approved for the current period.")
