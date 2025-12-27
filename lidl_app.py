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
        # Itt fontos, hogy a táblázat neve pontosan ez legyen:
        return client.open("Lidl_Projekt_Adatbazis").sheet1
    except Exception as e:
        st.error(f"Hiba: {e}")
        return None

sheet = connect_to_sheets()

# --- MENÜ (4 RÉSZ) ---
page = st.sidebar.radio("Menü", ["📊 Műszerfal", "📝 Napi jelentés", "⚠️ Hiba jelentése", "💰 Kalkulátor"])

# --- 1. MŰSZERFAL ---
if page == "📊 Műszerfal":
    st.title("🏗️ Projekt Áttekintés")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            headers = data[0]
            # Egyedivé tesszük a fejléceket a megjelenítéshez
            unique_headers = [f"{h if h else 'Oszlop'}_{i}" if h in headers[:i] or not h else h for i, h in enumerate(headers)]
            df = pd.DataFrame(data[1:], columns=unique_headers)
            st.dataframe(df.tail(20), use_container_width=True)
        else:
            st.info("Még nincs rögzített adat.")

# --- 2. NAPI JELENTÉS ---
elif page == "📝 Napi jelentés":
    st.title("📝 Napi Jelentés")
    with st.form("napi_form"):
        datum = st.date_input("Dátum", datetime.now())
        fazis = st.selectbox("Munka", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        letszam = st.number_input("Létszám", min_value=1, value=4)
        leiras = st.text_area("Leírás")
        submit_napi = st.form_submit_button("Mentés")
        
        if submit_napi:
            if sheet:
                # 8 oszlop: Dátum, Szakasz, Létszám, Leírás, Hiba?, Típus, Késés, Időbélyeg
                uj_sor = [[str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]]
                # Kényszerítjük az A1-től való keresést a table_range-el
                sheet.append_rows(uj_sor, value_input_option='USER_ENTERED', table_range='A1:H1')
                st.success("Sikeres mentés az A oszloptól!")
                st.balloons()

# --- 3. HIBA JELENTÉSE ---
elif page == "⚠️ Hiba jelentése":
    st.title("⚠️ Hiba vagy Késés Jelentése")
    with st.form("hiba_form"):
        datum_h = st.date_input("Dátum", datetime.now())
        fazis_h = st.selectbox("Melyik fázis?", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        tipus = st.selectbox("Hiba típusa", ["Logisztikai", "Műszaki", "Időjárás", "Személyi"])
        ora = st.number_input("Késés (óra)", min_value=0.0, step=0.5)
        submit_hiba = st.form_submit_button("Hiba rögzítése")
        
        if submit_hiba:
            if sheet:
                # Üres helyeket hagyunk a Létszám(C) és Leírás(D) helyén
                uj_sor_h = [[str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]]
                # Kényszerítjük az A1-től való keresést
                sheet.append_rows(uj_sor_h, value_input_option='USER_ENTERED', table_range='A1:H1')
                st.error("Hiba/Késés rögzítve!")

# --- 4. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Gyors Kalkulátor")
    netto = st.number_input("Nettó becsült összeg (Ft)", min_value=0, value=100000)
    puffer = netto * 0.15 # 15% kockázati puffer
    brutto = netto + puffer
    
    st.metric("Puffer (15%)", f"{puffer:,.0f} Ft".replace(",", " "))
    st.metric("Mindösszesen", f"{brutto:,.0f} Ft".replace(",", " "))
    st.write("---")
    st.info("A Lidl standard alapján 5% anyagveszteség és 20% időbeli ráhagyás javasolt.")








