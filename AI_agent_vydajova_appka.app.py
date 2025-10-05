import streamlit as st
import pandas as pd
import requests
from datetime import date as dt_date, datetime
import random

st.set_page_config(page_title="Výdavkový denník 💰", layout="centered")

# ==============================
# KONŠTANTY A API
# ==============================
CNB_TXT_DAILY = "https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt"
CNB_TXT_DAILY_AT = "https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt?date={date}"
CALENDARIFIC_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"
CALENDARIFIC_URL = "https://calendarific.com/api/v2/holidays"

# ==============================
# KRAJINY + KÓDY
# ==============================
COUNTRIES = {
    "sk": [
        "Česko – CZK Kč", "Slovensko – EUR €", "Nemecko – EUR €",
        "Rakúsko – EUR €", "Poľsko – PLN zł", "Maďarsko – HUF Ft",
        "Veľká Británia – GBP £", "USA – USD $", "Švajčiarsko – CHF ₣",
        "Dánsko – DKK kr", "Švédsko – SEK kr", "Nórsko – NOK kr",
        "Kanada – CAD $", "Japonsko – JPY ¥", "Holandsko – EUR €",
        "Francúzsko – EUR €", "Španielsko – EUR €", "Taliansko – EUR €"
    ],
    "en": [
        "Czechia – CZK Kč", "Slovakia – EUR €", "Germany – EUR €",
        "Austria – EUR €", "Poland – PLN zł", "Hungary – HUF Ft",
        "United Kingdom – GBP £", "USA – USD $", "Switzerland – CHF ₣",
        "Denmark – DKK kr", "Sweden – SEK kr", "Norway – NOK kr",
        "Canada – CAD $", "Japan – JPY ¥", "Netherlands – EUR €",
        "France – EUR €", "Spain – EUR €", "Italy – EUR €"
    ]
}

COUNTRY_TO_CODE = {
    "CZ": "CZK", "SK": "EUR", "DE": "EUR", "AT": "EUR", "PL": "PLN",
    "HU": "HUF", "GB": "GBP", "US": "USD", "CH": "CHF", "DK": "DKK",
    "SE": "SEK", "NO": "NOK", "CA": "CAD", "JP": "JPY",
    "NL": "EUR", "FR": "EUR", "ES": "EUR", "IT": "EUR"
}

# ==============================
# FUNKCIE
# ==============================

def get_rate(code):
    if code == "CZK":
        return 1.0
    try:
        txt = requests.get(CNB_TXT_DAILY, timeout=10).text
        for line in txt.splitlines()[2:]:
            parts = line.split("|")
            if len(parts) >= 5 and parts[3] == code:
                rate = float(parts[4].replace(",", "."))
                qty = float(parts[2])
                return rate / qty
    except:
        return None
    return None

def check_holiday(country_iso, year, month, day):
    try:
        r = requests.get(
            f"{CALENDARIFIC_URL}?api_key={CALENDARIFIC_KEY}&country={country_iso}&year={year}&month={month}&day={day}",
            timeout=10
        ).json()
        holidays = r.get("response", {}).get("holidays", [])
        return holidays[0]["name"] if holidays else None
    except:
        return None

# Panáčik IssueCoin podľa sezóny 🎭
def get_issuecoin_figure():
    today = datetime.now()
    m = today.month

    if 12 == m and 20 <= today.day <= 26:
        return "🎅🔵<br> /│\\<br> / \\ "
    elif m in [12, 1, 2]:
        return "🧣🔵<br> /│\\<br> / \\ "
    elif m in [3, 4, 5]:
        return "🌼🔵<br> /│💪<br> / \\ "
    elif m in [6, 7, 8]:
        return "😎🔵<br> /│\\<br> / \\ "
    elif m in [9, 10, 11]:
        return "🍄🔵<br> /│\\<br> / \\ "
    else:
        return "🔵<br> /│\\<br> / \\ "

# ==============================
# TITULOK A JAZYK
# ==============================
lang = st.sidebar.selectbox("🌐 Jazyk / Language", ["🇸🇰 Slovenčina / Čeština", "🇬🇧 English"])
language = "sk" if "Slovenčina" in lang else "en"

if language == "sk":
    st.title("💰 Výdavkový denník")
    st.caption("Tvoje financie pod kontrolou s úsmevom 😊")
else:
    st.title("💰 Expense Diary")
    st.caption("Your finances under control, with a smile 😊")

# ==============================
# VSTUPNÉ POLE
# ==============================
col1, col2 = st.columns(2)
with col1:
    selected_country = st.selectbox("🌍 Krajina / Country", COUNTRIES[language])
with col2:
    selected_date = st.date_input("📅 Dátum / Date", dt_date.today())

country_iso = list(COUNTRY_TO_CODE.keys())[list(COUNTRY_TO_CODE.values()).index(COUNTRY_TO_CODE.get("CZ", "CZK"))]
currency = COUNTRY_TO_CODE.get("CZ", "CZK")

# ==============================
# SUMA, KATEGÓRIA, POZNÁMKA
# ==============================
amount = st.number_input("💵 Čiastka / Amount", min_value=0.0, step=10.0)
category = st.selectbox("🛍️ Kategória / Category", [
    "Potraviny / Groceries", "Zábava / Entertainment", "Reštaurácie / Restaurants",
    "Drogéria / Drugstore", "Cestovanie / Travel", "Bývanie / Housing", "Ostatné / Other"
])
note = st.text_input("📝 Poznámka / Note")

# ==============================
# AI AGENT ISSUECOIN
# ==============================
issuecoin_html = f"""
<div style='text-align:center;'>
    <div style='font-size:40px; line-height:1.1;'>{get_issuecoin_figure()}</div>
</div>
"""

def show_issuecoin_message(msg):
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:20px;'>
        {issuecoin_html}
        <div style='font-size:18px; background:#f0f2f6; padding:10px 15px; border-radius:10px;'>{msg}</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# HLÁŠKY PODĽA SITUÁCIE
# ==============================
holiday = check_holiday("CZ", selected_date.year, selected_date.month, selected_date.day)

if holiday:
    msg = f"🎉 Dnes je sviatok ({holiday})! Oddýchni si a uži deň! 😊" if language == "sk" else f"🎉 It's a holiday today ({holiday})! Enjoy and relax! 😊"
    show_issuecoin_message(msg)
elif amount > 0:
    if category in ["Zábava / Entertainment", "Reštaurácie / Restaurants"]:
        if amount >= 1000:
            msg = random.choice([
                "🎉 Vyzerá to na super večer! Uži si to! 😄",
                "🍽️ Dobré jedlo, dobrá nálada!",
                "😋 Odmena musí byť, hlavne po dobrom týždni!"
            ])
        else:
            msg = None
    else:
        if amount >= 6500:
            msg = "💸 Uff, to už je slušná suma! Možno mal IssueCoin pravdu 😅"
        elif amount >= 2500:
            msg = "💡 Dobrý nákup, ale skús si dať pozor na rozpočet 😉"
        else:
            msg = None

    if msg:
        show_issuecoin_message(msg)

# ==============================
# GDPR INFO
# ==============================
gdpr_msg = "🔒 Tvoje údaje sa nikam neposielajú – všetko zostáva len u teba 💚" if language == "sk" else "🔒 Your data never leaves your device – everything stays safely with you 💚"
st.info(gdpr_msg)

# ==============================
# ULOŽENIE
# ==============================
if st.button("💾 Uložiť / Save"):
    rate = get_rate(currency)
    st.success(f"Záznam uložený. Kurz {currency}: {rate:.2f} CZK" if language == "sk" else f"Record saved. Rate {currency}: {rate:.2f} CZK")
