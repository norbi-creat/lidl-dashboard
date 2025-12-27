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
            headers = data[0]
            rows = data[1:]
            
            # --- JAVÍTÁS: Automatikusan egyedivé tesszük a fejlécneveket ---
            unique_headers = []
            for i, h in enumerate(headers):
                new_header = h if h.strip() else f"Oszlop_{i}"
                if new_header in unique_headers:
                    unique_headers.append(f"{new_header}_{i}")
                else:
                    unique_headers.append(new_header)
            
            df = pd.DataFrame(rows, columns=unique_headers)
            
            st.write("### Utolsó rögzített tevékenységek")
            st.dataframe(df.tail(15), use_container_width=True)
        else:
            st.info("A táblázat jelenleg üres. Rögzítsen új adatot a menüben!")

# --- 2. NAPI JELENTÉS BEKÜLDÉSE ---
if submit_napi:
    if sheet:
        # PONTOSAN 8 ADAT: A(Dátum), B(Szakasz), C(Létszám), D(Leírás), E(Hiba), F(Típus), G(Késés), H(Idő)
        uj_sor = [[str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]]
        
        # Ez a parancs kényszeríti az A oszloptól való írást:
        sheet.append_rows(uj_sor, value_input_option='RAW')
        
        st.success("Adat elmentve az A oszloptól!")
        st.balloons()

# --- 3. HIBA JELENTÉSE BEKÜLDÉSE ---
if submit_hiba:
    if sheet:
        # Itt is PONTOSAN 8 ADAT, üres helyekkel a C és D oszlopban
        uj_sor_h = [[str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]]
        
        # Kényszerített írás az A oszloptól:
        sheet.append_rows(uj_sor_h, value_input_option='RAW')
        
        st.error("Hiba rögzítve az A oszloptól!")
        
# --- 4. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Kalkulátor")
    netto = st.number_input("Nettó (Ft)", min_value=0, value=100000)
    st.metric("Végösszeg (15% pufferrel)", f"{netto * 1.15:,.0f} Ft")








