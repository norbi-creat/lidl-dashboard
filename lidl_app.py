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
page = st.sidebar.radio("Válassz funkciót:", ["📊 Műszerfal", "📝 Napi jelentés", "⚠️ Hiba jelentése", "💰 Kalkulátor"])

sheet = connect_to_sheets()

# --- 1. MŰSZERFAL ---
if page == "📊 Műszerfal":
    st.title("🏗️ Projekt Áttekintés")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            # Dupla oszlopnevek kezelése az appban
            df.columns = [f"{col}_{i}" if list(data[0]).count(col) > 1 else col for i, col in enumerate(data[0])]
            st.write("### Utolsó rögzített tevékenységek")
            st.dataframe(df.tail(15), use_container_width=True)
        else:
            st.info("Még nincs rögzített adat.")

# --- 2. NAPI JELENTÉS ---
if submit_napi:
    if sheet:
        # Sorrend: Dátum(A), Szakasz(B), Létszám(C), Leírás(D), Hiba?(E), Típus(F), Késés(G), Idő(H)
        # Itt a napi jelentésnél a hiba oszlopokba alapértelmezett értékeket írunk
        uj_sor = [str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]
        sheet.append_row(uj_sor)
        st.success("Adat elmentve!")
        st.balloons()
        
# --- 3. HIBA JELENTÉSE ---
if submit_hiba:
    if sheet:
        # Sorrend ugyanaz: Dátum(A), Szakasz(B), Létszám(C), Leírás(D), Hiba?(E), Típus(F), Késés(G), Idő(H)
        # Itt a C és D oszlopba üres szöveget teszünk, hogy a többi adat a helyére kerüljön
        uj_sor_h = [str(datum_h), szakasz_h, "", "", "Igen", hiba_tipus, keses, datetime.now().strftime("%H:%M:%S")]
        sheet.append_row(uj_sor_h)
        st.error("Hiba rögzítve!")
        
# --- 4. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Gyors Kalkulátor")
    netto = st.number_input("Nettó becsült összeg (Ft)", min_value=0, value=100000)
    puffer = netto * 0.15
    brutto = netto + puffer
    st.metric("Puffer (15%)", f"{puffer:,.0f} Ft".replace(",", " "))
    st.metric("Mindösszesen", f"{brutto:,.0f} Ft".replace(",", " "))







