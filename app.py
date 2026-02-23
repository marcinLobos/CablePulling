import streamlit as st
import pandas as pd
import math

# --- FUNKCJE POMOCNICZE ---
def get_weight_correction(d, D, mode):
    if mode == "Single":
        return 1.0
    ratio = D / d
    if mode == "Cradle": # Układ płaski/luźny
        return 1 + (4/3) * (1 / (ratio - 1))**2
    if mode == "Triangular": # Układ ciasny
        return 1 / math.sqrt(1 - (1 / (ratio - 1))**2)
    return 1.0

# --- INTERFEJS ---
st.set_page_config(page_title="Inżynierski Pull-Planner", layout="wide")
st.title("⚡ Profesjonalny Kalkulator Naciągu Kabli")

with st.sidebar:
    st.header("📏 Geometria Osłony")
    conduit_type = st.radio("Typ osłony:", ["Rura okrągła", "Kanał prostokątny"])
    
    if conduit_type == "Rura okrągła":
        D = st.number_input("Średnica wewn. rury D (mm)", value=100.0)
        H, W = None, None
    else:
        W = st.number_input("Szerokość kanału W (mm)", value=200.0)
        H = st.number_input("Wysokość kanału H (mm)", value=100.0)
        D = None

    st.header("🔌 Parametry Kabla")
    d = st.number_input("Średnica pojedynczego kabla d (mm)", value=30.0)
    w = st.number_input("Waga jednostkowa (kg/m)", value=1.5)
    n_cables = st.selectbox("Liczba kabli", [1, 3])
    
    if n_cables == 3 and conduit_type == "Rura okrągła":
        config = st.selectbox("Układ kabli", ["Cradle", "Triangular"])
    else:
        config = "Single"

    mu = st.slider("Współczynnik tarcia (μ)", 0.1, 0.6, 0.35)
    max_t = st.number_input("Max. dopuszczalny naciąg (N)", value=5000)

# --- ANALIZA GEOMETRII ---
st.subheader("📋 Analiza możliwości montażu")
col_a, col_b = st.columns(2)

if conduit_type == "Rura okrągła":
    jam_ratio = D / d
    jam_color = "red" if 2.8 <= jam_ratio <= 3.2 else "green"
    col_a.metric("Jam Ratio", round(jam_ratio, 2), delta_color="inverse")
    if 2.8 <= jam_ratio <= 3.2:
        st.error("⚠️ RYZYKO ZAKLINOWANIA! Jam Ratio w krytycznym zakresie 2.8 - 3.2.")
else:
    col_a.info("Kanał prostokątny: Brak ryzyka klinowania (Jam Ratio nie dotyczy).")

# --- OBLICZENIA TRASY ---
st.subheader("🛤️ Definicja trasy")
if 'route' not in st.session_state: st.session_state.route = []

c1, c2, c3 = st.columns(3)
with c1: s_type = st.selectbox("Typ", ["Prosta", "Łuk"])
with c2: s_val = st.number_input("Długość (m) / Kąt (°)", value=10.0)
with c3: s_rad = st.number_input("Promień łuku (m)", value=1.0 if s_type == "Łuk" else 0.0)

if st.button("➕ Dodaj sekcję"):
    st.session_state.route.append({"type": s_type, "val": s_val, "rad": s_rad})

# Wyliczanie naciągu
if st.session_state.route:
    wc = get_weight_correction(d, D if D else 1000, config)
    current_t = 0.0
    summary = []
    
    for i, s in enumerate(st.session_state.route):
        t_in = current_t
        if s['type'] == "Prosta":
            t_out = t_in + (s['val'] * w * n_cables * 9.81 * mu * wc)
            swp = 0
        else:
            phi = math.radians(s['val'])
            t_out = t_in * math.exp(mu * wc * phi)
            swp = t_out / s['rad'] if s['rad'] > 0 else 0
        
        current_t = t_out
        summary.append({
            "Odcinek": i+1, "Typ": s['type'], "Naciąg [N]": round(t_out, 1), "SWP [N/m]": round(swp, 1)
        })

    st.table(pd.DataFrame(summary))
    if current_t > max_t:
        st.error(f"❌ Przekroczono naciąg! Wynik: {round(current_t)} N")
    else:
        st.success(f"✅ Bezpiecznie. Naciąg końcowy: {round(current_t)} N")