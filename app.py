import streamlit as st
import pandas as pd
import math

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Pull-Planner v4.4",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INICJALIZACJA STANU SESJI ---
if 'motyw' not in st.session_state:
    st.session_state.motyw = "Dark"
if 'kable' not in st.session_state:
    st.session_state.kable = []
if 'trasa' not in st.session_state:
    st.session_state.trasa = []

# --- 3. KOMPLEKSOWY CSS (DARK MODE & UI FIXES) ---
def zastosuj_stylizacje():
    if st.session_state.motyw == "Dark":
        st.markdown("""
            <style>
            /* Główny kontener */
            .stApp { 
                background-color: #0e1117; 
                color: #ffffff; 
            }
            [data-testid="stSidebar"] { 
                background-color: #1d2129; 
            }
            
            /* Naprawa Selectbox (List Rozwijanych) */
            div[data-baseweb="select"] > div {
                background-color: #1d2129 !important;
                color: #ffffff !important;
                border: 1px solid #444 !important;
            }
            div[data-baseweb="popover"] ul {
                background-color: #1d2129 !important;
                color: #ffffff !important;
                border: 1px solid #444 !important;
            }
            div[data-baseweb="popover"] li {
                color: #ffffff !important;
            }
            div[data-baseweb="popover"] li:hover {
                background-color: #3d4452 !important;
            }
            
            /* Stylizacja tabel */
            .stTable { 
                border: 1px solid #444 !important; 
                background-color: #1d2129; 
            }
            .stTable td, .stTable th { 
                border: 1px solid #555 !important; 
                color: #ffffff !important;
                padding: 10px !important;
            }
            
            /* Teksty i etykiety */
            .stMarkdown, .stText, p, h1, h2, h3, span, label, li { 
                color: #ffffff !important; 
            }
            
            /* Metryki */
            div[data-testid="stMetricValue"] > div { 
                color: #00ffcc !important; 
            }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- 4. SŁOWNIK TŁUMACZEŃ (PEŁNY) ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Profesjonalny Planer Naciągu Kabli (v4.4)",
        "motyw": "Motyw wizualny:",
        "naciag": "Naciąg",
        "prosta": "Odcinek prosty",
        "luk": "Łuk / Zakręt / Kolano",
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
        "custom": "Własny kąt (wpisz...)",
        "dodaj": "Dodaj element",
        "wyczysc": "Wyczyść dane"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner (v4.4)",
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
        "kat_wybor": "Select elbow angle:",
        "custom": "Custom angle (type...)",
        "dodaj": "Add element",
        "wyczysc": "Clear data"
    }
}

# --- 5. SIDEBAR (USTAWIENIA) ---
with st.sidebar:
    lang = st.radio("Language / Język:", ["PL", "EN"], horizontal=True)
    t = TLUMACZENIA[lang]
    st.divider()
    
    st.session_state.motyw = st.select_slider(
        t["motyw"], 
        options=["Light", "Dark"], 
        value=st.session_state.motyw
    )
    zastosuj_stylizacje()
    
    st.header("System jednostek")
    u_sys = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    if "kN" in u_sys:
        j_sila, m_N, m_ekr, g, u_len = "kN", 1000.0, 0.001, 9.81, "m"
    elif "lb" in u_sys:
        j_sila, m_N, m_ekr, g, u_len = "lb", 1.0, 1.0, 1.0, "ft"
    else:
        j_sila, m_N, m_ekr, g, u_len = "N", 1.0, 1.0, 9.81, "m"

    st.header(t["oslona"])
    typ_o = st.radio("Typ osłony:", [t["o_rura"], t["o_kanal"]])
    if typ_o == t["o_rura"]:
        D_in = st.number_input("Średnica wewn. D (mm)", value=100.0)
        H_in = D_in
    else:
        W_in = st.number_input("Szerokość W (mm)", value=200.0)
        H_in = st.number_input("Wysokość H (mm)", value=100.0)
        D_in = 999.0

    st.header(t["kable"])
    c_diam = st.number_input("Średnica kabla (mm)", value=30.0)
    c_weight = st.number_input(f"Waga kabla ({u_len})", value=1.0)
    
    if st.button(f"➕ {t['dodaj']} kabel"):
        st.session_state.kable.append({"d": c_diam, "w": c_weight})
    
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {t['wyczysc']} kable"):
            st.session_state.kable = []
            st.rerun()

    st.divider()
    mu_val = st.slider("Współczynnik tarcia (μ)", 0.1, 0.6, 0.35)
    t_drum = st.number_input(f"Naciąg bębna ({j_sila})", value=0.0)
    lim_val = st.number_input(f"Limit ({j_sila})", value=5000.0 if "N" == j_sila else 10.0)
    limit_N = lim_val * m_N

# --- 6. PANEL ANALIZY ---
st.title(t["tytul"])
wc_factor = 1.0

if st.session_state.kable:
    st.subheader(t["analiza"])
    max_d_cab = max([k['d'] for k in st.session_state.kable])
    jam_r = D_in / max_d_cab
    
    if typ_o == t["o_rura"] and len(st.session_state.kable) >= 3:
        wc_factor = 1 + (4/3) * (1 / ((D_in / max_d_cab) - 1))**2
    
    ma, mb, mc = st.columns(3)
    ma.metric("Jam Ratio", round(jam_r, 2))
    mb.metric("Clearance", f"{round(H_in - max_d_cab, 1)} mm")
    mc.metric("WC Factor", round(wc_factor, 3))
    
    if typ_o == t["o_rura"] and 2.8 <= jam_r <= 3.2:
        st.error("🚨 UWAGA: Ryzyko zaklinowania kabli (Jam Ratio ok. 3.0)!")

# --- 7. PROJEKT TRASY ---
st.subheader(t["trasa"])
r1, r2, r3 = st.columns([2, 3, 3])

with r1:
    v_type = st.selectbox("Element", [t["prosta"], t["luk"]])
    t_id = "straight" if v_type == t["prosta"] else "bend"

with r2:
    if t_id == "straight":
        v_len_angle = st.number_input(f"Długość ({u_len})", value=10.0)
    else:
        opcje_lego = ["15°", "30°", "45°", "60°", "90°", t["custom"]]
        v_choice = st.selectbox(t["kat_wybor"], opcje_lego, index=4)
        if v_choice == t["custom"]:
            v_len_angle = st.number_input("Kąt (stopnie °)", value=22.5)
        else:
            v_len_angle = float(v_choice.replace("°", ""))

with r3:
    if t_id == "straight":
        n_unit = st.radio("Nachylenie:", ["%", "°"], horizontal=True)
        n_val = st.number_input("Wartość", value=0.0)
        r_bend = 0.0
    else:
        r_bend = st.number_input(f"{t['promien']} ({u_len})", value=1.0)
        n_val, n_unit = 0.0, "%"

if st.button(f"➕ {t['dodaj']} element"):
    st.session_state.trasa.append({
        "id": t_id, 
        "val": v_len_angle, 
        "slope": n_val, 
        "sl_mode": n_unit, 
        "r": r_bend
    })

# --- 8. OBLICZENIA I TABELA ---
if st.session_state.trasa:
    naciag_N = t_drum * m_N
    w_total = sum([k['w'] for k in st.session_state.kable]) if st.session_state.kable else 0.0
    sum_L = 0.0
    tablica_wynikowa = []

    for i, step in enumerate(st.session_state.trasa):
        if step["id"] == "straight":
            # Formuła dla odcinka prostego
            rad_slope = math.radians(step["slope"]) if step["sl_mode"] == "°" else math.atan(step['slope']/100)
            naciag_N += step["val"] * w_total * g * (mu_val * wc_factor * math.cos(rad_slope) + math.sin(rad_slope))
            real_L, swp_val, d_name = step["val"], 0.0, t["prosta"]
        else:
            # Formuła dla łuku
            rad_bend = math.radians(step["val"])
            naciag_N *= math.exp(mu_val * wc_factor * rad_bend)
            swp_val = (naciag_N / step["r"]) if step["r"] > 0 else 0.0
            real_L, d_name = (rad_bend * step["r"]), f"{t['luk']} ({step['val']}°)"
        
        naciag_N = max(0, naciag_N)
        sum_L += real_L
        
        tablica_wynikowa.append({
            "#": i+1,
            "Typ": d_name,
            t["l_rzecz"]: f"{round(real_L, 2)} {u_len}",
            f"{t['naciag']} [{j_sila}]": round(naciag_N * m_ekr, 3),
            f"SWP [{j_sila}/{u_len}]": round(swp_val * m_ekr, 2)
        })

    st.table(pd.DataFrame(tablica_wynikowa))
    st.divider()
    
    f1, f2 = st.columns(2)
    f1.metric("Całkowita długość", f"{round(sum_L, 2)} {u_len}")
    f2.metric("Naciąg końcowy", f"{round(naciag_N * m_ekr, 2)} {j_sila}")

    if naciag_N > limit_N:
        st.error(t["alarm"])
    else:
        st.success(t["bezpiecznie"])

    if st.button(f"🗑️ {t['wyczysc']} trasę"):
        st.session_state.trasa = []
        st.rerun()