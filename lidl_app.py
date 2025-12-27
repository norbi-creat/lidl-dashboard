import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "Lidl2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Ani-Roll Login")
        st.text_input("Please enter password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Ani-Roll Login")
        st.text_input("Please enter password:", type="password", on_change=password_entered, key="password")
        st.error("😕 Incorrect password!")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- CONNECTION ---
def connect_to_sheets():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_key_file_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            sheet = client.open("Lidl_Projekt_Adatbazis").sheet1
            return sheet
    except Exception as e:
        st.error(f"Error: {e}")
        return None

st.success("Siker! Bejelentkezve.")
