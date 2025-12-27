import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime

# --- JELSZÓ VÉDELEM ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "Lidl2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.title("🔐 Ani-Roll Login")
        st.text_input("Jelszó:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 Hibás jelszó!")
        st.text_input("Jelszó:", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password():
    st.stop()

# --- KAPCSOLÓDÁS ---
def connect_to_sheets():
    try:
        raw_creds = st.secrets["gcp_service_account"]
        creds_info = json.loads(raw_creds) if isinstance(raw_creds, str) else dict(raw_creds)
        client = gspread.service_account_from_dict(creds_info)
        return client.open("Lidl_Projekt_Adatbazis").sheet1
    except Exception as e:
        st.error(f"Hiba: {e}")
        return None

sheet = connect_to_sheets()

# --- MENÜ ---
page = st.sidebar.radio("Menü", ["📊 Műszerfal", "📝 Napi jelentés", "⚠️ Hiba jelentése", "💰 Kalkulátor"])

# --- 1. MŰSZERFAL ---
if page == "📊 Műszerfal":
    st.title("🏗️ Projekt Áttekintés")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df.tail(15), use_container_width=True)

# --- 2. NAPI JELENTÉS ---
elif page == "📝 Napi jelentés":
    st.title("📝 Napi Jelentés")
    with st.form("napi_form"):
        datum = st.date_input("Dátum", datetime.now())
        fazis = st.selectbox("Munka", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        letszam = st.number_input("Létszám", min_value=1, value=4)
        leiras = st.text_area("Leírás")
        submit_napi = st.form_submit_button("Mentés")
        
        if submit_napi: # Ez most már a formon BELÜL van!
            uj_sor = [str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]
            sheet.append_row(uj_sor)
            st.success("Sikeres mentés!")

# --- 3. HIBA JELENTÉSE ---
elif page == "⚠️ Hiba jelentése":
    st.title("⚠️ Hiba/Késés")
    with st.form("hiba_form"):
        datum_h = st.date_input("Dátum", datetime.now())
        fazis_h = st.selectbox("Hol?", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        tipus = st.selectbox("Típus", ["Logisztikai", "Műszaki", "Időjárás"])
        ora = st.number_input("Késés (óra)", min_value=0.0)
        submit_hiba = st.form_submit_button("Hiba rögzítése")
        
        if submit_hiba: # Ez is a formon BELÜL van!
            uj_sor_h = [str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]
            sheet.append_row(uj_sor_h)
            st.error("Hiba rögzítve!")

# --- 4. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Kalkulátor")
    netto = st.number_input("Nettó (Ft)", min_value=0, value=100000)
    st.metric("Végösszeg (15% pufferrel)", f"{netto * 1.15:,.0f} Ft")






