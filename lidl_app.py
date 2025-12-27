import json
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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
        st.text_input("Kérem a jelszót:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 Hibás jelszó!")
        st.text_input("Kérem a jelszót:", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- KAPCSOLÓDÁS A TÁBLÁZATHOZ ---
def connect_to_sheets():
    try:
        # Itt kényszerítjük, hogy szövegből listává alakítsa az adatot
        raw_creds = st.secrets["gcp_service_account"]
        if isinstance(raw_creds, str):
            creds_info = json.loads(raw_creds)
        else:
            creds_info = dict(raw_creds)
            
        client = gspread.service_account_from_dict(creds_info)
        sheet = client.open("Lidl_Projekt_Adatbazis").sheet1
        return sheet
    except Exception as e:
        st.error(f"Csatlakozási hiba: {e}")
        return None

# --- OLDALSÁV (MENÜ) ---
st.sidebar.title("Menü")
page = st.sidebar.radio("Válassz funkciót:", ["📊 Műszerfal", "📝 Napi jelentés", "💰 Kalkulátor"])

sheet = connect_to_sheets()

# --- 1. MŰSZERFAL (ADATOK MEGTEKINTÉSE) ---
if page == "📊 Műszerfal":
    st.title("🏗️ Projekt Áttekintés")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            # Létrehozzuk a táblázatot
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # --- JAVÍTÁS: Ez a sor kezeli az ismétlődő oszlopneveket ---
            df.columns = [f"{col}_{i}" if list(data[0]).count(col) > 1 else col for i, col in enumerate(data[0])]
            
            st.write("### Utolsó rögzített tevékenységek")
            st.dataframe(df.tail(10), use_container_width=True)
        else:
            st.info("Még nincs rögzített adat a táblázatban.")
# --- 2. NAPI JELENTÉS (ADATBEKÜLDÉS) ---
elif page == "📝 Napi jelentés":
    st.title("📝 Napi Jelentés Rögzítése")
    with st.form("adat_form"):
        datum = st.date_input("Dátum", datetime.now())
        fázis = st.selectbox("Munkafolyamat", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        letszam = st.number_input("Létszám (fő)", min_value=1, value=4)
        leiras = st.text_area("Rövid leírás a napi munkáról")
        
        submit = st.form_submit_button("Adatok Mentése")
        
        if submit:
            if sheet:
                uj_sor = [str(datum), fázis, letszam, leiras, datetime.now().strftime("%H:%M:%S")]
                sheet.append_row(uj_sor)
                st.success("Adat elmentve a Google Táblázatba!")
                st.balloons()

# --- 3. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Gyors Kalkulátor")
    st.info("Itt tudod gyorsan kiszámolni a költségeket.")
    
    egysegar = st.number_input("Egységár (Ft)", min_value=0, value=1000)
    mennyiseg = st.number_input("Mennyiség", min_value=0.0, value=1.0)
    
    osszesen = egysegar * mennyiseg
    st.metric("Végösszeg", f"{osszesen:,.0f} Ft".replace(",", " "))





