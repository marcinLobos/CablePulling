import streamlit as st
import pandas as pd
import math

# --- LOGIKA OBLICZENIOWA ---
def calc_tension(sections, mu, weight_kg_m):
    results = []
    current_tension = 0.0  # Zakładamy start z naciągiem 0 (lub siłą odwijaka)
    
    for i, sec in enumerate(sections):
        type = sec['type']
        val = sec['value']
        radius = sec.get('radius', 0)
        
        t_in = current_tension
        swp = 0.0
        
        if type == "Prosta":
            # T = T_in + L * w * mu
            t_out = t_in + (val * weight_kg_m * mu * 9.81)
        else:  # Łuk
            # T_out = T_in * e^(mu * phi_rad)
            phi_rad = math.radians(val)
            t_out = t_in * math.exp(mu * phi_rad)
            if radius > 0:
                swp = t_out / radius
        
        current_tension = t_out
        results.append({
            "Sekcja": f"{i+1}. {type}",
            "Parametr": f"{val} m" if type == "Prosta" else f"{val}°",
            "Naciąg Wyjściowy [N]": round(t_out, 2),
            "Nacisk Boczny [N/m]": round(swp, 2)
        })
    return results

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Pull-Planner Lite", layout="wide")
st.title("⚡ Kalkulator Przeciągania Kabli")

with st.sidebar:
    st.header("⚙️ Parametry Kabla")
    weight = st.number_input("Waga kabla (kg/m)", value=1.5, step=0.1)
    mu = st.slider("Współczynnik tarcia (μ)", 0.1, 0.8, 0.35)
    max_tension = st.number_input("Dopuszczalny naciąg (N)", value=5000)

st.subheader("🛤️ Definicja trasy")
if 'sections' not in st.session_state:
    st.session_state.sections = []

col1, col2, col3 = st.columns(3)
with col1:
    st_type = st.selectbox("Typ sekcji", ["Prosta", "Łuk"])
with col2:
    st_val = st.number_input("Długość (m) / Kąt (°)", value=10.0)
with col3:
    st_rad = st.number_input("Promień gięcia (m)", value=1.0 if st_type == "Łuk" else 0.0)

if st.button("➕ Dodaj sekcję"):
    st.session_state.sections.append({"type": st_type, "value": st_val, "radius": st_rad})

if st.button("🗑️ Wyczyść trasę"):
    st.session_state.sections = []

# --- WYNIKI ---
if st.session_state.sections:
    res_data = calc_tension(st.session_state.sections, mu, weight)
    df = pd.DataFrame(res_data)
    
    st.divider()
    st.table(df)
    
    # Sprawdzenie przekroczeń
    final_t = res_data[-1]["Naciąg Wyjściowy [N]"]
    if final_t > max_tension:
        st.error(f"⚠️ UWAGA: Naciąg końcowy ({final_t} N) przekracza dopuszczalny!")
    else:
        st.success(f"✅ Naciąg w normie: {final_t} N")

    # EKSPORT
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Pobierz wyniki jako CSV",
        data=csv,
        file_name='obliczenia_naciagu.csv',
        mime='text/csv',
    )