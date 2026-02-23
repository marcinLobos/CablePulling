import streamlit as st
import pandas as pd
import math

# --- 1. KONFIGURACJA I STAN SESJI ---
st.set_page_config(page_title="Pull-Planner v3.4", layout="wide")

# Inicjalizacja stanów, aby uniknąć resetowania przy przełączaniu widżetów
if 'motyw' not in st.session_state: st.session_state.motyw = "Light"
if 'kable' not in st.session_state: st.session_state.kable = []
if 'trasa' not in st.session_state: st.session_state.trasa = []

# --- 2. FUNKCJA DARK MODE (CSS) ---
def zastosuj_motyw():
    if st.session_state.motyw == "Dark":
        st.markdown("""<style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span { color: #ffffff !important; }
            .stTable { background-color: #1d2129; color: #ffffff; }
            div[data-testid="stMetricValue"] > div { color: #ffffff !important; }
            </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- 3. SŁOWNIK JĘZYKOWY ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Profesjonalny Planer Naciągu Kabli (v3.4)",
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
        "tytul": "⚡ Professional Cable Pull-Planner (v3.4)",
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
    
    # Wybór motywu z przypisaniem do session_state
    st.session_state.motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"], value=st.session_state.motyw)
    zastosuj_motyw() # Wywołanie po każdej zmianie
    
    st.header(txt["jednostki"])
    wybrany_sys = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    if "kN" in wybrany_sys:
        j_sila, m_N, m_ekr, g, u_len = "kN", 1000.0, 0.001, 9.81, "m"
    elif "lb" in wybrany_sys:
        j_sila, m_N, m_ekr, g, u_len = "lb", 1.0, 1.0, 1.0, "ft"
    else:
        j_sila, m_N, m_ekr, g, u_len = "N", 1.0, 1.0, 9.81, "m"

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
    c_d = st.number_input("Średnica kabla d (mm)", value=30.0)
    c_w = st.number_input(f"Waga ({u_len})", value=1.0)
    if st.button(f"➕ {txt['dodaj']} kabel"): st.session_state.kable.append({"d": c_d, "w": c_w})
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {txt['wyczysc']} kable"): st.session_state.kable = []; st.rerun()

# --- 5. INTERFEJS GŁÓWNY ---
st.title(txt["tytul"])
if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    jam_ratio = D_wew / max_d
    c1, c2 = st.columns(2)
    c1.metric("Jam Ratio", round(jam_ratio, 2))
    c2.metric("Clearance", f"{round(H_wew - max_d, 1)} mm")
    if typ_oslony == txt["o_rura"] and 2.8 <= jam_ratio <= 3.2: st.error(txt["jam_error"])

# --- 6. TRASA ---
st.subheader(txt["trasa"])
col1, col2, col3 = st.columns([2, 2, 3])
with col1: 
    typ_label = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
    typ_id = "straight" if typ_label == txt["prosta"] else "bend"
with col2: val_odc = st.number_input(f"{txt['wartosc']}", value=10.0)
with col3:
    if typ_id == "straight":
        t_nach = st.radio("Jedn.:", ["°", "%"], horizontal=True)
        nach = st.number_input("Nachylenie", value=0.0)
        r_luk = 0.0
    else:
        r_luk = st.number_input(txt["promien"], value=1.0)
        nach, t_nach = 0.0, "°"

if st.button(f"➕ {txt['dodaj']} element"):
    st.session_state.trasa.append({"id": typ_id, "val": val_odc, "slope": nach, "s_mode": t_nach, "r": r_luk})

# --- 7. OBLICZENIA ---
if st.session_state.trasa:
    naciag_N = t_pocz * m_N
    num_k = len(st.session_state.kable)
    waga_total = sum([k['w'] for k in st.session_state.kable])
    
    wc = 1.0 # Weight Correction Factor
    if typ_oslony == txt["o_rura"] and num_k >= 3:
        wc = 1 + (4/3) * (1 / ((D_wew / max_d) - 1))**2

    wyniki_tab = []
    total_L = 0.0
    for i, s in enumerate(st.session_state.trasa):
        if s["id"] == "straight":
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s['slope']/100)
            naciag_N += s["val"] * waga_total * g * (mu * wc * math.cos(theta) + math.sin(theta))
            swp, total_L, display_typ = 0.0, total_L + s["val"], txt["prosta"]
        else:
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc * phi)
            swp = (naciag_N / s["r"]) if s["r"] > 0 else 0.0
            total_L, display_typ = total_L + (phi * s["r"]), txt["luk"]
        
        naciag_N = max(0, naciag_N)
        wyniki_tab.append({"#": i+1, "Typ": display_typ, txt["wartosc"]: s["val"], f"{txt['naciag']} [{j_sila}]": round(naciag_N * m_ekr, 3), f"{txt['swp']} [{j_sila}/{u_len}]": round(swp * m_ekr, 2)})

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