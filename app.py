import streamlit as st
import pandas as pd
import math

# --- LOGIKA OBLICZENIOWA (Zgodna z Polywater) ---
def get_weight_correction(d, D, n_cables, mode):
    if n_cables == 1:
        return 1.0
    ratio = D / d
    if mode == "Cradle":  # Układ płaski/luźny
        return 1 + (4/3) * (1 / (ratio - 1))**2
    if mode == "Triangular":  # Układ ciasny
        return 1 / math.sqrt(1 - (1 / (ratio - 1))**2)
    return 1.0

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Pull-Planner v2.0", layout="wide")
st.title("⚡ Profesjonalny Kalkulator Przeciągania Kabli")

# --- SIDEBAR: GEOMETRIA I KABLE ---
with st.sidebar:
    st.header("📏 Geometria Osłony")
    conduit_type = st.radio("Typ osłony:", ["Rura okrągła", "Kanał prostokątny"])
    
    if conduit_type == "Rura okrągła":
        D_inner = st.number_input("Średnica wewn. rury D (mm)", value=100.0)
        H_box, W_box = None, None
    else:
        W_box = st.number_input("Szerokość kanału W (mm)", value=200.0)
        H_box = st.number_input("Wysokość kanału H (mm)", value=100.0)
        D_inner = None

    st.divider()
    st.header("🔌 Kable w osłonie")
    if 'cables' not in st.session_state:
        st.session_state.cables = []

    c_d = st.number_input("Średnica kabla (mm)", value=30.0)
    c_w = st.number_input("Waga kabla (kg/m)", value=1.5)
    
    if st.button("➕ Dodaj kabel do listy"):
        st.session_state.cables.append({"d": c_d, "w": c_w})

    if st.session_state.cables:
        st.write("Lista kabli:")
        st.table(pd.DataFrame(st.session_state.cables))
        if st.button("🗑️ Wyczyść kable"):
            st.session_state.cables = []

    st.divider()
    mu = st.slider("Współczynnik tarcia (μ)", 0.1, 0.6, 0.35)
    max_t = st.number_input("Dopuszczalny naciąg (N)", value=5000)

# --- ANALIZA TECHNICZNA (JAM RATIO / FILL) ---
st.subheader("📊 Analiza Zajętości i Bezpieczeństwa")
col1, col2, col3 = st.columns(3)

if st.session_state.cables:
    # Obliczenia przekrojów
    total_cable_area = sum([math.pi * (c['d']**2) / 4 for c in st.session_state.cables])
    if conduit_type == "Rura okrągła":
        conduit_area = math.pi * (D_inner**2) / 4
        # Clearance (Prześwit) wg Polywater
        max_d = max([c['d'] for c in st.session_state.cables])
        clearance = D_inner - max_d
        
        fill_ratio = (total_cable_area / conduit_area) * 100
        col1.metric("Wypełnienie", f"{round(fill_ratio, 1)}%")
        col2.metric("Prześwit (Clearance)", f"{round(clearance, 1)} mm")
        
        # Jam Ratio
        jam = D_inner / max_d
        if 2.8 <= jam <= 3.2:
            st.error(f"🚨 RYZYKO ZAKLINOWANIA! Jam Ratio: {round(jam, 2)}")
        else:
            col3.metric("Jam Ratio", round(jam, 2))
    else:
        box_area = W_box * H_box
        fill_ratio = (total_cable_area / box_area) * 100
        col1.metric("Wypełnienie kanału", f"{round(fill_ratio, 1)}%")
        st.info("Kanał prostokątny: Brak ryzyka Jam Ratio.")

# --- DEFINICJA TRASY I OBLICZENIA ---
st.subheader("🛤️ Planowanie Trasy Przeciągania")
if 'route' not in st.session_state:
    st.session_state.route = []

r1, r2, r3 = st.columns([2, 2, 1])
with r1: r_type = st.selectbox("Typ odcinka", ["Prosta", "Łuk"])
with r2: r_val = st.number_input("Długość (m) / Kąt (°)", value=10.0)
with r3: r_rad = st.number_input("Promień łuku (m)", value=1.0 if r_type == "Łuk" else 0.0)

if st.button("➕ Dodaj odcinek do trasy"):
    st.session_state.route.append({"type": r_type, "val": r_val, "rad": r_rad})

if st.session_state.route:
    # Ustalenie konfiguracji dla ostatniego kabla
    num_c = len(st.session_state.cables)
    config = "Cradle" if num_c >= 3 else "Single"
    wc = get_weight_correction(max_d if num_c > 0 else 1, D_inner if D_inner else 1000, num_c, config) if conduit_type == "Rura okrągła" else 1.0

    current_t = 0.0
    total_weight = sum([c['w'] for c in st.session_state.cables])
    results = []

    for i, step in enumerate(st.session_state.route):
        t_in = current_t
        if step['type'] == "Prosta":
            # T = T_in + L * w * mu * wc
            t_out = t_in + (step['val'] * total_weight * 9.81 * mu * wc)
            swp = 0
        else:
            # T_out = T_in * e^(mu * wc * phi)
            phi = math.radians(step['val'])
            t_out = t_in * math.exp(mu * wc * phi)
            swp = t_out / step['rad'] if step['rad'] > 0 else 0
        
        current_t = t_out
        results.append({
            "Odcinek": i+1,
            "Typ": step['type'],
            "Parametr": f"{step['val']} m" if step['type'] == "Prosta" else f"{step['val']}°",
            "Naciąg Wyj. [N]": round(t_out, 1),
            "Nacisk Boczny [N/m]": round(swp, 1)
        })

    st.divider()
    st.table(pd.DataFrame(results))
    
    if current_t > max_t:
        st.error(f"❌ ALARM! Naciąg końcowy {round(current_t)} N przekracza dopuszczalne {max_t} N!")
    else:
        st.success(f"✅ Naciąg bezpieczny: {round(current_t)} N")
    
    if st.button("🗑️ Wyczyść trasę"):
        st.session_state.route = []