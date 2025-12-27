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
            # Dupla oszlopnevek kezelése
            df.columns = [f"{col}_{i}" if list(data[0]).count(col) > 1 else col for i, col in enumerate(data[0])]
            st.write("### Utolsó rögzített tevékenységek")
            st.dataframe(df.tail(15), use_container_width=True)
        else:
            st.info("Még nincs rögzített adat.")

# --- 2. NAPI JELENTÉS ---
if page == "📝 Napi jelentés":
    # ... (a form marad)
    if submit:
        if sheet:
            # Oszlopok: A=Dátum, B=Szakasz, C=Létszám, D=Leírás, E=Hiba(Nem), F=Típus(-), G=Késés(0), H=Idő
            uj_sor = [str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]
            sheet.append_row(uj_sor)
            st.success("Adat elmentve!")

# --- 3. HIBA JELENTÉSE (JAVÍTOTT SORREND) ---
elif page == "⚠️ Hiba jelentése":
    # ... (a form marad)
    if submit_h:
        if sheet:
            # Oszlopok: A=Dátum, B=Szakasz, C=Létszám(üres), D=Leírás(üres), E=Hiba(Igen), F=Típus, G=Késés, H=Idő
            uj_sor_h = [str(datum_h), szakasz_h, "", "", "Igen", hiba_tipus, keses, datetime.now().strftime("%H:%M:%S")]
            sheet.append_row(uj_sor_h)
            st.error("Hiba rögzítve!")

# --- 4. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Gyors Kalkulátor (Lidl Standard)")
    st.info("15% kockázati pufferrel számolva.")
    
    netto = st.number_input("Nettó becsült összeg (Ft)", min_value=0, value=100000)
    puffer = netto * 0.15
    brutto = netto + puffer
    
    col1, col2 = st.columns(2)
    col1.metric("Puffer (15%)", f"{puffer:,.0f} Ft".replace(",", " "))
    col2.metric("Mindösszesen", f"{brutto:,.0f} Ft".replace(",", " "))
    
    st.write("---")
    st.write("📋 **Projekt Protokoll:** 5% anyagveszteség és 20% időbeli ráhagyás javasolt.")






