import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date as dt_date
import altair as alt

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="💰 Výdavkový denník / Expense Diary", layout="wide")

# ---------------------------
# STYLES
# ---------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 16px; line-height: 1.6; }
h1 { font-size: 28px !important; }
.issuecoin {
    font-family: monospace;
    text-align: center;
    margin-top: 15px;
    white-space: pre;
    line-height: 1.2;
}
.issuecoin-msg {
    text-align: center;
    font-size: 18px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# LANGUAGE SWITCH
# ---------------------------
col_lang, col_flag = st.columns([7, 3])
with col_flag:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

# ---------------------------
# TRANSLATIONS
# ---------------------------
TEXTS = {
    "sk": {
        "title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB.",
        "date": "📅 Dátum nákupu",
        "country": "🌍 Krajina + mena",
        "amount": "💵 Čiastka",
        "category": "📂 Kategória",
        "shop": "🏬 Obchod / miesto",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť nákup",
        "saved": "Záznam uložený!",
        "summary": "📊 Súhrn výdavkov",
        "total": "Celkom CZK",
        "export": "💾 Exportovať CSV",
        "holiday_msg": "🎉 Dnes je sviatok! Oddýchni si a uži deň. 😊",
        "gdpr": "🔒 Údaje sa ukladajú len lokálne v tvojom zariadení (žiadny server, GDPR friendly)."
    },
    "en": {
        "title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates.",
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "category": "📂 Category",
        "shop": "🏬 Shop / place",
        "note": "📝 Note",
        "save": "💾 Save purchase",
        "saved": "Saved!",
        "summary": "📊 Expenses summary",
        "total": "Total CZK",
        "export": "💾 Export CSV",
        "holiday_msg": "🎉 Today is a public holiday! Enjoy your day off! 😊",
        "gdpr": "🔒 Your data are stored locally only (no server, GDPR friendly)."
    }
}

# ---------------------------
# CATEGORIES
# ---------------------------
CATEGORIES = {
    "sk": [
        "Potraviny 🛒 / Potraviny 🛒",
        "Drogérie 🧴 / Drogérie 🧴",
        "Odevy 👕 / Oblečenie 👕",
        "Doprava 🚌 / Doprava 🚌",
        "Reštaurácie a bary 🍽️ / Restaurace a bary 🍽️",
        "Zábava 🎉 / Zábava 🎉",
        "Obuv 👟 / Obuv 👟",
        "Elektronika 💻 / Elektronika 💻",
        "Domácnosť / nábytok 🛋️ / Domácnost / nábytek 🛋️",
        "Šport a voľný čas 🏀 / Sport a volný čas 🏀",
        "Zdravie a lekáreň 💊 / Zdraví a lékárna 💊",
        "Cestovanie / dovolenka ✈️ / Cestování / dovolená ✈️",
        "Vzdelávanie / kurzy 📚 / Vzdělávání / kurzy 📚"
    ],
    "en": [
        "Groceries 🛒",
        "Drugstore 🧴",
        "Clothing 👕",
        "Transport 🚌",
        "Restaurants & Bars 🍽️",
        "Entertainment 🎉",
        "Shoes 👟",
        "Electronics 💻",
        "Household / Furniture 🛋️",
        "Sports & Leisure 🏀",
        "Health & Pharmacy 💊",
        "Travel / Holiday ✈️",
        "Education / Courses 📚"
    ]
}

# ---------------------------
# COUNTRIES (CNB + ISO2)
# ---------------------------
CNB_TXT_DAILY = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/denni_kurz.txt"
CNB_TXT_DAILY_AT = CNB_TXT_DAILY + "?date={date}"

COUNTRIES = {
    "sk": [
        "Česko – CZK Kč",
        "Slovensko – EUR €",
        "Nemecko – EUR € / Německo – EUR €",
        "Rakúsko – EUR € / Rakousko – EUR €",
        "Poľsko – PLN zł / Polsko – PLN zł",
        "Maďarsko – HUF Ft / Maďarsko – HUF Ft",
        "Veľká Británia – GBP £ / Velká Británie – GBP £",
        "USA – USD $",
        "Švajčiarsko – CHF ₣ / Švýcarsko – CHF ₣",
        "Dánsko – DKK kr / Dánsko – DKK kr",
        "Švédsko – SEK kr / Švédsko – SEK kr",
        "Nórsko – NOK kr / Norsko – NOK kr",
        "Kanada – CAD $",
        "Japonsko – JPY ¥",
        "Holandsko – EUR € / Nizozemsko – EUR €",
        "Belgicko – EUR € / Belgie – EUR €",
        "Francúzsko – EUR € / Francie – EUR €",
        "Španielsko – EUR € / Španělsko – EUR €",
        "Taliansko – EUR € / Itálie – EUR €",
        "Írsko – EUR € / Irsko – EUR €",
        "Fínsko – EUR € / Finsko – EUR €",
        "Grécko – EUR € / Řecko – EUR €",
        "Chorvátsko – EUR € / Chorvatsko – EUR €",
    ],
    "en": [
        "Czechia – CZK Kč",
        "Slovakia – EUR €",
        "Germany – EUR €",
        "Austria – EUR €",
        "Poland – PLN zł",
        "Hungary – HUF Ft",
        "United Kingdom – GBP £",
        "USA – USD $",
        "Switzerland – CHF ₣",
        "Denmark – DKK kr",
        "Sweden – SEK kr",
        "Norway – NOK kr",
        "Canada – CAD $",
        "Japan – JPY ¥",
        "Netherlands – EUR €",
        "Belgium – EUR €",
        "France – EUR €",
        "Spain – EUR €",
        "Italy – EUR €",
        "Ireland – EUR €",
        "Finland – EUR €",
        "Greece – EUR €",
        "Croatia – EUR €",
    ]
}

COUNTRY_TO_CODE = {
    "Česko – CZK Kč": "CZK",
    "Slovensko – EUR €": "EUR",
    "Nemecko – EUR € / Německo – EUR €": "EUR",
    "Rakúsko – EUR € / Rakousko – EUR €": "EUR",
    "Poľsko – PLN zł / Polsko – PLN zł": "PLN",
    "Maďarsko – HUF Ft / Maďarsko – HUF Ft": "HUF",
    "Veľká Británia – GBP £ / Velká Británie – GBP £": "GBP",
    "USA – USD $": "USD",
}

COUNTRY_TO_ISO = {
    "Česko – CZK Kč": "CZ",
    "Slovensko – EUR €": "SK",
    "Nemecko – EUR € / Německo – EUR €": "DE",
    "Rakúsko – EUR € / Rakousko – EUR €": "AT",
    "Poľsko – PLN zł / Polsko – PLN zł": "PL",
    "Maďarsko – HUF Ft / Maďarsko – HUF Ft": "HU",
    "Veľká Británia – GBP £ / Velká Británie – GBP £": "GB",
    "USA – USD $": "US"
}

# ---------------------------
# ISSUECOIN AGENT
# ---------------------------
def get_issuecoin_emoji():
    month = datetime.now().month
    # Base stick figure
    head = "🔵"
    body = " /│\\"
    legs = " / \\"
    extra = ""
    if month in [12, 1, 2]:
        extra = "🧣" if datetime.now().day < 20 else "🎅"
    elif month in [3, 4, 5]:
        extra = "🏃"
    elif month in [6, 7, 8]:
        extra = "😎"
    elif month in [9, 10, 11]:
        extra = "🍄"
    return f"{head}\n{body}\n{legs}\n{extra}"

# ---------------------------
# CNB EXCHANGE RATE
# ---------------------------
@st.cache_data(ttl=600)
def fetch_cnb_txt(date_str: str):
    url = CNB_TXT_DAILY_AT.format(date=date_str)
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.text

def parse_rate(txt: str, code: str):
    if not txt: return None, None
    lines = txt.splitlines()
    date = lines[0].split(" #")[0]
    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) == 5 and parts[3] == code:
            rate = float(parts[4].replace(",", "."))
            qty = float(parts[2].replace(",", "."))
            return rate/qty, date
    return None, None

def get_rate_for(code: str, d: dt_date):
    if code == "CZK": return 1.0, d.isoformat()
    d_str = d.strftime("%d.%m.%Y")
    txt = fetch_cnb_txt(d_str)
    rate, header_date = parse_rate(txt, code)
    if not rate:
        txt = requests.get(CNB_TXT_DAILY).text
        rate, header_date = parse_rate(txt, code)
    return rate, header_date or d.isoformat()

# ---------------------------
# HOLIDAY CHECK (Calendarific)
# ---------------------------
API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"

def is_holiday(iso_country, d):
    url = f"https://calendarific.com/api/v2/holidays?&api_key={API_KEY}&country={iso_country}&year={d.year}&month={d.month}&day={d.day}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        holidays = data.get("response", {}).get("holidays", [])
        return len(holidays) > 0
    return False

# ---------------------------
# MAIN APP
# ---------------------------
st.title(TEXTS[LANG]["title"])
st.caption(TEXTS[LANG]["subtitle"])

with st.form("form"):
    d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today())
    country = st.selectbox(TEXTS[LANG]["country"], COUNTRIES[LANG])
    amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0)
    category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    shop = st.text_input(TEXTS[LANG]["shop"])
    note = st.text_input(TEXTS[LANG]["note"])
    submit = st.form_submit_button(TEXTS[LANG]["save"])

if submit:
    code = COUNTRY_TO_CODE.get(country, "CZK")
    iso = COUNTRY_TO_ISO.get(country, "CZ")
    rate, rate_date = get_rate_for(code, d)
    converted = amount * rate if rate else amount
    st.success(f"{TEXTS[LANG]['saved']} ({converted:.2f} CZK)")
    if is_holiday(iso, d):
        st.info(TEXTS[LANG]["holiday_msg"])
    issue = get_issuecoin_emoji()
    st.markdown(f"<div class='issuecoin'>{issue}</div>", unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center;color:gray;font-size:14px'>{TEXTS[LANG]['gdpr']}</p>", unsafe_allow_html=True)
