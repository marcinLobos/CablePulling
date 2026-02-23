import streamlit as st
import pandas as pd
import math

# --- SŁOWNIK JĘZYKOWY ---
lang_dict = {
    "PL": {
        "title": "⚡ Profesjonalny Kalkulator Naciągu Kabli",
        "settings": "⚙️ Ustawienia",
        "lang_select": "Wybierz język / Select language:",
        "unit_select": "System jednostek:",
        "conduit": "📏 Geometria Osłony",
        "c_type": "Typ osłony:",
        "c_round": "Rura okrągła",
        "c_box": "Kanał prostokątny",
        "c_dia": "Średnica wewn. D",
        "c_w": "Szerokość W",
        "c_h": "Wysokość H",
        "cables": "🔌 Lista kabli",
        "add_c": "➕ Dodaj kabel",
        "clear_c": "🗑️ Wyczyść kable",
        "friction": "Współczynnik tarcia (μ)",
        "max_t": "Dopuszczalny naciąg",
        "analysis": "📊 Analiza Techniczna",
        "jam_err": "🚨 RYZYKO ZAKLINOWANIA!",
        "clearance": "Prześwit",
        "route_plan": "🛤️ Planowanie Trasy",
        "sec_type": "Typ odcinka",
        "sec_straight": "Prosta",
        "sec_bend": "Łuk",
        "sec_len": "Długość",
        "sec_ang": "Kąt",
        "sec_slope": "Jednostka nachylenia:",
        "slope_p": "Procenty (%)",
        "slope_d": "Stopnie (°)",
        "slope_val": "Wartość nachylenia (+ góra, - dół)",
        "radius": "Promień łuku",
        "add_sec": "➕ Dodaj odcinek",
        "results": "Wyniki",
        "tension": "Naciąg",
        "swp": "Nacisk Boczny (SWP)",
        "safe": "✅ Wynik bezpieczny",
        "alarm": "❌ ALARM: PRZEKROCZONO LIMIT!",
        "clear_route": "🗑️ Wyczyść trasę"
    },
    "EN": {
        "title": "⚡ Professional Cable Pull-Planner",
        "settings": "⚙️ Settings",
        "lang_select": "Select language:",
        "unit_select": "Unit system:",
        "conduit": "📏 Conduit Geometry",
        "c_type": "Conduit type:",
        "c_round": "Round Conduit",
        "c_box": "Rectangular Duct",
        "c_dia": "Internal Diameter D",
        "c_w": "Width W",
        "c_h": "Height H",
        "cables": "🔌 Cable List",
        "add_c": "➕ Add Cable",
        "clear_c": "🗑️ Clear Cables",
        "friction": "Coefficient of Friction (μ)",
        "max_t": "Max Allowable Tension",
        "analysis": "📊 Technical Analysis",
        "jam_err": "🚨 JAMMING RISK!",
        "clearance": "Clearance",
        "route_plan": "🛤️ Route Planning",
        "sec_type": "Section Type",
        "sec_straight": "Straight",
        "sec_bend": "Bend",
        "sec_len": "Length",
        "sec_ang": "Angle",
        "sec_slope": "Slope unit:",
        "slope_p": "Percentage (%)",
        "slope_d": "Degrees (°)",
        "slope_val": "Slope value (+ up, - down)",
        "radius": "Bend Radius",
        "add_sec": "➕ Add Section",
        "results": "Results",
        "tension": "Tension",
        "swp": "Sidewall Pressure (SWP)",
        "safe": "✅ Safe Result",
        "alarm": "❌ ALARM: LIMIT EXCEEDED!",
        "clear_route": "🗑️ Clear Route"
    }
}

# --- INICJALIZACJA ---
st.set_page_config(page_title="Pull-Planner v2.4", layout="wide")

# Wybór języka w sidebarze
with st.sidebar:
    L_CODE = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    T = lang_dict[L_CODE]

st.title(T["title"])

with st.sidebar:
    st.divider()
    st.header(T["settings"])
    unit_system = st.radio(T["unit_select"], ["Metric (kg, m, N)", "Metric (kg, m, kN)", "USA (lb, ft, lb)"])
    
    if "kN" in unit_system: u_len, u_dia, u_wgt, u_force, g_acc, force_mult = "m", "mm", "kg/m", "kN", 9.81, 0.001
    elif "lb" in unit_system: u_len, u_dia, u_wgt, u_force, g_acc, force_mult = "ft", "in", "lb/ft", "lb", 1.0, 1.0
    else: u_len, u_dia, u_wgt, u_force, g_acc, force_mult = "m", "mm", "kg/m", "N", 9.81, 1.0

    st.divider()
    st.header(T["conduit"])
    conduit_type = st.radio(T["c_type"], [T["c_round"], T["c_box"]])
    if conduit_type == T["c_round"]:
        D_inner = st.number_input(f"{T['c_dia']} ({u_dia})", value=100.0 if u_dia=="mm" else 4.0)
    else:
        W_box = st.number_input(f"{T['c_w']} ({u_dia})", value=200.0 if u_dia=="mm" else 8.0)
        H_box = st.number_input(f"{T['c_h']} ({u_dia})", value=100.0 if u_dia=="mm" else 4.0)
        D_inner = 1000

    st.divider()
    st.header(T["cables"])
    if 'cables' not in st.session_state: st.session_state.cables = []
    c_d = st.number_input(f"d ({u_dia})", value=30.0 if u_dia=="mm" else 1.2)
    c_w = st.number_input(f"w ({u_wgt})", value=1.5 if u_wgt=="kg/m" else 1.0)
    if st.button(T["add_c"]): st.session_state.cables.append({"d": c_d, "w": c_w})
    if st.session_state.cables:
        st.table(pd.DataFrame(st.session_state.cables))
        if st.button(T["clear_c"]): st.session_state.cables = []

    st.divider()
    mu = st.slider(T["friction"], 0.1, 0.6, 0.35)
    max_t = st.number_input(f"{T['max_t']} ({u_force})", value=5000.0 if u_force=="N" else (5.0 if u_force=="kN" else 1100.0))

# --- ANALIZA TECHNICZNA ---
st.subheader(T["analysis"])
if st.session_state.cables:
    max_d = max([c['d'] for c in st.session_state.cables])
    total_w = sum([c['w'] for c in st.session_state.cables])
    num_c = len(st.session_state.cables)
    col1, col2, col3 = st.columns(3)
    if conduit_type == T["c_round"]:
        jam = D_inner / max_d
        col1.metric("Jam Ratio", round(jam, 2))
        if 2.8 <= jam <= 3.2: st.error(T["jam_err"])
        col2.metric(f"{T['clearance']} ({u_dia})", round(D_inner - max_d, 1))
    else: col1.info(T["c_box"])

# --- TRASA ---
st.subheader(T["route_plan"])
if 'route' not in st.session_state: st.session_state.route = []
r1, r2, r3, r4 = st.columns([2,2,3,1])
with r1: r_type = st.selectbox(T["sec_type"], [T["sec_straight"], T["sec_bend"]])
with r2: r_val = st.number_input(f"{T['sec_len'] if r_type==T['sec_straight'] else T['sec_ang']} ({u_len if r_type==T['sec_straight'] else '°'})", value=10.0)
with r3:
    if r_type == T["sec_straight"]:
        slope_mode = st.radio(T["sec_slope"], [T["slope_p"], T["slope_d"]], horizontal=True)
        slope_val = st.number_input(T["slope_val"], value=0.0)
        r_rad = 0
    else:
        r_rad = st.number_input(f"{T['radius']} ({u_len})", value=1.0)
        slope_val, slope_mode = 0, "D"
with r4:
    if st.button(T["add_sec"]):
        st.session_state.route.append({"type": r_type, "val": r_val, "rad": r_rad, "slope": slope_val, "s_mode": slope_mode})

if st.session_state.route:
    config = "Cradle" if num_c >= 3 else "Single"
    if conduit_type == T["c_round"] and num_c > 0:
        ratio = D_inner / max_d
        wc = (1 + (4/3)*(1/(ratio-1))**2) if config == "Cradle" else 1.0
    else: wc = 1.0

    current_t, results = 0.0, []
    for i, s in enumerate(st.session_state.route):
        t_in = current_t
        if s['type'] == T["sec_straight"]:
            theta = math.atan(s['slope'] / 100) if s['s_mode'] == T["slope_p"] else math.radians(s['slope'])
            t_out = t_in + (s['val'] * total_w * g_acc * (mu * wc * math.cos(theta) + math.sin(theta))) * force_mult
            swp = 0
        else:
            phi = math.radians(s['val'])
            t_out = t_in * math.exp(mu * wc * phi)
            swp = (t_out / s['rad']) if s['rad'] > 0 else 0
        
        current_t = max(0, t_out)
        results.append({"#": i+1, T["sec_type"]: s['type'], f"{T['tension']} [{u_force}]": round(current_t, 3), f"{T['swp']} [{u_force}/{u_len}]": round(swp if s['type']==T["sec_bend"] else 0, 1)})

    st.table(pd.DataFrame(results))
    if current_t > max_t: st.error(f"{T['alarm']} ({round(current_t, 2)} {u_force})")
    else: st.success(f"{T['safe']} ({round(current_t, 2)} {u_force})")
    if st.button(T["clear_route"]): st.session_state.route = []