import streamlit as st
import pandas as pd
import math

# --- SŁOWNIK JĘZYKOWY ---
TLUMACZENIA_INTERFEJSU = {
    "PL": {
        "tytul": "⚡ Profesjonalny Kalkulator Naciągu Kabli",
        "naciag": "Naciąg",
        "bezpiecznie": "✅ Wynik bezpieczny",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "jednostki": "System jednostek:",
        "prosta": "Odcinek prosty",
        "luk": "Łuk (Zakręt)",
        "promien": "Promień łuku",
        "dodaj_odcinek": "➕ Dodaj odcinek",
        "lista_kabli": "🔌 Kable w kanale"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner",
        "naciag": "Tension",
        "bezpiecznie": "✅ Safe Result",
        "alarm": "❌ LIMIT EXCEEDED!",
        "jednostki": "Unit system:",
        "prosta": "Straight section",
        "luk": "Bend",
        "promien": "Bend Radius",
        "dodaj_odcinek": "➕ Add section",
        "lista_kabli": "🔌 Cable list"
    }
}

st.set_page_config(page_title="Pull-Planner v2.8", layout="wide")

# --- PANEL BOCZNY (USTAWIENIA) ---
with st.sidebar:
    jezyk = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA_INTERFEJSU[jezyk]
    
    st.header("⚙️ Ustawienia")
    wybrany_system = st.radio(txt["jednostki"], ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    # Logika mnożników i stała grawitacji g
    if "kN" in wybrany_system:
        jednostka_sily = "kN"
        mnoznik_na_N = 1000.0   # Wejście
        mnoznik_na_ekran = 0.001 # Wyjście
        g = 9.81
    elif "lb" in wybrany_system:
        jednostka_sily = "lb"
        mnoznik_na_N = 1.0
        mnoznik_na_ekran = 1.0
        g = 1.0 # W systemie USA lbf = lbm
    else:
        jednostka_sily = "N"
        mnoznik_na_N = 1.0
        mnoznik_na_ekran = 1.0
        g = 9.81

    st.divider()
    limit_uzytkownika = st.number_input(f"Limit ({jednostka_sily})", value=10.0 if jednostka_sily=="kN" else 5000.0)
    limit_N = limit_uzytkownika * mnoznik_na_N

    # Sekcja kabli
    st.header(txt["lista_kabli"])
    if 'kable' not in st.session_state: st.session_state.kable = []
    c_d = st.number_input("Średnica (mm/in)", value=30.0)
    c_w = st.number_input("Waga (kg/m / lb/ft)", value=1.5)
    if st.button("➕ Dodaj kabel"):
        st.session_state.kable.append({"d": c_d, "w": c_w})

# --- TRASA I OBLICZENIA ---
st.title(txt["tytul"])
if 'trasa' not in st.session_state: st.session_state.trasa = []

c1, c2, c3 = st.columns([2, 2, 3])
with c1: typ = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
with c2: val = st.number_input("Długość (m) / Kąt (°)", value=10.0)
with c3:
    if typ == txt["prosta"]:
        tryb_nachylenia = st.radio("Jednostka:", ["°", "%"], horizontal=True)
        nachylenie = st.number_input("Wartość (+ góra, - dół)", value=0.0)
        promien = 0.0
    else:
        promien = st.number_input(txt["promien"], value=1.0)
        nachylenie, tryb_nachylenia = 0.0, "°"

if st.button(txt["dodaj_odcinek"]):
    st.session_state.trasa.append({"typ": typ, "val": val, "slope": nachylenie, "s_mode": tryb_nachylenia, "r": promien})

if st.session_state.trasa:
    naciag_N = 0.0
    waga_total = sum([k['w'] for k in st.session_state.kable]) if st.session_state.kable else 1.5
    mu, wc = 0.35, 1.0
    
    wyniki_tabela = []
    for i, s in enumerate(st.session_state.trasa):
        if s["typ"] == txt["prosta"]:
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s["slope"]/100)
            # Fizyka z użyciem 'g'
            naciag_N += s["val"] * waga_total * g * (mu * wc * math.cos(theta) + math.sin(theta))
        else:
            phi = math.radians(s["val"])
            naciag_N *= math.exp(mu * wc * phi)
        
        naciag_N = max(0, naciag_N)
        wyniki_tabela.append({
            "#": i+1, 
            "Typ": s["typ"], 
            f"{txt['naciag']} [{jednostka_sily}]": round(naciag_N * mnoznik_na_ekran, 3)
        })

    st.table(pd.DataFrame(wyniki_tabela))
    
    naciag_finalny = naciag_N * mnoznik_na_ekran
    if naciag_N > limit_N:
        st.error(f