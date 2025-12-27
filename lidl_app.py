import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime
from fpdf import FPDF  # fpdf2 könyvtár használata

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
page = st.sidebar.radio("Menü", ["📊 Műszerfal", "📝 Napi jelentés", "⚠️ Hiba jelentése", "💰 Kalkulátor", "📄 Dokumentum generáló"])

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
            uj_sor_h = [[str(datum_h), fazis_h, "", "", "Igen", tipus, ora, datetime.now().strftime("%H:%M:%S")]]
            sheet.append_rows(uj_sor_h, value_input_option='USER_ENTERED', table_range='A1:H1')
            st.error(f"Hiba rögzítve!")

# --- 4. KALKULÁTOR ---
elif page == "💰 Kalkulátor":
    st.title("💰 Intelligens Kötbér Kalkulátor")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            hibak = df[df['Hiba történt-e'] == 'Igen'].copy()
            hibak['Késés órában'] = pd.to_numeric(hibak['Késés órában'], errors='coerce').fillna(0)
            osszes_ora = hibak['Késés órában'].sum()
            
            st.metric("Összesített késés", f"{osszes_ora} óra")
            oradij = st.number_input("Kötbér (Ft/óra)", value=15000)
            st.error(f"Kötbér összege: {osszes_ora * oradij:,.0f} Ft".replace(",", " "))

# --- 5. DOKUMENTUM GENERÁLÓ (STABIL VERZIÓ) ---
elif page == "📄 Dokumentum generáló":
    st.title("📄 Jegyzőkönyv exportálása")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            hibak = df[df['Hiba történt-e'] == 'Igen']
            
            if not hibak.empty:
                # Esemény kiválasztása
                valasztas = st.selectbox("Válassz ki egy eseményt:", 
                                         hibak.index, 
                                         format_func=lambda x: f"{hibak.loc[x, 'Dátum']} - {hibak.loc[x, 'Munkaszakasz']}")
                
                if st.button("PDF Jegyzőkönyv Generálása"):
                    hiba_adat = hibak.loc[valasztas]
                    
                    # PDF objektum létrehozása
                    pdf = FPDF()
                    pdf.add_page()
                    
                    # Címsor
                    pdf.set_font("Helvetica", 'B', 16)
                    pdf.cell(0, 10, "LIDL PROJEKT - SZALLITASI JEGYZOKONYV", align='C')
                    pdf.ln(20)
                    
                    # Adatok
                    pdf.set_font("Helvetica", size=12)
                    pdf.cell(0, 10, f"Datum: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
                    pdf.cell(0, 10, f"Helyszin: Lidl Projekt Munkaterulet", ln=True)
                    pdf.ln(10)
                    
                    # Szöveg összeállítása ékezetek nélkül a hiba elkerülése végett
                    leiras = (f"A bejegyzett hiba tipusa: {hiba_adat['Hiba típusa']}. "
                              f"A munkaszakasz: {hiba_adat['Munkaszakasz']}. "
                              f"A keses merteke: {hiba_adat['Késés órában']} ora.")
                    
                    # Ékezetmentesítés (biztonsági játék)
                    def clean_text(text):
                        replacements = {'á':'a','é':'e','í':'i','ó':'o','ö':'o','ő':'o','ú':'u','ü':'u','ű':'u',
                                        'Á':'A','É':'E','Í':'I','Ó':'O','Ö':'O','Ő':'O','Ú':'U','Ü':'U','Ű':'U'}
                        for k, v in replacements.items():
                            text = text.replace(k, v)
                        return text

                    pdf.multi_cell(0, 10, clean_text(leiras))
                    pdf.ln(20)
                    pdf.cell(0, 10, "..........................................", ln=True)
                    pdf.cell(0, 10, "Alairas (Ani-Roll Kft.)", ln=True)
                    
                    # PDF mentése változóba
                    try:
                        pdf_bytes = pdf.output() # fpdf2 esetén ez byte-okat ad vissza
                        
                        st.download_button(
                            label="📥 PDF Letöltése",
                            data=pdf_bytes,
                            file_name=f"jegyzokonyv_{hiba_adat['Dátum']}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Hiba a PDF generálása közben: {e}")
            else:
                st.warning("Nincs rögzített hiba a táblázatban.")









