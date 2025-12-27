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
            unique_headers = [f"{h if h else 'Oszlop'}_{i}" if h in headers[:i] or not h else h for i, h in enumerate(headers)]
            df = pd.DataFrame(data[1:], columns=unique_headers)
            st.dataframe(df.tail(20), use_container_width=True)

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
            # 8 oszlop: A(Dátum), B(Szakasz), C(Létszám), D(Leírás), E(Hiba), F(Típus), G(Késés), H(Idő)
            uj_sor = [[str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]]
            sheet.append_rows(uj_sor, value_input_option='USER_ENTERED', table_range='A1:H1')
            st.success("Mentve!")

# --- 3. HIBA JELENTÉSE ---
elif page == "⚠️ Hiba jelentése":
    st.title("⚠️ Hiba rögzítése")
    with st.form("hiba_form"):
        datum_h = st.date_input("Dátum", datetime.now())
        fazis_h = st.selectbox("Hol?", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        tipus = st.selectbox("Típus", ["Logisztikai", "Műszaki", "Időjárás"])
        ora = st.number_input("Késés (óra)", min_value=0.0)
        submit_hiba = st.form_submit_button("Hiba rögzítése")
        
        if submit_hiba:
            # Itt rögzítjük az "Igen"-t az E oszlopban és az órát a G oszlopban
            uj_sor_h = [[str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]]
            sheet.append_rows(uj_sor_h, value_input_option='USER_ENTERED', table_range='A1:H1')
            st.error(f"Hiba rögzítve: {ora} óra késés.")

# --- 4. OKOS KALKULÁTOR (Adatbázis alapú) ---
elif page == "💰 Kalkulátor":
    st.title("💰 Intelligens Kötbér Kalkulátor")
    
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Csak a hiba-sorokat szűrjük ki (ahol E oszlop = Igen)
            hibak = df[df['Hiba történt-e'] == 'Igen'].copy()
            
            # Kiszámoljuk az összesített késést órában
            hibak['Késés órában'] = pd.to_numeric(hibak['Késés órában'], errors='coerce').fillna(0)
            osszes_ora_keses = hibak['Késés órában'].sum()
            
            st.subheader("Aktuális projekt állapot")
            col1, col2 = st.columns(2)
            col1.metric("Összes hiba száma", len(hibak))
            col2.metric("Összes késés", f"{osszes_ora_keses} óra")
            
            st.write("---")
            st.subheader("Pénzügyi levonás")
            oradij = st.number_input("Kötbér mértéke (Ft / óra késés)", min_value=0, value=15000)
            
            varhato_kotber = osszes_ora_keses * oradij
            
            if varhato_kotber > 0:
                st.error(f"A táblázat adatai alapján levonandó kötbér: {varhato_kotber:,.0f} Ft".replace(",", " "))
                st.write("### Érintett hibák listája:")
                st.table(hibak[['Dátum', 'Munkaszakasz', 'Hiba típusa', 'Késés órában']])
            else:
                st.success("A táblázat szerint nincs jegyzőkönyvezett késés.")
        else:
            st.info("Nincs elég adat a számításhoz.")








