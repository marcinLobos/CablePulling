import streamlit as st
import pandas as pd
import math

# --- 1. KONFIGURACJA I STAN SESJI ---
st.set_page_config(page_title="Pull-Planner v3.5", layout="wide")

if 'motyw' not in st.session_state: st.session_state.motyw = "Light"
if 'kable' not in st.session_state: st.session_state.kable = []
if 'trasa' not in st.session_state: st.session_state.trasa = []

# --- 2. FUNKCJA DARK MODE (Z POPRAWIONĄ SIATKĄ TABELI) ---
def zastosuj_motyw():
    if st.session_state.motyw == "Dark":
        st.markdown("""<style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span, label { color: #ffffff !important; }
            /* Wyraźne linie tabeli w Dark Mode */
            .stTable { 
                border: 1px solid #444 !important; 
                background-color: #1d2129; 
            }
            .stTable td, .stTable th { 
                border: 1px solid #444 !important; 
                color: #ffffff !important;
            }
            div[data-testid="stMetricValue"] > div { color: #ffffff !important; }
            </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- 3. SŁOWNIK JĘZYKOWY ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Profesjonalny Planer Naciągu Kabli (v3.5)",
        "motyw": "Motyw wizualny:",
        "naciag": "Naciąg",
        "naciag_pocz": "Naciąg początkowy (bęben)",
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
        "wyczysc": "Wyczyść",
        "wartosc": "Dł. / Kąt"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner (v3.5)",
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
        "wyczysc": "Clear",
        "wartosc": "Len. / Angle"
    }
}

# --- 4. SIDEBAR ---
with st.sidebar:
    jezyk = st.radio("Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[jezyk]
    st.divider()
    st.session_state.motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"], value=st.session_state.motyw)
    zastosuj_motyw()
    
    st.header(txt["jednostki"])
    sys = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    if "kN" in sys: j_sila, m_N, m_ekr, g, u_len = "kN", 1000.0, 0.001, 9.81, "m"
    elif "lb" in sys: j_sila, m_N, m_ekr, g, u_len = "lb", 1.0, 1.0, 1.0, "ft"
    else: j_sila, m_N, m_ekr, g, u_len = "N", 1.0, 1.0, 9.81, "m"

    mu = st.slider(txt["tarcie"], 0.1, 0.6, 0.35)
    t_pocz = st.number_input(f"{txt['naciag_pocz']} ({j_sila})", value=0.0)
    limit_N = st.number_input(f"Limit ({j_sila})", value=10.0 if j_sila=="kN" else 5000.0) * m_N

    st.header(txt["oslona"])
    typ_oslony = st.radio("Typ:", [txt["o_rura"], txt["o_kanal"]])
    D_wew = st.number_input("Średnica D (mm)", value=100.0) if typ_oslony == txt["o_rura"] else 999.0
    H_wew = D_wew if typ_oslony == txt["o_rura"] else st.number_input("Wysokość H (mm)", value=100.0)

    st.header(txt["kable"])
    c_d, c_w = st.number_input("Średnica d (mm)", value=30.0), st.number_input(f"Waga ({u_len})", value=1.0)
    if st.button(f"➕ {txt['dodaj']} kabel"): st.session_state.kable.append({"d": c_d, "w": c_w})
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {txt['wyczysc']} kable"): st.session_state.kable = []; st.rerun()

# --- 5. ANALIZA TECHNICZNA ---
st.title(txt["tytul"])
if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    jam = D_wew / max_d
    c1, c2 = st.columns(2)
    c1.metric("Jam Ratio", round(jam, 2))
    c2.metric("Clearance", f"{round(H_wew - max_d, 1)} mm")
    if typ_oslony == txt["o_rura"] and 2.8 <= jam <= 3.2: st.error(txt["jam_error"])

# --- 6. TRASA ---
st.subheader(txt["trasa"])
col1, col2, col3 = st.columns([2, 2, 3])
with col1: 
    typ_label = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
    typ_id = "straight" if typ_label == txt["prosta"] else "bend"
with col2: val_odc = st.number_input(f"{txt['wartosc']}", value=10.0)
with col3:
    if typ_id == "straight":
        t_nach, nach, r_luk = st.radio("Jedn.:", ["°", "%"], horizontal=True), st.number_input("Wartość", value=0.0), 0.0
    else:
        r_luk, nach, t_nach = st.number_input(txt["promien"], value=1.0), 0.0, "°"

if st.button(f"➕ {txt['dodaj']} element"):
    st.session_state.trasa.append({"id": typ_id, "val": val_odc, "slope": nach, "s_mode": t_nach, "r": r_luk})

# --- 7. OBLICZENIA ---
if st.session_state.trasa:
    n_N, total_L = t_pocz * m_N, 0.0
    w_tot = sum([k['w'] for k in st.session_state.kable])
    wc = (1 + (4/3) * (1 / ((D_wew / max_d) - 1))**2) if (typ_oslony == txt["o_rura"] and len(st.session_state.kable) >= 3) else 1.0
    wyniki = []

    for i, s in enumerate(st.session_state.trasa):
        if s["id"] == "straight":
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s['slope']/100)
            n_N += s["val"] * w_tot * g * (mu * wc * math.cos(theta) + math.sin(theta))
            swp, total_L, d_typ = 0.0, total_L + s["val"], txt["prosta"]
        else:
            phi = math.radians(s["val"])
            n_N *= math.exp(mu * wc * phi)
            swp = (n_N / s["r"]) if s["r"] > 0 else 0.0
            total_L, d_typ = total_L + (phi * s["r"]), txt["luk"]
        
        n_N = max(0, n_N)
        wyniki.append({"#": i+1, "Typ": d_typ, txt["wartosc"]: s["val"], f"{txt['naciag']} [{j_sila}]": round(n_N * m_ekr, 3), f"{txt['swp']} [{j_sila}/{u_len}]": round(swp * m_ekr, 2)})

    st.table(pd.DataFrame(wyniki))
    st.subheader(txt["podsumowanie"])
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Długość trasy", f"{round(total_L, 1)} {u_len}")
    sc2.metric("Waga kabli", f"{round(w_tot, 2)}")
    sc3.metric("WC Factor", round(wc, 3))

    if n_N > limit_N: st.error(f"{txt['alarm']} ({round(n_N * m_ekr, 2)} {j_sila})")
    else: st.success(f"{txt['bezpiecznie']} ({round(n_N * m_ekr, 2)} {j_sila})")
    if st.button(f"🗑️ {txt['wyczysc']} trasę"): st.session_state.trasa = []; st.rerun()