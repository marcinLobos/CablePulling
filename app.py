import streamlit as st
import pandas as pd
import math

# --- KONFIGURACJA ---
st.set_page_config(page_title="Pull-Planner v3.2", layout="wide")

# --- DARK MODE CSS ---
def zastosuj_motyw(tryb):
    if tryb == "Dark":
        st.markdown("""<style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span { color: #ffffff !important; }
            .stTable { background-color: #1d2129; color: #ffffff; }
            </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- SŁOWNIK JĘZYKOWY (Z PRZYWRÓCONYM TARCIEM) ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Profesjonalny Planer Naciągu Kabli (v3.2)",
        "motyw": "Motyw wizualny:",
        "naciag": "Naciąg",
        "naciag_pocz": "Naciąg z bębna (początkowy)",
        "prosta": "Odcinek prosty",
        "luk": "Łuk / Zakręt",
        "promien": "Promień łuku (R)",
        "bezpiecznie": "✅ WYNIK W NORMIE",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "jednostki": "System miar:",
        "kable": "🔌 Konfiguracja Kabli",
        "trasa": "🛤️ Projekt Trasy",
        "oslona": "📏 Parametry Osłony",
        "o_rura": "Rura okrągła",
        "o_kanal": "Kanał (Duct)",
        "analiza": "📊 Raport Techniczny",
        "jam_error": "🚨 KRYTYCZNE RYZYKO ZAKLINOWANIA!",
        "swp": "Nacisk boczny (SWP)",
        "podsumowanie": "📈 Podsumowanie projektu",
        "tarcie": "Współczynnik tarcia (μ)",
        "dodaj": "Dodaj",
        "wyczysc": "Wyczyść"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner (v3.2)",
        "motyw": "Theme:",
        "naciag": "Tension",
        "naciag_pocz": "Drum Tension (initial)",
        "prosta": "Straight section",
        "luk": "Bend",
        "promien": "Bend Radius (R)",
        "bezpiecznie": "✅ WITHIN LIMITS",
        "alarm": "❌ LIMIT EXCEEDED!",
        "jednostki": "Units:",
        "kable": "🔌 Cable Configuration",
        "trasa": "🛤️ Route Design",
        "oslona": "📏 Conduit Parameters",
        "o_rura": "Round Conduit",
        "o_kanal": "Rectangular Duct",
        "analiza": "📊 Technical Report",
        "jam_error": "🚨 CRITICAL JAMMING RISK!",
        "swp": "Sidewall Pressure (SWP)",
        "podsumowanie": "📈 Project Summary",
        "tarcie": "Friction coefficient (μ)",
        "dodaj": "Add",
        "wyczysc": "Clear"
    }
}

# --- SIDEBAR ---
with st.sidebar:
    jezyk = st.radio("Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[jezyk]
    st.divider()
    motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"])
    zastosuj_motyw(motyw)
    
    st.header(txt["jednostki"])
    wybrany_sys = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    if "kN" in wybrany_sys:
        j_sila = "kN"; m_N = 1000.0; m_ekr = 0.001; g = 9.81; u_len = "m"
    elif "lb" in wybrany_sys:
        j_sila = "lb"; m_N = 1.0; m_ekr = 1.0; g = 1.0; u_len = "ft"
    else:
        j_sila = "N"; m_N = 1.0; m_ekr = 1.0; g = 9.81; u_len = "m"

    mu = st.slider(txt["tarcie"], 0.1, 0.6, 0.35)
    t_pocz = st.number_input(f"{txt['naciag_pocz']} ({j_sila})", value=0.0)
    limit_uzyt = st.number_input(f"Limit ({j_sila})", value=10.0 if j_sila=="kN" else 5000.0)
    limit_N = limit_uzyt * m_N

    st.header(txt["oslona"])
    typ_oslony = st.radio("Typ:", [txt["o_rura"], txt["o_kanal"]])
    if typ_oslony == txt["o_rura"]:
        D_wew = st.number_input("Średnica wewn. D (mm)", value=100.0)
        H_wew = D_wew
    else:
        W_wew = st.number_input("Szerokość W (mm)", value=200.0)
        H_wew = st.number_input("Wysokość H (mm)", value=100.0)
        D_wew = 999.0

    st.header(txt["kable"])
    if 'kable' not in st.session_state: st.session_state.kable = []
    c_d = st.number_input("Średnica kabla d (mm)", value=30.0)
    c_w = st.number_input(f"Waga ({u_len})", value=1.5)
    if st.button(f"➕ {txt['dodaj']} kabel"): st.session_state.kable.append({"d": c_d, "w": c_w})
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {txt['wyczysc']} kable"): st.session_state.kable = []; st.rerun()

# --- INTERFEJS GŁÓWNY ---
st.title(txt["tytul"])
if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    jam_ratio = D_wew / max_d
    c1, c2 = st.columns(2)
    c1.metric("Jam Ratio", round(jam_ratio, 2))
    c2.metric("Clearance", f"{round(H_wew - max_d, 1)} mm")
    if typ_oslony == txt["o_rura"] and 2.8 <= jam_ratio <= 3.2: st.error(txt["jam_error"])

# --- TRASA ---
if 'trasa' not in st.session_state: st.session_state.trasa = []
st.subheader(txt["trasa"])
col1, col2, col3 = st.columns([2, 2, 3])
with col1: typ_odc = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
with col2: val_odc = st.number_input("Dł. / Kąt", value=10.0)
with col3:
    if typ_odc == txt["prosta"]:
        t_nach = st.radio("Jedn.:", ["°", "%"], horizontal=True)
        nach = st.number_input("Wartość", value=0.0)
        r_luk = 0.0
    else:
        r_luk = st.number_input(txt["promien"], value=1.0)
        nach, t_nach = 0.0, "°"

if st.button(f"➕ {txt['dodaj']} element"):
    st.session_state.trasa.append({"typ": typ_odc, "val": val_odc, "slope": nach, "s_mode": t_nach, "r": r_luk})

# --- OBLICZENIA ---
if st.session_state.trasa:
    naciag_N = t_pocz * m_N
    num_k = len(st.session_state.kable)
    waga_total = sum([k['w'] for k in st.session_state.kable])
    
    wc = 1.0
    if typ_oslony == txt["o_rura"] and num_k >= 3:
        wc = 1 + (4/3) * (1 / ((D_wew / max_d) - 1))**2

    wyniki_tab = []
    total_L = 0.0
    for i, s in enumerate(st.session_state.trasa):
        if s["typ"] == txt["prosta"]:
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s['slope']/100)
            naciag_N += s["val"] * waga_total * g * (mu * wc * math.cos(theta) + math.sin(theta))
            swp = 0.0
            total_L += s["val"]
        else:
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc * phi)
            swp = (naciag_N / s["r"]) if s["r"] > 0 else 0.0
            total_L += (phi * s["r"])
        
        naciag_N = max(0, naciag_N)
        wyniki_tab.append({"#": i+1, "Typ": s["typ"], f"{txt['naciag']} [{j_sila}]": round(naciag_N * m_ekr, 3), f"{txt['swp']} [{j_sila}/{u_len}]": round(swp * m_ekr, 2)})

    st.table(pd.DataFrame(wyniki_tab))
    st.subheader(txt["podsumowanie"])
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Długość trasy", f"{round(total_L, 1)} {u_len}")
    sc2.metric("Waga kabli", f"{round(waga_total, 2)}")
    sc3.metric("WC Factor", round(wc, 3))

    f_ekr = naciag_N * m_ekr
    if naciag_N > limit_N: st.error(f"{txt['alarm']} ({round(f_ekr, 2)} {j_sila})")
    else: st.success(f"{txt['bezpiecznie']} ({round(f_ekr, 2)} {j_sila})")
    if st.button(f"🗑️ {txt['wyczysc']} trasę"): st.session_state.trasa = []; st.rerun()