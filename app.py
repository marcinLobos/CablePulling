import streamlit as st
import pandas as pd
import math

# --- KONFIGURACJA ---
st.set_page_config(page_title="Pull-Planner Max Pro", layout="wide")

# --- FUNKCJA DARK MODE ---
def zastosuj_motyw(wybrany_motyw):
    if wybrany_motyw == "Dark":
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
        "prosta": "Odcinek prosty",
        "luk": "Łuk (Zakręt)",
        "promien": "Promień łuku",
        "bezpiecznie": "✅ Wynik bezpieczny",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "jednostki": "System jednostek:",
        "kable": "🔌 Kable w kanale",
        "trasa": "🛤️ Planowanie Trasy",
        "dodaj": "Dodaj",
        "wyczysc": "Wyczyść",
        "tarcie": "Współczynnik tarcia (μ)",
        "rura": "📏 Geometria Osłony (D)",
        "analiza": "📊 Analiza Techniczna",
        "jam_error": "🚨 RYZYKO ZAKLINOWANIA!",
        "swp": "Nacisk boczny (SWP)"
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
        "wyczysc": "Clear",
        "tarcie": "Friction (μ)",
        "rura": "📏 Conduit Geometry (D)",
        "analiza": "📊 Technical Analysis",
        "jam_error": "🚨 JAMMING RISK!",
        "swp": "Sidewall Pressure (SWP)"
    }
}

# --- SIDEBAR (USTAWIENIA) ---
with st.sidebar:
    jezyk = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[jezyk]
    
    st.divider()
    motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"])
    zastosuj_motyw(motyw)
    
    st.header("⚙️ Ustawienia")
    wybrany_sys = st.radio(txt["jednostki"], ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    if "kN" in wybrany_sys:
        j_sila = "kN"; m_N = 1000.0; m_ekr = 0.001; g = 9.81; u_len = "m"
    elif "lb" in wybrany_sys:
        j_sila = "lb"; m_N = 1.0; m_ekr = 1.0; g = 1.0; u_len = "ft"
    else:
        j_sila = "N"; m_N = 1.0; m_ekr = 1.0; g = 9.81; u_len = "m"

    mu = st.slider(txt["tarcie"], 0.1, 0.6, 0.35)
    limit_uzytkownika = st.number_input(f"Limit ({j_sila})", value=10.0 if j_sila=="kN" else 5000.0)
    limit_N = limit_uzytkownika * m_N

    st.header(txt["rura"])
    D_wew = st.number_input("Średnica wewn. rury D", value=100.0)

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

# --- INTERFEJS GŁÓWNY & ANALIZA ---
st.title(txt["tytul"])

if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    jam_ratio = D_wew / max_d
    c1, c2 = st.columns(2)
    c1.metric("Jam Ratio", round(jam_ratio, 2))
    c2.metric(f"Clearance ({u_len})", round(D_wew - max_d, 1))
    if 2.8 <= jam_ratio <= 3.2: st.error(txt["jam_error"])

# --- TRASA ---
if 'trasa' not in st.session_state: st.session_state.trasa = []
st.subheader(txt["trasa"])
col1, col2, col3 = st.columns([2, 2, 3])
with col1: typ = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
with col2: val = st.number_input("Długość/Kąt", value=10.0)
with col3:
    if typ == txt["prosta"]:
        tryb_n = st.radio("Jedn.:", ["°", "%"], horizontal=True)
        nachylenie = st.number_input("Wartość", value=0.0)
        promien = 0.0
    else:
        promien = st.number_input(txt["promien"], value=1.0)
        nachylenie, tryb_n = 0.0, "°"

if st.button(f"➕ {txt['dodaj']} odcinek"):
    st.session_state.trasa.append({"typ": typ, "val": val, "slope": nachylenie, "s_mode": tryb_n, "r": promien})

# --- OBLICZENIA ---
if st.session_state.trasa:
    naciag_N = 0.0
    num_k = len(st.session_state.kable)
    waga_total = sum([k['w'] for k in st.session_state.kable]) if num_k > 0 else 0.0
    
    # Wyznaczanie Weight Correction (wc) - Cradle Configuration
    wc = 1.0
    if num_k >= 3 and D_wew > max_d:
        ratio = D_wew / max_d
        wc = 1 + (4/3) * (1 / (ratio - 1))**2

    wyniki = []
    for i, s in enumerate(st.session_state.trasa):
        t_in = naciag_N
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
    
    final_ekr = naciag_N * m_ekr
    if naciag_N > limit_N: st.error(f"{txt['alarm']} ({round(final_ekr, 2)} {j_sila})")
    else: st.success(f"{txt['bezpiecznie']} ({round(final_ekr, 2)} {j_sila})")

    if st.button(f"🗑️ {txt['wyczysc']} (t)"): 
        st.session_state.trasa = []; st.rerun()