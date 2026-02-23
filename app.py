import streamlit as st
import pandas as pd
import math

# =================================================================
# 1. KONFIGURACJA STRONY I ŚRODOWISKA
# =================================================================
st.set_page_config(
    page_title="Pull-Planner v4.6 Professional",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================================================================
# 2. INICJALIZACJA STANU SESJI (PAMIĘĆ SYSTEMU)
# =================================================================
if 'motyw' not in st.session_state:
    st.session_state.motyw = "Dark"

if 'kable' not in st.session_state:
    st.session_state.kable = []

if 'trasa' not in st.session_state:
    st.session_state.trasa = []

# =================================================================
# 3. KOMPLEKSOWY CSS (NAPRAWA DARK MODE DLA LIST I TABEL)
# =================================================================
def zastosuj_stylizacje_premium():
    if st.session_state.motyw == "Dark":
        st.markdown("""
            <style>
            /* Główny kontener aplikacji */
            .stApp { 
                background-color: #0e1117; 
                color: #ffffff; 
            }
            
            /* Sidebar (Panel Boczny) */
            [data-testid="stSidebar"] { 
                background-color: #1d2129; 
            }
            
            /* Naprawa List Rozwijanych (Selectbox) - Tło i Tekst */
            div[data-baseweb="select"] > div {
                background-color: #1d2129 !important;
                color: #ffffff !important;
                border: 1px solid #444 !important;
            }
            
            /* Naprawa Listy po otwarciu (Popover) */
            div[data-baseweb="popover"] ul {
                background-color: #1d2129 !important;
                color: #ffffff !important;
                border: 1px solid #444 !important;
            }
            
            /* Elementy listy przy najechaniu myszką */
            div[data-baseweb="popover"] li:hover {
                background-color: #3d4452 !important;
            }
            
            /* Stylizacja tabel wyników */
            .stTable { 
                border: 1px solid #444 !important; 
                background-color: #1d2129; 
            }
            
            .stTable td, .stTable th { 
                border: 1px solid #555 !important; 
                color: #ffffff !important;
                padding: 12px !important;
            }
            
            /* Naprawa tekstów i etykiet */
            .stMarkdown, .stText, p, h1, h2, h3, span, label, li { 
                color: #ffffff !important; 
            }
            
            /* Metryki wyników (wyróżnienie kolorem) */
            div[data-testid="stMetricValue"] > div { 
                color: #00ffcc !important; 
            }
            
            /* Pola tekstowe i numeryczne */
            div[data-baseweb="input"] {
                background-color: #1d2129 !important;
                color: white !important;
            }
            /* Naprawa widoczności tekstu na przyciskach w Dark Mode */
          div.stButton > button {
            background-color: #1d2129 !important; /* Tło takie jak sidebar */
            color: #ffffff !important;           /* Zawsze biały tekst */
            border: 1px solid #444444 !important; /* Dyskretna ramka */
            border-radius: 4px;
            transition: all 0.2s ease-in-out;
        }

            div.stButton > button:hover {
                background-color: #2c313c !important; /* Delikatne rozjaśnienie przy najechaniu */
                color: #00ffcc !important;           /* Tylko tekst dostaje akcent morski */
                border: 1px solid #00ffcc !important; /* Cienka morska obwoluta */
                box-shadow: 0px 0px 10px rgba(0, 255, 204, 0.2); /* Subtelna poświata zamiast jaskrawości */
            }

            /* Fix dla napisu, o który pytałeś - wymuszenie widoczności */
             div.stButton > button p {
            color: #ffffff !important;
            }


            [data-testid="collapsedControl"] {
            color: #00ffcc !important;
            background-color: rgba(0, 255, 204, 0.1) !important;
            border-radius: 0 10px 10px 0 !important;
            }

            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-color: #ffffff; color: #000000; }</style>""", unsafe_allow_html=True)

# =================================================================
# 4. SŁOWNIK TŁUMACZEŃ (PL / EN)
# =================================================================
TLUMACZENIA = {
    "PL": {
        "tytul": "⚡ Planer Naciągu Kabli 3D (v4.6)",
        "kable": "🔌 Konfiguracja Kabli",
        "trasa": "🛤️ Projekt Trasy",
        "oslona": "📏 Parametry Osłony",
        "o_rura": "Rura okrągła",
        "o_kanal": "Kanał (Duct)",
        "analiza": "📊 Analiza Techniczna",
        "swp": "Nacisk boczny (SWP)",
        "l_rzecz": "Dł. rzeczywista",
        "naciag": "Naciąg",
        "prosta": "Odcinek prosty",
        "luk": "Łuk / Kolano",
        "plaszczyzna": "Płaszczyzna (kierunek):",
        "poz": "Poziomo",
        "dol": "Pionowo w dół (Dociąża)",
        "gora": "Pionowo w górę (Odciąża)",
        "dodaj": "Dodaj do projektu",
        "wyczysc": "Wyczyść wszystko",
        "limit": "Limit bezpieczeństwa"
    },
    "EN": {
        "tytul": "⚡ 3D Cable Pull-Planner (v4.6)",
        "kable": "🔌 Cable Configuration",
        "trasa": "🛤️ Route Design",
        "oslona": "📏 Conduit Parameters",
        "o_rura": "Round Pipe",
        "o_kanal": "Rectangular Duct",
        "analiza": "📊 Technical Analysis",
        "swp": "Sidewall Pressure (SWP)",
        "l_rzecz": "Real Length",
        "naciag": "Tension",
        "prosta": "Straight section",
        "luk": "Bend / Elbow",
        "plaszczyzna": "Plane (Direction):",
        "poz": "Horizontal",
        "dol": "Vertical Down (Added load)",
        "gora": "Vertical Up (Lightened)",
        "dodaj": "Add to project",
        "wyczysc": "Clear all",
        "limit": "Safety limit"
    }
}

# =================================================================
# 5. PANEL BOCZNY (SIDEBAR) - WEJŚCIE DANYCH
# =================================================================
with st.sidebar:
    # Wybór języka
    jezyk_wybor = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA[jezyk_wybor]
    
    st.divider()
    
    # Przełącznik motywu
    st.session_state.motyw = st.select_slider(
        "Motyw:", 
        options=["Light", "Dark"], 
        value=st.session_state.motyw
    )
    zastosuj_stylizacje_premium()
    
    # Wybór jednostek
    st.header("Jednostki")
    sys_miar = st.radio("", ["Metric (N)", "Metric (kN)", "USA (lb)"])
    if "kN" in sys_miar:
        j_sila, m_N, m_ekran, g, u_dl = "kN", 1000.0, 0.001, 9.81, "m"
    elif "lb" in sys_miar:
        j_sila, m_N, m_ekran, g, u_dl = "lb", 1.0, 1.0, 1.0, "ft"
    else:
        j_sila, m_N, m_ekran, g, u_dl = "N", 1.0, 1.0, 9.81, "m"

    # Parametry osłony
    st.header(txt["oslona"])
    typ_oslony = st.radio("Typ:", [txt["o_rura"], txt["o_kanal"]])
    D_wewn = st.number_input("Średnica wewn. (mm)", value=100.0)
    if typ_oslony == txt["o_kanal"]:
        W_wewn = st.number_input("Szerokość (mm)", value=200.0)
    
    # Dodawanie kabli
    st.header(txt["kable"])
    c_d = st.number_input("Średnica d (mm)", value=30.0)
    c_w = st.number_input(f"Waga ({u_dl})", value=1.0)
    
    if st.button(f"➕ {txt['dodaj']} kabel"):
        st.session_state.kable.append({"d": c_d, "w": c_w})
    
    if st.session_state.kable:
        st.table(pd.DataFrame(st.session_state.kable))
        if st.button("🗑️ Usuń kable"):
            st.session_state.kable = []
            st.rerun()

    # Współczynniki tarcia i limity
    st.divider()
    mu_f = st.slider("Wsp. tarcia (μ)", 0.1, 0.6, 0.35)
    t_start = st.number_input(f"Naciąg pocz. ({j_sila})", value=0.0)
    t_limit = st.number_input(f"Limit ({j_sila})", value=10.0 if "kN" in j_sila else 5000.0)

# =================================================================
# 6. PANEL GŁÓWNY - ANALIZA I PROJEKT
# =================================================================
st.title(txt["tytul"])

# Obliczenia pomocnicze (WC Factor i Jam Ratio)
wc_factor = 1.0
if st.session_state.kable:
    st.subheader(txt["analiza"])
    max_d_kabla = max([k['d'] for k in st.session_state.kable])
    jam_r = D_wewn / max_d_kabla
    
    # Wzór na Weight Correction Factor (dla 3+ kabli w rurze)
    if typ_oslony == txt["o_rura"] and len(st.session_state.kable) >= 3:
        wc_factor = 1 + (4/3) * (1 / ((D_wewn / max_d_kabla) - 1))**2
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Jam Ratio", round(jam_r, 2))
    col_b.metric("Weight Factor", round(wc_factor, 3))
    col_b.metric("Clearance", f"{round(D_wewn - max_d_kabla, 1)} mm")

# Dodawanie elementów trasy
st.subheader(txt["trasa"])
r1, r2, r3 = st.columns([2, 3, 3])

with r1:
    typ_el = st.selectbox("Element", [txt["prosta"], txt["luk"]])
    t_id = "straight" if typ_el == txt["prosta"] else "bend"

with r2:
    if t_id == "straight":
        v_size = st.number_input(f"Długość ({u_dl})", value=10.0)
        v_dir = txt["poz"]
    else:
        v_size = st.selectbox("Kąt kształtki", ["15°", "30°", "45°", "60°", "90°", "Inny"])
        if v_size == "Inny":
            v_size = st.number_input("Wpisz kąt (°)", value=22.5)
        else:
            v_size = float(v_size.replace("°", ""))
        v_dir = st.selectbox(txt["plaszczyzna"], [txt["poz"], txt["dol"], txt["gora"]])

with r3:
    if t_id == "straight":
        nach_val = st.number_input("Nachylenie (%)", value=0.0)
        r_bend = 0.0
    else:
        r_bend = st.number_input(f"Promień R ({u_dl})", value=1.0)
        nach_val = 0.0

if st.button(f"➕ {txt['dodaj']} element trasy"):
    st.session_state.trasa.append({
        "id": t_id, 
        "val": v_size, 
        "slope": nach_val, 
        "r": r_bend, 
        "plane": v_dir
    })

# =================================================================
# 7. OBLICZENIA KOŃCOWE (SILNIK FIZYCZNY)
# =================================================================
if st.session_state.trasa:
    naciag_N = t_start * m_N
    suma_wag = sum([k['w'] for k in st.session_state.kable])
    suma_L = 0.0
    tabela_wynikow = []

    for i, krok in enumerate(st.session_state.trasa):
        if krok["id"] == "straight":
            # Odcinek prosty (uwzględnia kąt nachylenia)
            theta = math.atan(krok["slope"] / 100)
            naciag_N += krok["val"] * suma_wag * g * (mu_f * wc_factor * math.cos(theta) + math.sin(theta))
            d_rzecz, swp_val, opis = krok["val"], 0.0, txt["prosta"]
        else:
            # Łuk (uwzględnia płaszczyznę gięcia)
            phi = math.radians(krok["val"])
            
            # Siła dociągu grawitacyjnego (waga efektywna)
            if krok["plane"] == txt["dol"]:
                # Kabel dociśnięty przez grawitację
                w_eff = math.sqrt((naciag_N/krok["r"])**2 + (suma_wag*g*math.cos(phi))**2) + (suma_wag*g*math.sin(phi))
                naciag_N += mu_f * wc_factor * w_eff * (krok["r"] * phi)
            elif krok["plane"] == txt["gora"]:
                # Kabel podrywany przez grawitację
                w_eff = math.sqrt((naciag_N/krok["r"])**2 + (suma_wag*g*math.cos(phi))**2) - (suma_wag*g*math.sin(phi))
                naciag_N += mu_f * wc_factor * w_eff * (krok["r"] * phi)
            else:
                # Standardowy łuk poziomy (Capstan Equation)
                naciag_N *= math.exp(mu_f * wc_factor * phi)
            
            d_rzecz = phi * krok["r"]
            swp_val = naciag_N / krok["r"] if krok["r"] > 0 else 0.0
            opis = f"{txt['luk']} {krok['val']}° ({krok['plane']})"

        naciag_N = max(0, naciag_N)
        suma_L += d_rzecz
        
        tabela_wynikow.append({
            "#": i+1,
            "Typ": opis,
            txt["l_rzecz"]: f"{round(d_rzecz, 2)} {u_dl}",
            f"{txt['naciag']} [{j_sila}]": round(naciag_N * m_ekran, 3),
            f"SWP [{j_sila}/{u_dl}]": round(swp_val * m_ekran, 2)
        })

    # Wyświetlanie wyników
    st.table(pd.DataFrame(tabela_wynikow))
    st.divider()
    
    col1, col2 = st.columns(2)
    col1.metric("Długość trasy", f"{round(suma_L, 2)} {u_dl}")
    col2.metric("Naciąg końcowy", f"{round(naciag_N * m_ekran, 2)} {j_sila}")

    if naciag_N > (t_limit * m_N):
        st.error(txt["alarm"])
    else:
        st.success("✅ Naciąg w dopuszczalnej normie.")

    if st.button("🗑️ Wyczyść projekt trasy"):
        st.session_state.trasa = []
        st.rerun()

# =================================================================
# 8. STOPKA SYSTEMOWA
# =================================================================
st.caption(f"Mike-OS v4.6 Ready. System state: Stable. Gravity engine: Active.")