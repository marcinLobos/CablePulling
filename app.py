import streamlit as st
import pandas as pd
import math

# --- KONFIGURACJA ---
st.set_page_config(page_title="Pull-Planner v3.0", layout="wide")

# --- FUNKCJA DARK MODE ---
def zastosuj_motyw(tryb):
    if tryb == "Dark":
        st.markdown("""<style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span { color: #ffffff !important; }
            </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- SŁOWNIK JĘZYKOWY ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Planer Przeciągania Kabli - Wersja Profesjonalna",
        "motyw": "Motyw wizualny:",
        "naciag": "Naciąg",
        "naciag_pocz": "Naciąg początkowy (bęben)",
        "prosta": "Odcinek prosty",
        "luk": "Łuk (Zakręt)",
        "promien": "Promień łuku",
        "bezpiecznie": "✅ Wynik bezpieczny",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "jednostki": "System jednostek:",
        "kable": "🔌 Kable w osłonie",
        "trasa": "🛤️ Planowanie Trasy",
        "dodaj": "Dodaj",
        "wyczysc": "Wyczyść",
        "tarcie": "Współczynnik tarcia (μ)",
        "oslona": "📏 Typ i Geometria Osłony",
        "o_rura": "Rura okrągła",
        "o_kanal": "Kanał prostokątny",
        "analiza": "📊 Analiza Techniczna",
        "swp": "Nacisk boczny (SWP)"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner Pro",
        "motyw": "Visual Theme:",
        "naciag": "Tension",
        "naciag_pocz": "Initial Tension (drum)",
        "prosta": "Straight section",
        "luk": "Bend",
        "promien": "Bend Radius",
        "bezpiecznie": "✅ Safe Result",
        "alarm": "❌ LIMIT EXCEEDED!",
        "jednostki": "Unit system:",
        "kable": "🔌 Cable list",
        "trasa": "🛤️ Route Planning",
        "dodaj": "Add",
        "wyczysc": "Clear",
        "tarcie": "Friction (μ)",
        "oslona": "📏 Conduit Type & Geometry",
        "o_rura": "Round Conduit",
        "o_kanal": "Rectangular Duct",
        "analiza": "📊 Technical Analysis",
        "swp": "Sidewall Pressure (SWP)"
    }
}

# --- SIDEBAR ---
with st.sidebar:
    jezyk = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[jezyk]
    
    st.divider()
    motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"])
    zastosuj_motyw(motyw)
    
    st.header("⚙️ Ustawienia")
    wybrany_sys = st.radio(txt["jednostki"], ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    if "kN" in wybrany_sys:
        j_sila = "kN"; m_na_N = 1000.0; m_ekr = 0.001; g = 9.81; u_len = "m"
    elif "lb" in wybrany_sys:
        j_sila = "lb"; m_na_N = 1.0; m_ekr = 1.0; g = 1.0; u_len = "ft"
    else:
        j_sila = "N"; m_na_N = 1.0; m_ekr = 1.0; g = 9.81; u_len = "m"

    mu = st.slider(txt["tarcie"], 0.1, 0.6, 0.35)
    t_start_uzyt = st.number_input(f"{txt['naciag_pocz']} ({j_sila})", value=0.0)
    limit_uzytkownika = st.number_input(f"Limit ({j_sila})", value=10.0 if j_sila=="kN" else 5000.0)
    limit_N = limit_uzytkownika * m_na_N

    st.header(txt["oslona"])
    typ_oslony = st.radio("Typ:", [txt["o_rura"], txt["o_kanal"]])
    if typ_oslony == txt["o_rura"]:
        D_wew = st.number_input("Średnica wewn. D", value=100.0)
        H_wew = D_wew
    else:
        W_wew = st.number_input("Szerokość (W)", value=200.0)
        H_wew = st.number_input("Wysokość (H)", value=100.0)
        D_wew = 9999 # Wyłączamy Jam Ratio

    st.header(txt["kable"])
    if 'kable' not in st.session_state: st.session_state.kable = []
    c_d = st.number_input("Średnica kabla d", value=30.0)
    c_w = st.number_input(f"Waga ({u_len})", value=1.5)
    if st.button(f"➕ {txt['dodaj']} kabel"):
        st.session_state.kable.append({"d": c_d, "w": c_w})
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {txt['wyczysc']} (k)"): 
            st.session_state.kable = []; st.rerun()

# --- ANALIZA TECHNICZNA ---
st.title(txt["tytul"])
if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    col1, col2 = st.columns(2)
    if typ_oslony == txt["o_rura"]:
        jam_ratio = D_wew / max_d
        col1.metric("Jam Ratio", round(jam_ratio, 2))
        if 2.8 <= jam_ratio <= 3.2: st.error("🚨 RYZYKO ZAKLINOWANIA (Jamming)!")
    col2.metric(f"Prześwit / Clearance ({u_len})", round(H_wew - max_d, 1))

# --- TRASA ---
if 'trasa' not in st.session_state: st.session_state.trasa = []
st.subheader(txt["trasa"])
c1, c2, c3 = st.columns([2, 2, 3])
with c1: typ = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
with c2: val = st.number_input("Długość/Kąt", value=10.0)
with c3:
    if typ == txt["prosta"]:
        tryb_n = st.radio("Jedn.:", ["°", "%"], horizontal=True)
        nachylenie = st.number_input("Wartość (+/-)", value=0.0)
        promien = 0.0
    else:
        promien = st.number_input(txt["promien"], value=1.0)
        nachylenie, tryb_n = 0.0, "°"

if st.button(f"➕ {txt['dodaj']} odcinek"):
    st.session_state.trasa.append({"typ": typ, "val": val, "slope": nachylenie, "s_mode": tryb_n, "r": promien})

# --- OBLICZENIA ---
if st.session_state.trasa:
    naciag_N = t_start_uzyt * m_na_N
    num_k = len(st.session_state.kable)
    waga_total = sum([k['w'] for k in st.session_state.kable])
    
    wc = 1.0 # Weight Correction
    if typ_oslony == txt["o_rura"] and num_k >= 3:
        wc = 1 + (4/3) * (1 / ((D_wew / max_d) - 1))**2

    wyniki = []
    for i, s in enumerate(st.session_state.trasa):
        if s["typ"] == txt["prosta"]:
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s['slope']/100)
            naciag_N += s["val"] * waga_total * g * (mu * wc * math.cos(theta) + math.sin(theta))
            swp = 0.0
        else:
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc * phi)
            swp = (naciag_N / s["r"]) if s["r"] > 0 else 0.0
        
        naciag_N = max(0, naciag_N)
        wyniki.append({
            "#": i+1, "Typ": s["typ"], 
            f"{txt['naciag']} [{j_sila}]": round(naciag_N * m_ekr, 3),
            f"{txt['swp']} [{j_sila}/{u_len}]": round(swp * m_ekr, 2)
        })

    st.table(pd.DataFrame(wyniki))
    f_ekr = naciag_N * m_ekr
    if naciag_N > limit_N: st.error(f"{txt['alarm']} ({round(f_ekr, 2)} {j_sila})")
    else: st.success(f"{txt['bezpiecznie']} ({round(f_ekr, 2)} {j_sila})")
    if st.button(f"🗑️ {txt['wyczysc']} (trasa)"): 
        st.session_state.trasa = []; st.rerun()