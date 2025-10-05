import streamlit as st
import pandas as pd
import requests
from datetime import date as dt_date, datetime

# -------------------------------
# API KONŠTANTY
# -------------------------------
CNB_TXT_DAILY = "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/exchange-rate-fixing/daily.txt"
CNB_TXT_DAILY_AT = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt?date={date}"
CALENDARIFIC_API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"

st.set_page_config(page_title="Výdavkový denník / Expense Diary", page_icon="💰", layout="centered")

# -------------------------------
# KRAJINY + MENY (CNB)
# -------------------------------
COUNTRIES = [
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
    "Francúzsko – EUR € / Francie – EUR €",
    "Taliansko – EUR € / Itálie – EUR €",
    "Španielsko – EUR € / Španělsko – EUR €",
    "Holandsko – EUR € / Nizozemsko – EUR €",
]

COUNTRY_TO_CODE = {
    "Česko – CZK Kč": ("CZK", "CZ"),
    "Slovensko – EUR €": ("EUR", "SK"),
    "Nemecko – EUR € / Německo – EUR €": ("EUR", "DE"),
    "Rakúsko – EUR € / Rakousko – EUR €": ("EUR", "AT"),
    "Poľsko – PLN zł / Polsko – PLN zł": ("PLN", "PL"),
    "Maďarsko – HUF Ft / Maďarsko – HUF Ft": ("HUF", "HU"),
    "Veľká Británia – GBP £ / Velká Británie – GBP £": ("GBP", "GB"),
    "USA – USD $": ("USD", "US"),
    "Švajčiarsko – CHF ₣ / Švýcarsko – CHF ₣": ("CHF", "CH"),
    "Dánsko – DKK kr / Dánsko – DKK kr": ("DKK", "DK"),
    "Švédsko – SEK kr / Švédsko – SEK kr": ("SEK", "SE"),
    "Nórsko – NOK kr / Norsko – NOK kr": ("NOK", "NO"),
    "Kanada – CAD $": ("CAD", "CA"),
    "Japonsko – JPY ¥": ("JPY", "JP"),
    "Francúzsko – EUR € / Francie – EUR €": ("EUR", "FR"),
    "Taliansko – EUR € / Itálie – EUR €": ("EUR", "IT"),
    "Španielsko – EUR € / Španělsko – EUR €": ("EUR", "ES"),
    "Holandsko – EUR € / Nizozemsko – EUR €": ("EUR", "NL"),
}

# -------------------------------
# CNB FUNKCIE
# -------------------------------
@st.cache_data(ttl=600)
def _fetch_txt(url: str):
    try:
        r = requests.get(url, timeout=10)
        return r.text if r.status_code == 200 else None
    except:
        return None

def _parse_cnb(txt: str, code: str):
    if not txt: return None, None
    lines = txt.splitlines()
    header = lines[0].split(" #")[0].strip() if lines else None
    for line in lines[2:]:
        parts = line.strip().split("|")
        if len(parts) == 5:
            _, _, qty, ccode, rate = parts
            if ccode == code:
                try:
                    qty = float(qty.replace(",", "."))
                    rate = float(rate.replace(",", "."))
                    return rate / qty, header
                except:
                    return None, header
    return None, header

def get_rate_for(code: str, d: dt_date):
    if code == "CZK": return 1.0, d.isoformat()
    d_str = d.strftime("%d.%m.%Y")
    txt = _fetch_txt(CNB_TXT_DAILY_AT.format(date=d_str))
    rate, header = _parse_cnb(txt, code)
    if not rate:
        txt2 = _fetch_txt(CNB_TXT_DAILY)
        rate, header = _parse_cnb(txt2, code)
        rdate = datetime.today().date().isoformat()
    else:
        rdate = datetime.strptime(header, "%d.%m.%Y").date().isoformat()
    return rate, rdate

# -------------------------------
# Calendarific – sviatky
# -------------------------------
@st.cache_data(ttl=3600)
def get_holiday(iso2: str, d: dt_date):
    try:
        url = f"https://calendarific.com/api/v2/holidays?api_key={CALENDARIFIC_API_KEY}&country={iso2}&year={d.year}&month={d.month}&day={d.day}"
        r = requests.get(url)
        data = r.json()
        holidays = data.get("response", {}).get("holidays", [])
        if holidays:
            return holidays[0]["name"]
    except:
        return None
    return None

def translate_holiday(name, lang="sk"):
    translations = {
        "Christmas Eve": {
            "sk": "Štedrý večer (Vianoce)",
            "cz": "Štědrý večer (Vánoce)",
            "en": "Christmas Eve"
        },
        "Harvest Festival": {
            "sk": "Dožinky / Jesenný festival",
            "cz": "Dožínky / Podzimní festival",
            "en": "Harvest Festival"
        },
        "New Year's Day": {
            "sk": "Nový rok",
            "cz": "Nový rok",
            "en": "New Year’s Day"
        }
    }
    return translations.get(name, {}).get(lang, name)

# -------------------------------
# Hlášky podľa sezóny
# -------------------------------
def get_issuecoin_message(date_obj):
    m = date_obj.month
    if m in [12, 1, 2]:
        return "❄️ Krásne sviatky! Teplý čaj a teplý rozpočet. ☕"
    elif m in [3, 4, 5]:
        return "🌸 Jarný štart — malé kroky robia silný rozpočet. 💪"
    elif m in [6, 7, 8]:
        return "😎 Letná pohoda — uži si slnko a účtenky drž v chládku. 🌞"
    else:
        return "🍂 Jesenná pohoda — nech sú výdavky ako lesná prechádzka: pokojné. 🍁"

# -------------------------------
# Panáčik IssueCoin – HLAVA NAD TELOM
# -------------------------------
def render_issuecoin(style="default"):
    if style == "winter":
        head = "🧑‍🎄"
        accessory = "🧣"  # šál
    elif style == "spring":
        head = "🙂"
        accessory = "💪💪"  # ruky cvičia
    elif style == "summer":
        head = "🕶️"
        accessory = ""  # okuliare sú hlava
    elif style == "autumn":
        head = "🧑"
        accessory = "🍄🍄"  # huby
    else:
        head = "🧍"
        accessory = ""

    body = "/|\\"
    legs = "/ \\"

    html = f"""
    <div style='text-align:center;font-size:26px;line-height:1.1;margin:8px 0;'>
      <div>{head}</div>
      <div>{accessory}</div>
      <div>{body}</div>
      <div>{legs}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------
# DATABÁZA
# -------------------------------
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date","Country","Currency","Amount","Category","Shop","Note","Converted_CZK","Rate_value","Rate_date"
    ])

# -------------------------------
# UI
# -------------------------------
st.title("💰 Výdavkový denník / Expense Diary")

date_val = st.date_input("📅 Dátum nákupu / Purchase date", value=datetime.today())
country_label = st.selectbox("🌍 Krajina + mena / Country + currency", COUNTRIES)
amount = st.number_input("💵 Čiastka / Amount", min_value=0.0, step=1.0)
category = st.selectbox("📁 Kategória / Category", ["Potraviny 🛒", "Doprava 🚗", "Zábava 🎮", "Drogéria 🧴", "Ostatné 💼"])
shop = st.text_input("🏪 Obchod / miesto / Shop / place")
note = st.text_input("📝 Poznámka / Note")

if st.button("💾 Uložiť nákup / Save purchase"):
    code, iso2 = COUNTRY_TO_CODE[country_label]
    rate, rdate = get_rate_for(code, date_val)
    czk_value = amount * rate if rate else 0

    new_row = {
        "Date": date_val,
        "Country": country_label,
        "Currency": code,
        "Amount": amount,
        "Category": category,
        "Shop": shop,
        "Note": note,
        "Converted_CZK": round(czk_value, 2),
        "Rate_value": round(rate, 2) if rate else None,
        "Rate_date": rdate,
    }
    st.session_state["expenses"] = pd.concat([st.session_state["expenses"], pd.DataFrame([new_row])], ignore_index=True)
    st.success(f"Záznam uložený! ({round(czk_value,2)} CZK) — Použitý kurz: {round(rate,2)} CZK/1 {code} (k {rdate})")

    # Panáčik podľa sezóny
    style = "winter" if date_val.month in [12,1,2] else "spring" if date_val.month in [3,4,5] else "summer" if date_val.month in [6,7,8] else "autumn"
    render_issuecoin(style)

    # Sviatok
    holiday_name = get_holiday(iso2, date_val)
    if holiday_name:
        lang = "cz" if "Česko" in country_label else "sk"
        translated = translate_holiday(holiday_name, lang)
        st.markdown(f"🎉 Dnes je sviatok: **{translated}**")

    # Hláška
    st.info(get_issuecoin_message(date_val))

# -------------------------------
# TABUĽKA
# -------------------------------
if len(st.session_state["expenses"]) > 0:
    st.markdown("🧾 **Zoznam nákupov / Seznam nákupů**")
    st.dataframe(st.session_state["expenses"])
