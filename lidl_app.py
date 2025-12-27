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

# --- KAPCSOLÓDÁS A TÁBLÁZATHOZ ---
def connect_to_sheets():
    try:
        raw_creds = st.secrets["gcp_service_account"]
        creds_info = json.loads(raw_creds) if isinstance(raw_creds, str) else dict(raw_creds)
        client = gspread.service_account_from_dict(creds_info)
        return client.open("Lidl_Projekt_Adatbazis").sheet1
    except Exception as e:
        st.error(f"Hiba a csatlakozáskor: {e}")
        return None

sheet = connect_to_sheets()

# --- OLDALSÁV (4 RÉSZ) ---
st.sidebar.title("Lidl Projekt Navigáció")
page = st.sidebar.radio("Válaszd ki a funkciót:", 
                        ["📊 Műszerfal", "📝 Napi jelentés", "⚠️ Hiba jelentése", "💰 Kalkulátor"])

# --- 1. MŰSZERFAL ---
if page == "📊 Műszerfal":
    st.title("🏗️ Projekt Áttekintés")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            headers = data[0]
            # Oszlopnevek egyedivé tétele a hibák elkerülésére
            unique_headers = [f"{h if h else 'Oszlop'}_{i}" if h in headers[:i] or not h else h for i, h in enumerate(headers)]
            df = pd.DataFrame(data[1:], columns=unique_headers)
            st.write("### Utolsó rögzített tevékenységek")
            st.dataframe(df.tail(20), use_container_width=True)
        else:
            st.info("A táblázat jelenleg üres. Rögzítsen új adatot!")

# --- 2. NAPI JELENTÉS ---
elif page == "📝 Napi jelentés":
    st.title("📝 Napi Jelentés Rögzítése")
    with st.form("napi_form"):
        datum = st.date_input("Dátum", datetime.now())
        fazis = st.selectbox("Munkafolyamat", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Áthidalás", "Egyéb"])
        letszam = st.number_input("Létszám (fő)", min_value=1, value=4)
        leiras = st.text_area("Rövid leírás a napi munkáról")
        submit_napi = st.form_submit_button("Mentés")
        
        if submit_napi:
            if sheet:
                # 8 oszlop kényszerítése az A-H tartományba
                uj_sor = [[str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]]
                sheet.append_rows(uj_sor, value_input_option='USER_ENTERED', table_range='A1:H1')
                st.success("Adat sikeresen elmentve az A oszloptól!")
                st.balloons()

# --- 3. HIBA JELENTÉSE ---
elif page == "⚠️ Hiba jelentése":
    st.title("⚠️ Probléma vagy Késés Jelentése")
    with st.form("hiba_form"):
        st.warning("Ezt akkor töltsd ki, ha valami hátráltatja a munkát!")
        datum_h = st.date_input("Dátum", datetime.now())
        fazis_h = st.selectbox("Melyik fázisnál merült fel?", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Szállítás"])
        tipus = st.selectbox("Hiba típusa", ["Logisztikai", "Műszaki", "Időjárás", "Személyi"])
        ora = st.number_input("Várható késés (óra)", min_value=0.0, step=0.5)
        submit_hiba = st.form_submit_button("Hiba rögzítése")
        
        if submit_hiba:
            if sheet:
                # 8 oszlopos sorrend megtartása, üres C és D oszloppal az eltolódás ellen
                uj_sor_h = [[str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]]
                sheet.append_rows(uj_sor_h, value_input_option='USER_ENTERED', table_range='A1:H1')
                st.error("Hiba és késés rögzítve a rendszerben!")

# --- 4. KALKULÁTOR (PROJEKT & KÖTBÉR) ---
elif page == "💰 Kalkulátor":
    st.title("💰 Projekt & Kötbér Kalkulátor")
    
    st.info("A Lidl standard szerint 15% kockázati puffer és kötbér-figyelés szükséges.")
    
    tab1, tab2 = st.tabs(["Költségtervezés", "Kötbér számítás"])
    
    with tab1:
        netto = st.number_input("Nettó tervezett összeg (Ft)", min_value=0, value=1000000)
        puffer = netto * 0.15
        st.metric("Kockázati puffer (15%)", f"{puffer:,.0f} Ft".replace(",", " "))
        st.metric("Várható bruttó keret", f"{netto + puffer:,.0f} Ft".replace(",", " "))
        st.write("---")
        st.caption("Javaslat: 5% vágási veszteség anyagnál, 20% időbeli ráhagyás.")

    with tab2:
        st.subheader("Késedelmi kötbér")
        napi_kotber = st.number_input("Napi kötbér összege (Ft/nap)", min_value=0, value=50000)
        keses_napok = st.number_input("Késedelmes napok száma", min_value=0, value=0)
        
        osszes_kotber = napi_kotber * keses_napok
        if osszes_kotber > 0:
            st.error(f"Levonandó kötbér: {osszes_kotber:,.0f} Ft".replace(",", " "))
        else:
            st.success("Jelenleg nincs kötbér kockázat.")








