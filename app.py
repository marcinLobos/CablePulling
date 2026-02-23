import streamlit as st
import pandas as pd
import math

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Pull-Planner v4.2",
    layout="wide"
)

# --- 2. STAN SESJI (PAMIĘĆ SYSTEMU) ---
if 'motyw' not in st.session_state:
    st.session_state.motyw = "Light"
if 'kable' not in st.session_state:
    st.session_state.kable = []
if 'trasa' not in st.session_state:
    st.session_state.trasa = []

# --- 3. CSS DLA TRYBU CIEMNEGO ---
def zastosuj_stylizacje():
    if st.session_state.motyw == "Dark":
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span, label, li { color: #ffffff !important; }
            /* Linie tabeli w Dark Mode */
            .stTable { 
                border: 1px solid #444 !important; 
                background-color: #1d2129; 
            }
            .stTable td, .stTable th { 
                border: 1px solid #555 !important; 
                color: #ffffff !important;
                padding: 8px !important;
            }
            div[data-testid="stMetricValue"] > div { color: #00ffcc !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- 4. SŁOWNIK JĘZYKOWY ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Profesjonalny Planer Naciągu Kabli (v4.2)",
        "motyw": "Motyw wizualny:",
        "naciag": "Naciąg",
        "prosta": "Odcinek prosty",
        "luk": "Łuk / Zakręt",
        "promien": "Promień gięcia R",
        "bezpiecznie": "✅ WYNIK W NORMIE",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "kable": "🔌 Konfiguracja Kabli",
        "trasa": "🛤️ Projekt Trasy",
        "oslona": "📏 Parametry Osłony",
        "o_rura": "Rura okrągła",
        "o_kanal": "Kanał (Duct)",
        "analiza": "📊 Analiza Techniczna",
        "swp": "Nacisk boczny (SWP)",
        "l_rzecz": "Długość rzeczywista",
        "kat_wybor": "Kąt kształtki:",
        "custom": "Inny (wpisz...)",
        "dodaj": "Dodaj element",
        "wyczysc": "Wyczyść listę"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner (v4.2)",
        "motyw": "Visual Theme:",
        "naciag": "Tension",
        "prosta": "Straight section",
        "luk": "Bend / Elbow",
        "promien": "Bend Radius R",
        "bezpiecznie": "✅ WITHIN LIMITS",
        "alarm": "❌ LIMIT EXCEEDED!",
        "kable": "🔌 Cable Configuration",
        "trasa": "🛤️ Route Design",
        "oslona": "📏 Conduit Parameters",
        "o_rura": "Round Conduit",
        "o_kanal": "Rectangular Duct",
        "analiza": "📊 Technical Analysis",
        "swp": "Sidewall Pressure (SWP)",
        "l_rzecz": "Real Length",
        "kat_wybor": "Elbow angle:",
        "custom": "Custom (type...)",
        "dodaj": "Add element",
        "wyczysc": "Clear list"
    }
}

# --- 5. SIDEBAR (USTAWIENIA) ---
with st.sidebar:
    wybor_jezyka = st.radio("Language / Język:", ["PL", "EN"], horizontal=True)
    t = TLUMACZENIA[wybor_jezyka]
    
    st.session_state.motyw = st.select_slider(t["motyw"], options=["Light", "Dark"], value=st.session_state.motyw)
    zastosuj_stylizacje()
    
    st.header("System jednostek")
    sys_u = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    if "kN" in sys_u:
        j_sila, m_N, m_ekr, g, u_len = "kN", 1000.0, 0.001, 9.81, "m"
    elif "lb" in sys_u:
        j_sila, m_N, m_ekr, g, u_len = "lb", 1.0, 1.0, 1.0, "ft"
    else:
        j_sila, m_N, m_ekr, g, u_len = "N", 1.0, 1.0, 9.81, "m"

    st.header(t["oslona"])
    typ_oslony = st.radio("Typ:", [t["o_rura"], t["o_kanal"]])
    if typ_oslony == t["o_rura"]:
        D_wew = st.number_input("Średnica D (mm)", value=100.0)
        H_wew = D_wew
    else:
        W_wew = st.number_input("Szerokość W (mm)", value=200.0)
        H_wew = st.number_input("Wysokość H (mm)", value=100.0)
        D_wew = 999.0

    st.header(t["kable"])
    c_d = st.number_input("Średnica d (mm)", value=30.0)
    c_w = st.number_input(f"Waga ({u_len})", value=1.0)
    if st.button(f"➕ {t['dodaj']} kabel"):
        st.session_state.kable.append({"d": c_d, "w": c_w})
    
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {t['wyczysc']} kable"):
            st.session_state.kable = []
            st.rerun()

    st.divider()
    mu = st.slider("Współczynnik tarcia (μ)", 0.1, 0.6, 0.35)
    t_pocz = st.number_input(f"Naciąg bębna ({j_sila})", value=0.0)
    limit_val = st.number_input(f"Limit ({j_sila})", value=10.0 if "kN" in j_sila else 5000.0)
    limit_N = limit_val * m_N

# --- 6. GŁÓWNY PANEL I ANALIZA ---
st.title(t["tytul"])
wc_factor = 1.0

if st.session_state.kable:
    st.subheader(t["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    jam_ratio = D_wew / max_d
    if typ_oslony == t["o_rura"] and len(st.session_state.kable) >= 3:
        wc_factor = 1 + (4/3) * (1 / ((D_wew / max_d) - 1))**2
    
    ca, cb, cc = st.columns(3)
    ca.metric("Jam Ratio", round(jam_ratio, 2))
    cb.metric("Clearance", f"{round(H_wew - max_d, 1)} mm")
    cc.metric("WC Factor", round(wc_factor, 3))

# --- 7. PROJEKT TRASY ---
st.subheader(t["trasa"])
col1, col2, col3 = st.columns([2, 3, 3])

with col1:
    wybor_typu = st.selectbox("Typ elementu", [t["prosta"], t["luk"]])
    typ_id = "straight" if wybor_typu == t["prosta"] else "bend"

with col2:
    if typ_id == "straight":
        v_odc = st.number_input(f"Długość odcinka ({u_len})", value=10.0)
    else:
        opcje = ["15°", "30°", "45°", "60°", "90°", t["custom"]]
        wyb_k = st.selectbox(t["kat_wybor"], opcje, index=4)
        if wyb_k == t["custom"]:
            v_odc = st.number_input("Wpisz kąt (°)", value=22.5)
        else:
            v_odc = float(wyb_k.replace("°", ""))

with col3:
    if typ_id == "straight":
        m_nach = st.radio("Jednostka:", ["%", "°"], horizontal=True)
        nachylenie = st.number_input("Wartość", value=0.0)
        r_promien = 0.0
    else:
        r_promien = st.number_input(f"{t['promien']} ({u_len})", value=1.0)
        nachylenie, m_nach = 0.0, "%"

if st.button(f"➕ {t['dodaj']} do trasy"):
    st.session_state.trasa.append({"id": typ_id, "val": v_odc, "slope": nachylenie, "sl_mode": m_nach, "r": r_promien})

# --- 8. OBLICZENIA KOŃCOWE ---
if st.session_state.trasa:
    naciag_N = t_pocz * m_N
    w_suma = sum([k['w'] for k in st.session_state.kable]) if st.session_state.kable else 0.0
    total_L = 0.0
    dane_tabeli = []

    for i, s in enumerate(st.session_state.trasa):
        if s["id"] == "straight":
            theta = math.radians(s["slope"]) if s["sl_mode"] == "°" else math.atan(s['slope']/100)
            naciag_N += s["val"] * w_suma * g * (mu * wc_factor * math.cos(theta) + math.sin(theta))
            r_l, swp, d_t = s["val"], 0.0, t["prosta"]
        else:
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc_factor * phi)
            swp = (naciag_N / s["r"]) if s["r"] > 0 else 0.0
            r_l, d_t = (phi * s["r"]), f"{t['luk']} ({s['val']}°)"
        
        naciag_N = max(0, naciag_N)
        total_L += r_l
        dane_tabeli.append({
            "#": i+1, "Typ": d_t, t["l_rzecz"]: f"{round(r_l, 2)} {u_len}",
            f"{t['naciag']} [{j_sila}]": round(naciag_N * m_ekr, 3), f"{t['swp']}": round(swp * m_ekr, 2)
        })

    st.table(pd.DataFrame(dane_tabeli))
    st.divider()
    
    r1, r2 = st.columns(2)
    r1.metric("Długość całkowita", f"{round(total_L, 2)} {u_len}")
    r2.metric("Naciąg końcowy", f"{round(naciag_N * m_ekr, 2)} {j_sila}")

    if naciag_N > limit_N:
        st.error(t["alarm"])
    else:
        st.success(t["bezpiecznie"])

    if st.button(f"🗑️ {t['wyczysc']} trasę"):
        st.session_state.trasa = []
        st.rerun()