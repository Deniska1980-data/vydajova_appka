import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date

# ---------------------------------
# CONFIG & CSS
# ---------------------------------
st.set_page_config(page_title="Expense Diary", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px;
    line-height: 1.6;
}
h1 { font-size: 28px !important; }
.stButton>button {
    font-size: 18px;
    padding: 10px 20px;
}
.issuecoin {
    display: flex;
    align-items: center;
    gap: 10px;
}
.issuecoin img {
    width: 60px;
    border-radius: 50%;
    animation: wink 5s infinite;
}
@keyframes wink {
    0%, 90%, 100% { filter: brightness(1); }
    95% { filter: brightness(0.5); }
}
.gdpr-box {
    background-color: #f0f2f6;
    border-left: 6px solid #4CAF50;
    padding: 12px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------
# LANGUAGE SWITCH + ISSUECOIN
# ---------------------------------
col_lang, col_icon = st.columns([8, 2])
with col_lang:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"
with col_icon:
    st.markdown(
        f'<div class="issuecoin">'
        f'<img src="maly_IssueCoin.JPG" alt="IssueCoin agent" title="IssueCoin here 👋">'
        f'</div>',
        unsafe_allow_html=True
    )

# ---------------------------------
# TEXTS
# ---------------------------------
TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB.",
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "category": "📂 Kategória / Kategorie",
        "shop": "🏬 Obchod / miesto",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť nákup / Uložit nákup",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "export": "💾 Exportovať do CSV",
        "gdpr": "ℹ️ Táto aplikácia neukladá žiadne osobné údaje. Dáta sú spracovávané iba lokálne vo vašom zariadení."
    },
    "en": {
        "app_title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates.",
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "category": "📂 Category",
        "shop": "🏬 Shop / place",
        "note": "📝 Note",
        "save": "💾 Save purchase",
        "list": "🧾 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "export": "💾 Export CSV",
        "gdpr": "ℹ️ This app does not store or send any personal data. All data stay local on your device."
    }
}

# ---------------------------------
# CATEGORIES
# ---------------------------------
CATEGORIES = {
    "sk": [
        "Potraviny 🛒 / Potraviny 🛒",
        "Drogérie 🧴 / Drogérie 🧴",
        "Odevy 👕 / Oblečení 👕",
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

# ---------------------------------
# CNB HELPERS
# ---------------------------------
@st.cache_data(ttl=600)
def fetch_cnb_txt(date_str: str):
    url = f"https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt?date={date_str}"
    r = requests.get(url, timeout=10)
    return r.text if r.status_code == 200 else None

@st.cache_data(ttl=600)
def fetch_cnb_txt_latest():
    url = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
    r = requests.get(url, timeout=10)
    return r.text if r.status_code == 200 else None

def parse_rate_from_txt(txt: str, code: str):
    if not txt: return None, None, None
    lines = txt.splitlines()
    header_date = lines[0].split(" #")[0].strip() if lines else None
    for line in lines[2:]:
        parts = line.strip().split("|")
        if len(parts) == 5:
            _, _, qty, c_code, rate = parts
            if c_code == code:
                qty_f = float(qty.replace(",", "."))
                rate_f = float(rate.replace(",", "."))
                return rate_f, qty_f, header_date
    return None, None, header_date

def get_rate_for(code: str, d: dt_date):
    d_str = d.strftime("%d.%m.%Y")
    txt = fetch_cnb_txt(d_str)
    rate, qty, header_date = parse_rate_from_txt(txt, code)
    if rate is None:
        txt2 = fetch_cnb_txt_latest()
        rate, qty, header_date = parse_rate_from_txt(txt2, code)
        rate_date_iso = datetime.today().date().isoformat()
    else:
        rate_date_iso = datetime.strptime(header_date, "%d.%m.%Y").date().isoformat()
    return (rate/qty if rate else None), rate_date_iso

# ---------------------------------
# HOLIDAY CHECK (Calendarific)
# ---------------------------------
API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"
def check_holiday(country_code, d):
    try:
        url = f"https://calendarific.com/api/v2/holidays?api_key={API_KEY}&country={country_code}&year={d.year}&month={d.month}&day={d.day}"
        r = requests.get(url, timeout=10)
        data = r.json()
        holidays = data.get("response", {}).get("holidays", [])
        return holidays[0]["name"] if holidays else None
    except:
        return None

# ---------------------------------
# STATE INIT
# ---------------------------------
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=["Date", "Country", "Currency", "Amount", "Category", "Shop", "Note", "Converted_CZK", "Rate_value", "Rate_date"])

# ---------------------------------
# HEADER & GDPR
# ---------------------------------
st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])
st.markdown(f'<div class="gdpr-box">{TEXTS[LANG]["gdpr"]}</div>', unsafe_allow_html=True)

# ---------------------------------
# INPUT FORM
# ---------------------------------
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today())
        country = st.text_input(TEXTS[LANG]["country"], value="CZ")
        category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    with col2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, step=1.0)
        shop = st.text_input(TEXTS[LANG]["shop"])
        note = st.text_input(TEXTS[LANG]["note"])
    submit = st.form_submit_button(TEXTS[LANG]["save"])

# ---------------------------------
# SAVE + ISSUECOIN LOGIC
# ---------------------------------
if submit:
    per_unit, rate_date = get_rate_for("CZK", d)
    converted = round(amount * per_unit, 2) if per_unit else amount
    df = st.session_state["expenses"]

    df.loc[len(df)] = [d.isoformat(), country, "CZK", amount, category, shop, note, converted, per_unit, rate_date]
    st.success(f"{TEXTS[LANG]['save']} ✅ {converted} CZK")

    # --- AI logic for limits ---
    msg = ""
    if ("Zábava" in category or "Restaurants" in category) and amount > 1000:
        msg = "🎉 Užívaj, ale nezabudni aj šetriť! 😉" if LANG == "sk" else "🎉 Enjoy, but save a bit for later! 😉"
    elif amount > 6500:
        msg = "💰 To bol veľký nákup! Dúfam, že to stálo za to. 😄" if LANG == "sk" else "💰 Big purchase! Hope it was worth it. 😄"
    elif amount > 2500:
        msg = "🛒 Výdavky rastú, ale všetko s mierou. 🙂" if LANG == "sk" else "🛒 Spending more — keep it balanced. 🙂"

    # --- Check holiday ---
    holiday_name = check_holiday(country, d)
    if holiday_name:
        msg = f"🎉 Dnes je {holiday_name}! Užívaj deň voľna. 😄" if LANG == "sk" else f"🎉 Today is {holiday_name}! Enjoy your day off. 😄"

    if msg:
        st.markdown(
            f"""
            <div class="issuecoin">
                <img src="maly_IssueCoin.JPG" alt="IssueCoin" />
                <div><b>IssueCoin:</b> {msg}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------
# LIST + SUMMARY
# ---------------------------------
st.subheader(TEXTS[LANG]["list"])
st.dataframe(st.session_state["expenses"], use_container_width=True)

if not st.session_state["expenses"].empty:
    st.subheader(TEXTS[LANG]["summary"])
    total = st.session_state["expenses"]["Converted_CZK"].sum()
    st.metric(TEXTS[LANG]["total"], f"{total:.2f} CZK")

    chart = (
        alt.Chart(st.session_state["expenses"])
        .mark_bar()
        .encode(
            x="Category",
            y="Converted_CZK",
            tooltip=["Category", "Converted_CZK"]
        )
    )
    st.altair_chart(chart, use_container_width=True)

    csv = st.session_state["expenses"].to_csv(index=False).encode("utf-8")
    st.download_button(TEXTS[LANG]["export"], csv, f"expenses_{dt_date.today().isoformat()}.csv", "text/csv")
