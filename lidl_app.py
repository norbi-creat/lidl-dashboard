import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime
from fpdf import FPDF

# --- BOLT LISTA (KÓD + NÉV) ---
BOLTOK = {
    "1245": "Miskolc - József Attila u.",
    "2133": "Budapest - Bajcsy-Zsilinszky út",
    "0988": "Debrecen - Derék utca",
    "3341": "Győr - Tihanyi Árpád út"
}

# --- JELSZÓ VÉDELEM (Változatlan) ---
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
page = st.sidebar.radio("Menü", ["📊 Műszerfal", "📝 Napi jelentés", "⚠️ Hiba jelentése", "💰 Kalkulátor", "📄 Dokumentum generáló"])

# Oldalsáv Bolt kód választó
st.sidebar.write("---")
kod_valasztas = st.sidebar.selectbox("Válassz Bolt kódot:", list(BOLTOK.keys()), format_func=lambda x: f"{x} - {BOLTOK[x]}")

# --- 1. MŰSZERFAL (Szűrés Bolt kódra) ---
if page == "📊 Műszerfal":
    st.title(f"🏗️ Projekt: {kod_valasztas} ({BOLTOK[kod_valasztas]})")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            # Szűrés a Bolt kód oszlopra (A oszlop)
            df_szurt = df[df['Bolt kód'] == kod_valasztas]
            
            if not df_szurt.empty:
                st.dataframe(df_szurt.tail(20), use_container_width=True)
            else:
                st.info(f"A(z) {kod_valasztas} kódszámú bolthoz még nincs adat.")

# --- 2. NAPI JELENTÉS ---
elif page == "📝 Napi jelentés":
    st.title("📝 Napi Jelentés")
    with st.form("napi_form"):
        u_bolt_kod = st.selectbox("Bolt kód", list(BOLTOK.keys()), format_func=lambda x: f"{x} - {BOLTOK[x]}")
        datum = st.date_input("Dátum", datetime.now())
        fazis = st.selectbox("Munka", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        letszam = st.number_input("Létszám", min_value=1, value=4)
        leiras = st.text_area("Leírás")
        submit_napi = st.form_submit_button("Mentés")
        
        if submit_napi:
            # 9 oszlop: A(Bolt kód), B(Dátum), C(Szakasz), D(Létszám), E(Leírás), F(Hiba), G(Típus), H(Késés), I(Idő)
            uj_sor = [[u_bolt_kod, str(datum), fazis, letszam, leiras, "Nem", "-", 0, datetime.now().strftime("%H:%M:%S")]]
            sheet.append_rows(uj_sor, value_input_option='USER_ENTERED', table_range='A1:I1')
            st.success(f"Mentve a {u_bolt_kod} bolthoz!")

# --- 3. HIBA JELENTÉSE ---
elif page == "⚠️ Hiba jelentése":
    st.title("⚠️ Hiba rögzítése")
    with st.form("hiba_form"):
        u_bolt_kod = st.selectbox("Bolt kód", list(BOLTOK.keys()), format_func=lambda x: f"{x} - {BOLTOK[x]}")
        datum_h = st.date_input("Dátum", datetime.now())
        fazis_h = st.selectbox("Hol?", ["Földmunka", "Zsaluzás", "Vasszerelés", "Betonozás", "Egyéb"])
        tipus = st.selectbox("Típus", ["Logisztikai", "Műszaki", "Időjárás"])
        ora = st.number_input("Késés (óra)", min_value=0.0)
        submit_hiba = st.form_submit_button("Hiba rögzítése")
        
        if submit_hiba:
            uj_sor_h = [[u_bolt_kod, str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]]
            sheet.append_rows(uj_sor_h, value_input_option='USER_ENTERED', table_range='A1:I1')
            st.error(f"Hiba rögzítve a {u_bolt_kod} bolt esetén!")

# --- 4. KALKULÁTOR (Bolt kód szűréssel) ---
elif page == "💰 Kalkulátor":
    st.title(f"💰 Kötbér kalkuláció: {kod_valasztas}")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            hibak = df[(df['Bolt kód'] == kod_valasztas) & (df['Hiba történt-e'] == 'Igen')].copy()
            
            hibak['Késés órában'] = pd.to_numeric(hibak['Késés órában'], errors='coerce').fillna(0)
            osszes_ora = hibak['Késés órában'].sum()
            
            st.metric(f"Összes késés ({kod_valasztas})", f"{osszes_ora} óra")
            oradij = st.number_input("Kötbér (Ft/óra)", value=15000)
            st.error(f"Kötbér összege: {osszes_ora * oradij:,.0f} Ft".replace(",", " "))

# --- 5. DOKUMENTUM GENERÁLÓ ---
elif page == "📄 Dokumentum generáló":
    st.title("📄 Jegyzőkönyv generálás")
    if sheet:
        data = sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        hibak = df[(df['Bolt kód'] == kod_valasztas) & (df['Hiba történt-e'] == 'Igen')]
        
        if not hibak.empty:
            valasztas = st.selectbox("Válassz eseményt:", hibak.index, 
                                     format_func=lambda x: f"{hibak.loc[x, 'Dátum']} - {hibak.loc[x, 'Munkaszakasz']}")
            
            if st.button("PDF Jegyzőkönyv Generálása"):
                h_adat = hibak.loc[valasztas]
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, f"JEGYZOKONYV - BOLT KOD: {h_adat['Bolt kód']}", align='C', ln=True)
                pdf.ln(10)
                pdf.set_font("Helvetica", size=12)
                pdf.cell(0, 10, f"Bolt: {BOLTOK.get(h_adat['Bolt kód'], 'Ismeretlen')}", ln=True)
                pdf.cell(0, 10, f"Datum: {h_adat['Dátum']}", ln=True)
                pdf.ln(10)
                szoveg = f"A {h_adat['Munkaszakasz']} fázisban fellépő hiba típusa: {h_adat['Hiba típusa']}. Késés: {h_adat['Késés órában']} óra."
                # Ékezetmentesítés a biztonságért
                pdf.multi_cell(0, 10, szoveg.replace('ő','o').replace('ű','u').replace('á','a').replace('é','e').replace('í','i'))
                
                pdf_bytes = bytes(pdf.output())
                st.download_button(label="📥 PDF Jegyzőkönyv Letöltése", data=pdf_bytes, file_name=f"Lidl_{h_adat['Bolt kód']}_jkv.pdf", mime="application/pdf")










