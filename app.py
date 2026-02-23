import streamlit as st
import pandas as pd
import math

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Pull-Planner v2.2", layout="wide")
st.title("⚡ Profesjonalny Kalkulator Przeciągania Kabli")

# --- SIDEBAR: JEDNOSTKI I GEOMETRIA ---
with st.sidebar:
    st.header("🌐 Regionalizacja")
    unit_system = st.radio("System jednostek:", ["Europejski (Metric)", "USA (Imperial)"])
    
    # Definicja etykiet i przeliczników
    if unit_system == "Europejski (Metric)":
        u_len, u_dia, u_wgt, u_force = "m", "mm", "kg/m", "N"
        g_acc = 9.81
    else:
        u_len, u_dia, u_wgt, u_force = "ft", "in", "lb/ft", "lb"
        g_acc = 1.0 # W systemie USA lbf = lbm

    st.divider()
    st.header("📏 Geometria Osłony")
    conduit_type = st.radio("Typ osłony:", ["Rura okrągła", "Kanał prostokątny"])
    
    if conduit_type == "Rura okrągła":
        D_inner = st.number_input(f"Średnica wewn. D ({u_dia})", value=100.0 if u_dia=="mm" else 4.0)
    else:
        W_box = st.number_input(f"Szerokość W ({u_dia})", value=200.0 if u_dia=="mm" else 8.0)
        H_box = st.number_input(f"Wysokość H ({u_dia})", value=100.0 if u_dia=="mm" else 4.0)
        D_inner = 1000 # Dummy value dla kanałów

    st.divider()
    st.header("🔌 Lista kabli")
    if 'cables' not in st.session_state: st.session_state.cables = []
    
    c_d = st.number_input(f"Średnica kabla d ({u_dia})", value=30.0 if u_dia=="mm" else 1.2)
    c_w = st.number_input(f"Waga kabla w ({u_wgt})", value=1.5 if u_wgt=="kg/m" else 1.0)
    
    if st.button("➕ Dodaj kabel"):
        st.session_state.cables.append({"d": c_d, "w": c_w})
    if st.session_state.cables:
        st.table(pd.DataFrame(st.session_state.cables))
        if st.button("🗑️ Wyczyść kable"): st.session_state.cables = []

    st.divider()
    mu = st.slider("Współczynnik tarcia (μ)", 0.1, 0.6, 0.35)
    max_t = st.number_input(f"Dopuszczalny naciąg ({u_force})", value=5000 if u_force=="N" else 1100)

# --- ANALIZA (JAM RATIO / FILL) ---
st.subheader("📊 Analiza Techniczna")
if st.session_state.cables:
    max_d = max([c['d'] for c in st.session_state.cables])
    total_w = sum([c['w'] for c in st.session_state.cables])
    num_c = len(st.session_state.cables)
    
    # Jam Ratio i Fill wg Polywater
    col1, col2, col3 = st.columns(3)
    if conduit_type == "Rura okrągła":
        jam = D_inner / max_d
        col1.metric("Jam Ratio", round(jam, 2))
        if 2.8 <= jam <= 3.2: st.error("🚨 RYZYKO ZAKLINOWANIA!")
        
        clearance = D_inner - max_d
        col2.metric(f"Prześwit ({u_dia})", round(clearance, 1))
    else:
        col1.info("Kanał prostokątny")

# --- TRASA Z NACHYLENIEM ---
st.subheader("🛤️ Planowanie Trasy")
if 'route' not in st.session_state: st.session_state.route = []

r1, r2, r3, r4 = st.columns([2,2,2,1])
with r1: r_type = st.selectbox("Typ", ["Prosta", "Łuk"])
with r2: r_val = st.number_input(f"Długość ({u_len}) / Kąt (°)", value=10.0)
with r3:
    if r_type == "Prosta":
        slope = st.number_input("Nachylenie (%)", value=0.0)
        r_rad = 0
    else:
        r_rad = st.number_input(f"Promień ({u_len})", value=1.0)
        slope = 0
with r4:
    if st.button("➕ Dodaj odcinek"):
        st.session_state.route.append({"type": r_type, "val": r_val, "rad": r_rad, "slope": slope})

if st.session_state.route:
    # Wyznaczanie wc (Weight Correction) wg Polywater
    config = "Cradle" if num_c >= 3 else "Single"
    if conduit_type == "Rura okrągła" and num_c > 0:
        ratio = D_inner / max_d
        wc = (1 + (4/3)*(1/(ratio-1))**2) if config == "Cradle" else 1.0
    else: wc = 1.0

    current_t, results = 0.0, []
    for i, s in enumerate(st.session_state.route):
        t_in = current_t
        if s['type'] == "Prosta":
            theta = math.atan(s['slope'] / 100)
            # Wzór uwzględniający grawitację i tarcie
            t_out = t_in + (s['val'] * total_w * g_acc * (mu * wc * math.cos(theta) + math.sin(theta)))
            swp = 0
        else:
            phi = math.radians(s['val'])
            # Wzór na naciąg na łuku
            t_out = t_in * math.exp(mu * wc * phi)
            swp = t_out / s['rad'] if s['rad'] > 0 else 0
        
        current_t = max(0, t_out)
        results.append({"Odcinek": i+1, "Typ": s['type'], f"Naciąg [{u_force}]": round(current_t, 1), f"SWP [{u_force}/{u_len}]": round(swp, 1)})

    st.table(pd.DataFrame(results))
    if current_t > max_t: st.error(f"❌ Przekroczono limit: {round(current_t)} {u_force}")
    else: st.success(f"✅ Wynik: {round(current_t)} {u_force}")
    if st.button("🗑️ Wyczyść trasę"): st.session_state.route = []