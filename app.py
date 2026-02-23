import streamlit as st
import pandas as pd
import math

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Pull-Planner v4.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INICJALIZACJA STANU SESJI (PAMIĘĆ SYSTEMU) ---
if 'motyw' not in st.session_state:
    st.session_state.motyw = "Light"
if 'kable' not in st.session_state:
    st.session_state.kable = []
if 'trasa' not in st.session_state:
    st.session_state.trasa = []

# --- 3. CSS DLA TRYBU CIEMNEGO I TABEL ---
def zastosuj_style():
    if st.session_state.motyw == "Dark":
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stSidebar"] { background-color: #1d2129; }
            .stMarkdown, .stText, p, h1, h2, h3, span, label, li { color: #ffffff !important; }
            /* Wyraźna siatka tabeli */
            .stTable { 
                border: 1px solid #444 !important; 
                background-color: #1d2129; 
            }
            .stTable td, .stTable th { 
                border: 1px solid #555 !important; 
                color: #ffffff !important;
                padding: 10px !important;
            }
            div[data-testid="stMetricValue"] > div { color: #00ffcc !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# --- 4. SŁOWNIK TŁUMACZEŃ ---
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Profesjonalny Planer Naciągu Kabli (v4.0)",
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
        "kat_wybor": "Wybierz kąt kształtki:",
        "custom": "Własny kąt (wpisz...)",
        "dodaj": "Dodaj do projektu",
        "wyczysc": "Wyczyść dane",
        "jednostki": "System miar i jednostek:"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner (v4.0)",
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
        "dodaj": "Add to project",
        "wyczysc": "Clear data",
        "jednostki": "Unit System:"
    }
}

# --- 5. SIDEBAR ---
with st.sidebar:
    jezyk = st.radio("Language / Język:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[jezyk]
    st.divider()
    
    st.session_state.motyw = st.select_slider(txt["motyw"], options=["Light", "Dark"], value=st.session_state.motyw)
    zastosuj_style()
    
    st.header(txt["jednostki"])
    wybrany_sys = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    if "kN" in wybrany_sys:
        j_sila, m_N, m_ekr, g, u_len = "kN", 1000.0, 0.001, 9.81, "m"
    elif "lb" in wybrany_sys:
        j_sila, m_N, m_ekr, g, u_len = "lb", 1.0, 1.0, 1.0, "ft"
    else:
        j_sila, m_N, m_ekr, g, u_len = "N", 1.0, 1.0, 9.81, "m"

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
    if st.button(f"➕ {txt['dodaj']} kabel"):
        st.session_state.kable.append({"d": c_d, "w": c_w})
    
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button(f"🗑️ {txt['wyczysc']} kable"):
            st.session_state.kable = []
            st.rerun()

    st.divider()
    mu = st.slider("Współczynnik tarcia (μ)", 0.1, 0.6, 0.35)
    t_pocz = st.number_input(f"Naciąg bębna ({j_sila})", value=0.0)
    limit_uzyt = st.number_input(f"Limit naciągu ({j_sila})", value=10.0 if "kN" in j_sila else 5000.0)
    limit_N = limit_uzyt * m_N

# --- 6. GŁÓWNY PANEL ANALIZY ---
st.title(txt["tytul"])

if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d = max([k['d'] for k in st.session_state.kable])
    jam_ratio = D_wew / max_d
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Jam Ratio", round(jam_ratio, 2))
    col_b.metric("Clearance", f"{round(H_wew - max_d, 1)} mm")
    
    wc_factor = 1.0
    if typ_oslony == txt["o_rura"] and len(st.session_state.kable) >= 3:
        wc_factor = 1 + (4/3) * (1 / ((D_wew / max_d) - 1))**2
    col_c.metric("Weight Corr. Factor", round(wc_factor, 3))
    
    if typ_oslony == txt["o_rura"] and 2.8 <= jam_ratio <= 3.2:
        st.error("🚨 KRYTYCZNE RYZYKO ZAKLINOWANIA (Jam Ratio ok. 3.0)!")

# --- 7. PROJEKTOWANIE TRASY ---
st.subheader(txt["trasa"])
c1, c2, c3 = st.columns([2, 3, 3])

with c1:
    typ_label = st.selectbox("Typ elementu", [txt["prosta"], txt["luk"]])
    typ_id = "straight" if typ_label == txt["prosta"] else "bend"

with c2:
    if typ_id == "straight":
        v_odc = st.number_input(f"Długość odcinka ({u_len})", value=10.0)
    else:
        opcje = ["15°", "30°", "45°", "60°", "90°", txt["custom"]]
        wyb = st.selectbox(txt["kat_wybor"], opcje, index=4)
        if wyb == txt["custom"]:
            v_odc = st.number_input("Wpisz kąt (stopnie °)", value=22.5)
        else:
            v_odc = float(wyb.replace("°", ""))

with c3:
    if typ_id == "straight":
        tryb_n = st.radio("Jednostka nachylenia:", ["%", "°"], horizontal=True)
        nach = st.number_input("Wartość nachylenia", value=0.0)
        r_luk = 0.0
    else:
        r_luk = st.number_input(f"{txt['promien']} ({u_len})", value=1.0)
        nach, tryb_n = 0.0, "%"

if st.button(f"➕ {txt['dodaj']} element trasy"):
    st.session_state.trasa.append({
        "id": typ_id, "val": v_odc, "slope": nach, 
        "sl_mode": tryb_n, "r": r_luk
    })

# --- 8. OBLICZENIA I TABELA WYNIKÓW ---
if st.session_state.trasa:
    naciag_N = t_pocz * m_N
    suma_wag = sum([k['w'] for k in st.session_state.kable]) if st.session_state.kable else 0.0
    total_L = 0.0
    wyniki_tab = []

    for i, s in enumerate(st.session_state.trasa):
        if s["id"] == "straight":
            # Obliczanie kąta nachylenia
            theta = math.radians(s["slope"]) if s["sl_mode"] == "°" else math.atan(s['slope']/100)
            # Wzór: T2 = T1 + L*W*g*(mu*cos + sin)
            naciag_N += s["val"] * suma_wag * g * (mu * wc_factor * math.cos(theta) + math.sin(theta))
            r_len, swp, d_typ = s["val"], 0.0, txt["prosta"]
        else:
            # Wzór: T2 = T1 * e^(mu*phi)
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc_factor * phi)
            swp = (naciag_N / s["r"]) if s["r"] > 0 else 0.0
            r_len, d_typ = (phi * s["r"]), f"{txt['luk']} ({s['val']}°)"
        
        naciag_N = max(0, naciag_N)
        total_L += r_len
        
        wyniki_tab.append({
            "#": i+1,
            "Typ": d_typ,
            txt["l_rzecz"]: f"{round(r_len, 2)} {u_len}",
            f"{txt['naciag']} [{j_sila}]": round(naciag_N * m_ekr, 3),
            f"{txt['swp']} [{j_sila}/{u_len}]": round(swp * m_ekr, 2)
        })

    st.table(pd.DataFrame(wyniki_tab))
    
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Długość całkowita", f"{round(total_L, 2)} {u_len}")
    res2.metric("Naciąg końcowy", f"{round(naciag_N * m_ekr, 2)} {j_sila}")
    
    if naciag_N > limit_N:
        st.error(f"{txt['alarm']} ({round(naciag_N * m_ekr, 2)} {j_sila} > {limit_uzyt} {j_sila})")
    else:
        st.success(f"{txt['bezpiecznie']} ({round(naciag_N * m_ekr, 2)} {j_sila})")

    if st.button(f"🗑️ {txt['wyczysc']} trasę"):
        st.session_state.trasa = []
        st.rerun()