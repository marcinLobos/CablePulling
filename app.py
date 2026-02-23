import streamlit as st
import pandas as pd
import math

# --- SŁOWNIK JĘZYKOWY (Jasne i pełne nazwy) ---
TLUMACZENIA_INTERFEJSU = {
    "PL": {
        "tytul": "⚡ Profesjonalny Kalkulator Naciągu Kabli",
        "naciag": "Naciąg",
        "bezpiecznie": "✅ Wynik bezpieczny",
        "alarm": "❌ PRZEKROCZONO LIMIT!",
        "jednostki": "System jednostek:",
        "prosta": "Odcinek prosty",
        "luk": "Łuk (Zakręt)",
        "nachylenie": "Nachylenie",
        "promien": "Promień łuku",
        "lista_kabli": "🔌 Lista kabli w kanale",
        "dodaj_odcinek": "➕ Dodaj odcinek do trasy",
        "wyczysc": "🗑️ Wyczyść"
    },
    "EN": {
        "tytul": "⚡ Professional Cable Pull-Planner",
        "naciag": "Tension",
        "bezpiecznie": "✅ Safe Result",
        "alarm": "❌ LIMIT EXCEEDED!",
        "jednostki": "Unit system:",
        "prosta": "Straight section",
        "luk": "Bend",
        "nachylenie": "Slope",
        "promien": "Bend Radius",
        "lista_kabli": "🔌 Cable list in conduit",
        "dodaj_odcinek": "➕ Add section to route",
        "wyczysc": "🗑️ Clear"
    }
}

st.set_page_config(page_title="Pull-Planner v2.7", layout="wide")

# --- PANEL BOCZNY ---
with st.sidebar:
    jezyk = st.radio("Język / Language:", ["PL", "EN"], horizontal=True)
    txt = TLUMACZENIA_INTERFEJSU[jezyk]
    
    st.header("⚙️ Ustawienia")
    wybrany_system = st.radio(txt["jednostki"], ["Metric (N)", "Metric (kN)", "USA (lb)"])
    
    # Dobór mnożników - Twoja poprawka z kN jest tutaj kluczowa
    if "kN" in wybrany_system:
        jednostka_sily = "kN"
        mnoznik_na_niutony = 1000.0  # Dane z klawiatury * 1000 = Niutony
        mnoznik_na_ekran = 0.001     # Niutony z fizyki * 0.001 = kN na ekran
        g = 9.81
    elif "lb" in wybrany_system:
        jednostka_sily = "lb"
        mnoznik_na_niutony = 1.0
        mnoznik_na_ekran = 1.0
        g = 1.0
    else:
        jednostka_sily = "N"
        mnoznik_na_niutony = 1.0
        mnoznik_na_ekran = 1.0
        g = 9.81

    st.divider()
    limit_uzytkownika = st.number_input(f"Limit ({jednostka_sily})", value=10.0 if jednostka_sily=="kN" else 5000.0)
    limit_N = limit_uzytkownika * mnoznik_na_niutony

# --- ZARZĄDZANIE KABLAMI ---
if 'kable' not in st.session_state: st.session_state.kable = []
st.sidebar.header(txt["lista_kabli"])
c_d = st.sidebar.number_input("Średnica (mm/in)", value=30.0)
c_w = st.sidebar.number_input("Waga (kg/m / lb/ft)", value=1.5)
if st.sidebar.button(txt["dodaj_odcinek"].split()[0]): # Uproszczony przycisk 'Dodaj'
    st.session_state.kable.append({"d": c_d, "w": c_w})

# --- TRASA I OBLICZENIA ---
st.title(txt["tytul"])
if 'trasa' not in st.session_state: st.session_state.trasa = []

c1, c2, c3 = st.columns([2, 2, 3])
with c1: typ = st.selectbox("Typ", [txt["prosta"], txt["luk"]])
with c2: val = st.number_input("Długość/Kąt", value=10.0)
with c3:
    if typ == txt["prosta"]:
        tryb_nachylenia = st.radio("Jednostka nachylenia:", ["°", "%"], horizontal=True)
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
    mu, wc = 0.35, 1.0 # Tarcie i korekcja wagi
    
    dane_tabeli = []
    for i, s in enumerate(st.session_state.trasa):
        if s["typ"] == txt["prosta"]:
            # Zamiana nachylenia na radiany (one-liner, ale czytelny)
            theta = math.radians(s["slope"]) if s["s_mode"] == "°" else math.atan(s["slope"]/100)
            # Fizyka: T = T_in + L*w*g*(mu*cos + sin)
            naciag_N += s["val"] * waga_total * g * (mu * wc * math.cos(theta) + math.sin(theta))
        else:
            phi = math.radians(s["val"])
            # Fizyka łuku: T = T_in * e^(mu*wc*phi)
            naciag_N *= math.exp(mu * wc * phi)
        
        naciag_N = max(0, naciag_N)
        dane_tabeli.append({
            "#": i+1, 
            "Typ": s["typ"], 
            f"{txt['naciag']} [{jednostka_sily}]": round(naciag_N * mnoznik_na_ekran, 3)
        })

    st.table(pd.DataFrame(dane_tabeli))
    
    wynik_ekran = naciag_N * mnoznik_na_ekran
    if naciag_N > limit_N:
        st.error(f"{txt['alarm']} ({round(wynik_ekran, 2)} {jednostka_sily})")
    else:
        st.success(f"{txt['bezpiecznie']} ({round(wynik_ekran, 2)} {jednostka_sily})")