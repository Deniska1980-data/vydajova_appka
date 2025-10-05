# app.py  — Expense Diary (SK/CZ + EN) with CNB, Calendarific and IssueCoin thresholds

import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date

st.set_page_config(page_title="Expense Diary", layout="wide")

# ---------------------------
# Custom CSS (clean UI + IssueCoin card)
# ---------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 16px; line-height: 1.6; }
h1 { font-size: 28px !important; }
h2 { font-size: 22px !important; }
.stButton>button { font-size: 16px; padding: 8px 16px; }
.issuecoin {
  border: 1px solid #BBD7FF;
  background: #ECF5FF;
  padding: 14px 16px;
  border-radius: 12px;
  display: flex; gap: 14px; align-items: center;
}
.issuecoin img {
  width: 44px; height: 44px; border-radius: 50%;
  object-fit: cover; border: 1px solid #aac8ff; background: white;
}
.issuecoin .text { font-size: 16px; }
.gdpr {
  border-left: 6px solid #4CAF50;
  background: #F2FFF2; padding: 12px 14px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Language switch
# ---------------------------
left, right = st.columns([7, 3])
with right:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

# ---------------------------
# Translations
# ---------------------------
T = {
    "sk": {
        "title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": ("CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB. "
                     "Ak pre vybraný deň nie je kurz, použije sa posledný dostupný kurz."),
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "category": "📂 Kategória / Kategorie",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť záznam",
        "saved": "Záznam uložený!",
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "rate_info": "Použitý kurz",
        "rate_from": "k",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "export": "💾 Exportovať do CSV",
        "gdpr": "Táto aplikácia neukladá tvoje údaje na server. Všetky dáta ostávajú len u teba v prehliadači.",
        "holiday": "Dnes je sviatok/voľno: {name} – {desc}",
        "issuecoin_default": "IssueCoin hlási:"
    },
    "en": {
        "title": "💰 Expense Diary",
        "subtitle": ("CZK = always 1:1. Other currencies follow CNB daily rates. "
                     "If the rate for the selected day is missing, the last available rate is used."),
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "shop": "🏬 Shop / place",
        "category": "📂 Category",
        "note": "📝 Note",
        "save": "💾 Save entry",
        "saved": "Saved!",
        "rate_err": "❌ Could not fetch exchange rate.",
        "rate_info": "Applied rate",
        "rate_from": "as of",
        "list": "🧾 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "export": "💾 Export CSV",
        "gdpr": "This app does not store your data on any server. All information stays locally in your browser.",
        "holiday": "Holiday/observance today: {name} – {desc}",
        "issuecoin_default": "IssueCoin says:"
    }
}

# ---------------------------
# Countries + currencies (label → currency code)
# ---------------------------
COUNTRIES = {
    "sk": [
        "Česko – CZK Kč", "Slovensko – EUR €", "Nemecko – EUR € / Německo – EUR €",
        "Rakúsko – EUR € / Rakousko – EUR €", "Francúzsko – EUR € / Francie – EUR €",
        "Španielsko – EUR € / Španělsko – EUR €", "Taliansko – EUR € / Itálie – EUR €",
        "Holandsko – EUR € / Nizozemsko – EUR €", "Belgicko – EUR € / Belgie – EUR €",
        "Fínsko – EUR € / Finsko – EUR €", "Írsko – EUR € / Irsko – EUR €", "Portugalsko – EUR €",
        "Grécko – EUR € / Řecko – EUR €", "Slovinsko – EUR €", "Litva – EUR €", "Lotyšsko – EUR €",
        "Estónsko – EUR €", "Malta – EUR €", "Cyprus – EUR €", "Chorvátsko – EUR € / Chorvatsko – EUR €",
        "USA – USD $", "Veľká Británia – GBP £ / Velká Británie – GBP £",
        "Poľsko – PLN zł / Polsko – PLN zł", "Maďarsko – HUF Ft", "Švajčiarsko – CHF ₣ / Švýcarsko – CHF ₣",
        "Dánsko – DKK kr", "Švédsko – SEK kr", "Nórsko – NOK kr", "Kanada – CAD $", "Japonsko – JPY ¥"
    ],
    "en": [
        "Czechia – CZK Kč", "Slovakia – EUR €", "Germany – EUR €", "Austria – EUR €", "France – EUR €",
        "Spain – EUR €", "Italy – EUR €", "Netherlands – EUR €", "Belgium – EUR €", "Finland – EUR €",
        "Ireland – EUR €", "Portugal – EUR €", "Greece – EUR €", "Slovenia – EUR €", "Lithuania – EUR €",
        "Latvia – EUR €", "Estonia – EUR €", "Malta – EUR €", "Cyprus – EUR €", "Croatia – EUR €",
        "USA – USD $", "United Kingdom – GBP £", "Poland – PLN zł", "Hungary – HUF Ft", "Switzerland – CHF ₣",
        "Denmark – DKK kr", "Sweden – SEK kr", "Norway – NOK kr", "Canada – CAD $", "Japan – JPY ¥"
    ]
}

# label → 3-letter currency (for CNB)
COUNTRY_TO_CURR = {}
for label in COUNTRIES["sk"] + COUNTRIES["en"]:
    code = label.split("–")[-1].strip().split()[0]
    COUNTRY_TO_CURR[label] = code

# label → 2-letter ISO (for Calendarific)
ISO2 = {
    "Czechia – CZK Kč": "CZ", "Česko – CZK Kč": "CZ",
    "Slovakia – EUR €": "SK", "Slovensko – EUR €": "SK",
    "Germany – EUR €": "DE", "Nemecko – EUR € / Německo – EUR €": "DE",
    "Austria – EUR €": "AT", "Rakúsko – EUR € / Rakousko – EUR €": "AT",
    "France – EUR €": "FR", "Francúzsko – EUR € / Francie – EUR €": "FR",
    "Spain – EUR €": "ES", "Španielsko – EUR € / Španělsko – EUR €": "ES",
    "Italy – EUR €": "IT", "Taliansko – EUR € / Itálie – EUR €": "IT",
    "Netherlands – EUR €": "NL", "Holandsko – EUR € / Nizozemsko – EUR €": "NL",
    "Belgium – EUR €": "BE", "Belgicko – EUR € / Belgie – EUR €": "BE",
    "Finland – EUR €": "FI", "Fínsko – EUR € / Finsko – EUR €": "FI",
    "Ireland – EUR €": "IE", "Írsko – EUR € / Irsko – EUR €": "IE",
    "Portugal – EUR €": "PT", "Portugalsko – EUR €": "PT",
    "Greece – EUR €": "GR", "Grécko – EUR € / Řecko – EUR €": "GR",
    "Slovenia – EUR €": "SI", "Slovinsko – EUR €": "SI",
    "Lithuania – EUR €": "LT", "Litva – EUR €": "LT",
    "Latvia – EUR €": "LV", "Lotyšsko – EUR €": "LV",
    "Estonia – EUR €": "EE", "Estónsko – EUR €": "EE",
    "Malta – EUR €": "MT", "Cyprus – EUR €": "CY",
    "Croatia – EUR €": "HR", "Chorvátsko – EUR € / Chorvatsko – EUR €": "HR",
    "USA – USD $": "US", "United Kingdom – GBP £": "GB",
    "Veľká Británia – GBP £ / Velká Británie – GBP £": "GB",
    "Poland – PLN zł": "PL", "Poľsko – PLN zł / Polsko – PLN zł": "PL",
    "Hungary – HUF Ft": "HU", "Maďarsko – HUF Ft": "HU",
    "Switzerland – CHF ₣": "CH", "Švajčiarsko – CHF ₣ / Švýcarsko – CHF ₣": "CH",
    "Denmark – DKK kr": "DK", "Dánsko – DKK kr": "DK",
    "Sweden – SEK kr": "SE", "Švédsko – SEK kr": "SE",
    "Norway – NOK kr": "NO", "Nórsko – NOK kr": "NO",
    "Canada – CAD $": "CA", "Kanada – CAD $": "CA",
    "Japan – JPY ¥": "JP", "Japonsko – JPY ¥": "JP"
}

# ---------------------------
# App state
# ---------------------------
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date", "Country", "Currency", "Amount", "Category", "Shop", "Note",
        "Converted_CZK", "Rate_value", "Rate_date"
    ])
if "gdpr_shown" not in st.session_state:
    st.session_state["gdpr_shown"] = False

# ---------------------------
# CNB helpers (TXT feed)
# ---------------------------
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
                try:
                    qty_f = float(qty.replace(",", "."))
                    rate_f = float(rate.replace(",", "."))
                    return rate_f, qty_f, header_date
                except:  # noqa
                    return None, None, header_date
    return None, None, header_date

def get_rate_for(code: str, d: dt_date):
    if code == "CZK":
        return 1.0, d.isoformat()
    d_str = d.strftime("%d.%m.%Y")
    txt = fetch_cnb_txt(d_str)
    rate, qty, header_date = parse_rate_from_txt(txt, code)
    if rate is None:
        txt2 = fetch_cnb_txt_latest()
        rate, qty, header_date = parse_rate_from_txt(txt2, code)
        rate_date_iso = datetime.today().date().isoformat()
    else:
        rate_date_iso = datetime.strptime(header_date, "%d.%m.%Y").date().isoformat()
    if rate is None or not qty:
        return None, None
    return rate / qty, rate_date_iso

# ---------------------------
# Calendarific (holidays) — show only when there IS a holiday
# ---------------------------
CALENDARIFIC_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"  # tvoj kľúč

@st.cache_data(ttl=3600)
def get_holiday_for(iso_country: str, d: dt_date):
    """Return first holiday dict or None."""
    try:
        params = {
            "api_key": CALENDARIFIC_KEY,
            "country": iso_country,
            "year": d.year,
            "month": d.month,
            "day": d.day
        }
        r = requests.get("https://calendarific.com/api/v2/holidays", params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        holidays = data.get("response", {}).get("holidays", [])
        return holidays[0] if holidays else None
    except Exception:
        return None

# ---------------------------
# IssueCoin thresholds & messages
# ---------------------------
ISSUECOIN_LIMITS = {
    # exact EN names + SK/CZ variants we use in selectboxes
    "Entertainment 🎉": 1000,
    "Zábava 🎉 / Zábava 🎉": 1000,
    "Restaurants & Bars 🍽️": 1000,
    "Reštaurácie a bary 🍽️ / Restaurace a bary 🍽️": 1000,
    # default for all others if not matched: 2500 CZK
}

def category_limit(category: str):
    return ISSUECOIN_LIMITS.get(category, 2500)

def issuecoin_message(category: str, amount_czk: float):
    # minimalistické, priateľské hlášky
    if "Restaur" in category or "Reštaur" in category:
        return "🍽️ Skvelé jedlo si treba užiť – len sleduj rozpočet 😉"
    if "Entertainment" in category or "Zábava" in category:
        return "🎉 Paráda! Trochu zábavy je zdravé – len nech to nebolí peňaženku 😉"
    if "Groc" in category or "Potraviny" in category:
        return "🛒 Nákupy idú – držíš to pod kontrolou."
    if "Drog" in category or "Drugstore" in category:
        return "🧴 Domácnosť je zásobená. 👍"
    return "✅ Výdavok zaznamenaný – len pripomienka držať si cieľ."

def show_issuecoin_card(text: str, title: str = "IssueCoin"):
    st.markdown(
        f"""
        <div class="issuecoin">
            <img src="obrazek_IssuaCoin_by_Deny.JPG" alt="IssueCoin"/>
            <div class="text"><b>{title}</b><br/>{text}</div>
        </div>
        """, unsafe_allow_html=True
    )

# ---------------------------
# GDPR note (once per session)
# ---------------------------
if not st.session_state["gdpr_shown"]:
    st.info(f"ℹ️ {T[LANG]['gdpr']}")
    st.session_state["gdpr_shown"] = True

# ---------------------------
# UI header
# ---------------------------
st.title(T[LANG]["title"])
st.caption(T[LANG]["subtitle"])

# ---------------------------
# Input form
# ---------------------------
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input(T[LANG]["date"], value=dt_date.today(), min_value=dt_date(2024, 1, 1))
        country = st.selectbox(T[LANG]["country"], COUNTRIES[LANG])
        category = st.selectbox(
            T[LANG]["category"],
            [
                # SK/CZ blok
                "Potraviny 🛒 / Potraviny 🛒" if LANG == "sk" else "Groceries 🛒",
                "Drogérie 🧴 / Drogérie 🧴" if LANG == "sk" else "Drugstore 🧴",
                "Doprava 🚌 / Doprava 🚌" if LANG == "sk" else "Transport 🚌",
                "Reštaurácie a bary 🍽️ / Restaurace a bary 🍽️" if LANG == "sk" else "Restaurants & Bars 🍽️",
                "Zábava 🎉 / Zábava 🎉" if LANG == "sk" else "Entertainment 🎉",
                "Odevy 👕 / Oblečení 👕" if LANG == "sk" else "Clothing 👕",
                "Obuv 👟 / Obuv 👟" if LANG == "sk" else "Shoes 👟",
                "Elektronika 💻 / Elektronika 💻" if LANG == "sk" else "Electronics 💻",
                "Domácnosť / nábytok 🛋️ / Domácnost / nábytek 🛋️" if LANG == "sk" else "Household / Furniture 🛋️",
                "Šport a voľný čas 🏀 / Sport a volný čas 🏀" if LANG == "sk" else "Sports & Leisure 🏀",
                "Zdravie a lekáreň 💊 / Zdraví a lékárna 💊" if LANG == "sk" else "Health & Pharmacy 💊",
                "Cestovanie / dovolenka ✈️ / Cestování / dovolená ✈️" if LANG == "sk" else "Travel / Holiday ✈️",
                "Vzdelávanie / kurzy 📚 / Vzdělávání / kurzy 📚" if LANG == "sk" else "Education / Courses 📚"
            ]
        )
    with col2:
        amount = st.number_input(T[LANG]["amount"], min_value=0.0, step=1.0, format="%.2f")
        shop = st.text_input(T[LANG]["shop"])
        note = st.text_input(T[LANG]["note"])

    submit = st.form_submit_button(T[LANG]["save"])

# ---------------------------
# Submit logic
# ---------------------------
if submit:
    curr = COUNTRY_TO_CURR.get(country, "CZK")
    per_unit, rate_date = get_rate_for(curr, d)

    if per_unit is None:
        st.error(T[LANG]["rate_err"])
    else:
        converted = round(amount * per_unit, 2)
        new_row = pd.DataFrame([{
            "Date": d.isoformat(),
            "Country": country,
            "Currency": curr,
            "Amount": float(amount),
            "Category": category,
            "Shop": shop,
            "Note": note,
            "Converted_CZK": converted,
            "Rate_value": round(per_unit, 4),
            "Rate_date": rate_date
        }])
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)

        st.success(
            f"{T[LANG]['saved']} → {converted:.2f} CZK "
            f"(1 {curr} = {1/per_unit:.4f} CZK, {T[LANG]['rate_from']} {rate_date})"
            if curr != "CZK"
            else f"{T[LANG]['saved']} → {converted:.2f} CZK (1 CZK = 1.0000 CZK, {rate_date})"
        )

        # --- Holiday message (only if there is a holiday)
        iso2 = ISO2.get(country)
        if iso2:
            holiday = get_holiday_for(iso2, d)
            if holiday:
                hname = holiday.get("name", "")
                hdesc = holiday.get("description", "")
                show_issuecoin_card(T[LANG]["holiday"].format(name=hname, desc=hdesc), title="🎉 IssueCoin")

        # --- IssueCoin thresholds (only when exceeded)
        limit = category_limit(category)
        if converted >= limit:
            msg = issuecoin_message(category, converted)
            show_issuecoin_card(msg, title="💬 IssueCoin")

# ---------------------------
# List + summary
# ---------------------------
st.subheader(T[LANG]["list"])
df = st.session_state["expenses"]
st.dataframe(df, use_container_width=True)

if not df.empty:
    st.subheader(T[LANG]["summary"])
    total = df["Converted_CZK"].sum()
    st.metric(T[LANG]["total"], f"{total:.2f} CZK")

    grouped = df.groupby("Category")["Converted_CZK"].sum().reset_index()
    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("Category", sort="-y", title=T[LANG]["category"]),
            y=alt.Y("Converted_CZK", title="CZK"),
            tooltip=["Category", "Converted_CZK"]
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)

    # Export
    csv = df.to_csv(index=False).encode("utf-8")
    file_name = f"expenses_{dt_date.today().isoformat()}.csv"
    st.download_button(label=T[LANG]["export"], data=csv, file_name=file_name, mime="text/csv")
