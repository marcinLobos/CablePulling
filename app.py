import streamlit as st
import pandas as pd
import math

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Pull-Planner Max Pro", layout="wide")

# --- FUNKCJA DARK MODE (Wstrzykiwanie CSS) ---
def zastosuj_motyw(wybrany_motyw):
    if wybrany_motyw == "Dark":
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span { color: #ffffff !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp { background-color: #ffffff; color: #000000; }
            </style>
            """, unsafe_allow_html=True)

# --- SŁOWNIK JĘZYKOWY (Poprawione Tytuły) ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Planer Przeciągania Kabli - Wersja Profesjonalna",
        "motyw": "Motyw wizualny:",
        "naciag": "Naciąg",
        "prosta": "Odcinek prosty",
        "luk": "Łuk (Zakręt)",
        "promien": "Promień łuku",
        "bezpiecznie": "✅ Wynik bezpieczny",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "jednostki": "System jednostek:",
        "kable": "🔌 Kable w kanale",
        "trasa": "🛤️ Planowanie Trasy",
        "dodaj": "Dodaj",
        "wyczysc": "Wyczyść wszystko"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner Pro",
        "motyw": "Visual Theme:",
        "naciag": "Tension",
        "prosta": "Straight section",
        "luk": "Bend",
        "promien": "Bend Radius",
        "bezpiecznie": "✅ Safe Result",
        "alarm": "❌ LIMIT EXCEEDED!",
        "jednostki": "Unit system:",
        "kable": "🔌 Cable list",
        "trasa": "🛤️ Route Planning",
        "dodaj": "Add",
        "wyczysc": "Clear all"
    }
}

# --- SIDEBAR (Ustawienia) ---
with st.sidebar:
    wybrany_jezyk = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[wybrany_jezyk]
    
    st.divider()
    wybrany_motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"])
    zastosuj_motyw(wybrany_motyw)
    
    st.header("⚙️ Ustawienia")
    wybrany_system = st.radio(txt["jednostki"], ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    # Logika jednostek i grawitacji g
    if "kN" in wybrany_system:
        jednostka = "kN"; m_na_N = 1000.0; m_ekran = 0.001; g = 9.81
    elif "lb" in wybrany_system:
        jednostka = "lb"; m_na_N = 1.0; m_ekran = 1.0; g = 1.0
    else:
        jednostka = "N"; m_na_N = 1.0; m_ekran = 1.0; g = 9.81

    limit_uzytkownika = st.number_input(f"Limit ({jednostka})", value=10.0 if jednostka=="kN" else 5000.0)
    limit_N = limit_uzytkownika * m_na_N

    st.header(txt["kable"])
    if 'kable' not in st.session_state: st.session_state.kable = []
    c_d = st.number_input("Średnica (mm/in)", value=30.0)
    c_w = st.number_input("Waga (kg/m / lb/ft)", value=1.5)
    if st.button(f"➕ {txt['dodaj']} kabel"):
        st.session_state.kable.append({"d": c_d, "w": c_w})
    if st.session_state.kable and st.button(f"🗑️ {txt['wyczysc']} (kable)"):
        st.session_state.kable = []

# --- INTERFEJS GŁÓWNY ---
st.title(txt["tytul"])

if 'trasa' not in st.session_state: st.session_state.trasa = []

st.subheader(txt["trasa"])
c1, c2, c3 = st.columns([2, 2, 3])
with c1: 
    typ = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
with c2: 
    val = st.number_input("Długość (m) / Kąt (°)", value=10.0)
with c3:
    if typ == txt["prosta"]:
        tryb_n = st.radio("Jednostka:", ["°", "%"], horizontal=True)
        nachylenie = st.number_input("Wartość (+ góra, - dół)", value=0.0)
        promien = 0.0
    else:
        promien = st.number_input(txt["promien"], value=1.0)
        nachylenie, tryb_n = 0.0, "°"

if st.button(f"➕ {txt['dodaj']} odcinek"):
    st.session_state.trasa.append({"typ": typ, "val": val, "slope": nachylenie, "s_mode": tryb_n, "r": promien})

# --- OBLICZENIA I TABELA ---
if st.session_state.trasa:
    naciag_N = 0.0
    waga_total = sum([k['w'] for k in st.session_state.kable]) if st.session_state.kable else 1.5
    mu, wc = 0.35, 1.0
    
    wyniki_tabela = []
    for i, s in enumerate(st.session_state.trasa):
        if s["typ"] == txt["prosta"]:
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s['slope']/100)
            naciag_N += s["val"] * waga_total * g * (mu * wc * math.cos(theta) + math.sin(theta))
        else:
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc * phi)
        
        naciag_N = max(0, naciag_N)
        wyniki_tabela.append({
            "#": i+1, 
            "Typ": s["typ"], 
            f"{txt['naciag']} [{jednostka}]": round(naciag_N * m_ekran, 3)
        })

    st.table(pd.DataFrame(wyniki_tabela))
    
    wynik_ekran = naciag_N * m_ekran
    if naciag_N > limit_N:
        st.error(f"{txt['alarm']} ({round(wynik_ekran, 2)} {jednostka})")
    else:
        st.success(f"{txt['bezpiecznie']} ({round(wynik_ekran, 2)} {jednostka})")

    if st.button(f"🗑️ {txt['wyczysc']} (trasa)"):
        st.session_state.trasa = []