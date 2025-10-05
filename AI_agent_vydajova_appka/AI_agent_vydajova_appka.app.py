import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="Expense Diary", layout="wide")

# ---------------------------
# CUSTOM CSS
# ---------------------------
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 16px;  
        line-height: 1.6;
    }
    h1 { font-size: 28px !important; }
    h2 { font-size: 24px !important; }
    h3 { font-size: 20px !important; }
    .stButton>button {
        font-size: 18px;
        padding: 10px 20px;
    }
    .stSelectbox>div>div {
        font-size: 16px;
    }
    .issuecoin-box {
        display: flex;
        align-items: center;
        background-color: #E8F4FF;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0px 0px 6px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .issuecoin-img {
        width: 80px;
        margin-right: 15px;
    }
    .issuecoin-text {
        font-size: 18px;
        color: #003366;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# LANGUAGE SWITCH
# ---------------------------
left, right = st.columns([7, 3])
with right:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

# ---------------------------
# LOAD AI AGENT MESSAGES FROM CSV
# ---------------------------
@st.cache_data
def load_messages_csv():
    df = pd.read_csv("AI_agent_vydajova_appka/hlasky_kategorie_SK_CZ_EN.csv")
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    hlasky_df = load_messages_csv()
except Exception as e:
    st.error("❌ Nepodarilo sa načítať súbor s hláškami IssueCoin.")
    hlasky_df = pd.DataFrame()

def get_agent_message(category, lang):
    """Return IssueCoin message for given category and language."""
    if hlasky_df.empty:
        return None
    if lang == "sk":
        col_lang = "SK_CZ"
    else:
        col_lang = "EN"

    match = hlasky_df[hlasky_df["category"].str.lower().str.contains(category.split()[0].lower(), na=False)]
    if not match.empty:
        return match.iloc[0][col_lang]
    return None

# ---------------------------
# TEXTS
# ---------------------------
TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB. "
                    "Ak pre vybraný deň nie je kurz, použije sa posledný dostupný kurz.",
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "category": "📂 Kategória / Kategorie",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť nákup / Uložit nákup",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "saved_ok": "Záznam uložený!",
        "rate_info": "Použitý kurz",
        "rate_from": "k",
        "export": "💾 Exportovať do CSV"
    },
    "en": {
        "app_title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates. "
                    "If no rate is available for the selected date, the last available rate is used.",
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
        "rate_err": "❌ Could not fetch exchange rate.",
        "saved_ok": "Saved!",
        "rate_info": "Applied rate",
        "rate_from": "as of",
        "export": "💾 Export CSV"
    }
}

# ---------------------------
# CATEGORIES
# ---------------------------
CATEGORIES = {
    "sk": [
        "Potraviny 🛒 / Potraviny 🛒",
        "Drogérie 🧴 / Drogérie 🧴",
        "Zábava 🎉 / Zábava 🎉",
        "Elektronika 💻 / Elektronika 💻",
        "Domácnosť / nábytok 🛋️ / Domácnost / nábytek 🛋️",
        "Odevy 👕 / Oblečení 👕",
        "Obuv 👟 / Obuv 👟",
        "Cestovanie / dovolenka ✈️ / Cestování / dovolená ✈️",
    ],
    "en": [
        "Groceries 🛒",
        "Drugstore 🧴",
        "Entertainment 🎉",
        "Electronics 💻",
        "Household / Furniture 🛋️",
        "Clothing 👕",
        "Shoes 👟",
        "Travel / Holiday ✈️",
    ]
}

# ---------------------------
# COUNTRIES + CURRENCIES (FULL)
# ---------------------------
COUNTRIES = {
    "sk": [
        "Česko – CZK Kč",
        "Slovensko – EUR €",
        "Nemecko – EUR € / Německo – EUR €",
        "Rakúsko – EUR € / Rakousko – EUR €",
        "Francúzsko – EUR € / Francie – EUR €",
        "Španielsko – EUR € / Španělsko – EUR €",
        "Taliansko – EUR € / Itálie – EUR €",
        "Holandsko – EUR € / Nizozemsko – EUR €",
        "Belgicko – EUR € / Belgie – EUR €",
        "Fínsko – EUR € / Finsko – EUR €",
        "Írsko – EUR € / Irsko – EUR €",
        "Portugalsko – EUR €",
        "Grécko – EUR € / Řecko – EUR €",
        "Slovinsko – EUR €",
        "Litva – EUR €",
        "Lotyšsko – EUR €",
        "Estónsko – EUR €",
        "Malta – EUR €",
        "Cyprus – EUR €",
        "Chorvátsko – EUR € / Chorvatsko – EUR €",
        "USA – USD $",
        "Veľká Británia – GBP £ / Velká Británie – GBP £",
        "Poľsko – PLN zł / Polsko – PLN zł",
        "Maďarsko – HUF Ft / Maďarsko – HUF Ft",
        "Švajčiarsko – CHF ₣ / Švýcarsko – CHF ₣",
        "Dánsko – DKK kr / Dánsko – DKK kr",
        "Švédsko – SEK kr / Švédsko – SEK kr",
        "Nórsko – NOK kr / Norsko – NOK kr",
        "Kanada – CAD $",
        "Japonsko – JPY ¥"
    ],
    "en": [
        "Czechia – CZK Kč",
        "Slovakia – EUR €",
        "Germany – EUR €",
        "Austria – EUR €",
        "France – EUR €",
        "Spain – EUR €",
        "Italy – EUR €",
        "Netherlands – EUR €",
        "Belgium – EUR €",
        "Finland – EUR €",
        "Ireland – EUR €",
        "Portugal – EUR €",
        "Greece – EUR €",
        "Slovenia – EUR €",
        "Lithuania – EUR €",
        "Latvia – EUR €",
        "Estonia – EUR €",
        "Malta – EUR €",
        "Cyprus – EUR €",
        "Croatia – EUR €",
        "USA – USD $",
        "United Kingdom – GBP £",
        "Poland – PLN zł",
        "Hungary – HUF Ft",
        "Switzerland – CHF ₣",
        "Denmark – DKK kr",
        "Sweden – SEK kr",
        "Norway – NOK kr",
        "Canada – CAD $",
        "Japan – JPY ¥"
    ]
}

COUNTRY_TO_CODE = {}
for label in COUNTRIES["sk"] + COUNTRIES["en"]:
    code = label.split("–")[-1].strip().split()[0]
    COUNTRY_TO_CODE[label] = code

# ---------------------------
# STATE INIT
# ---------------------------
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date", "Country", "Currency", "Amount", "Category", "Shop", "Note",
        "Converted_CZK", "Rate_value", "Rate_date"
    ])

# ---------------------------
# CNB API HELPERS
# ---------------------------
@st.cache_data(ttl=600)
def fetch_cnb_txt(date_str: str):
    url = f"https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt?date={date_str}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return None
    return r.text

@st.cache_data(ttl=600)
def fetch_cnb_txt_latest():
    url = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return None
    return r.text

def parse_rate_from_txt(txt: str, code: str):
    if not txt:
        return None, None, None
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
                except:
                    return None, None, header_date
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
    if rate is None or not qty:
        return None, None
    return rate/qty, rate_date_iso

# ---------------------------
# UI HEADER
# ---------------------------
st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])

# ---------------------------
# INPUT FORM
# ---------------------------
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today(), min_value=dt_date(2024,1,1))
        country = st.selectbox(TEXTS[LANG]["country"], COUNTRIES[LANG])
        category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    with col2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, step=1.0)
        shop = st.text_input(TEXTS[LANG]["shop"])
        note = st.text_input(TEXTS[LANG]["note"])
    submit = st.form_submit_button(TEXTS[LANG]["save"])

# ---------------------------
# SAVE + AI AGENT MESSAGE
# ---------------------------
if submit:
    code = COUNTRY_TO_CODE[country]
    per_unit, rate_date = (1.0, d.isoformat()) if code == "CZK" else get_rate_for(code, d)
    if per_unit is None:
        st.error(TEXTS[LANG]["rate_err"])
    else:
        converted = round(amount * per_unit, 2)
        new_row = pd.DataFrame([{
            "Date": d.isoformat(),
            "Country": country,
            "Currency": code,
            "Amount": amount,
            "Category": category,
            "Shop": shop,
            "Note": note,
            "Converted_CZK": converted,
            "Rate_value": round(per_unit, 4),
            "Rate_date": rate_date
        }])
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)
        st.success(f"{TEXTS[LANG]['saved_ok']} {converted} CZK — {TEXTS[LANG]['rate_info']}: {round(per_unit,4)} CZK/1 {code} ({TEXTS[LANG]['rate_from']} {rate_date})")

        # SUMS PER CATEGORY
        sums = st.session_state["expenses"].groupby("Category")["Converted_CZK"].sum()

        # LIMITS
        limits = {
            "Potraviny": 6500,
            "Zábava": 2000,
            "Drogérie": 2000,
            "Elektronika": 5000,
        }

        msg = None
        for key, val in limits.items():
            if any(k for k in sums.index if key in k and sums[k] > val):
                msg = get_agent_message(key, LANG)
                break

        if msg:
            st.markdown(f"""
                <div class="issuecoin-box">
                    <img src="AI_agent_vydajova_appka/obrazek_IssuaCoin_by_Deny.JPG" class="issuecoin-img" />
                    <div class="issuecoin-text">{msg}</div>
                </div>
            """, unsafe_allow_html=True)

# ---------------------------
# LIST + SUMMARY
# ---------------------------
st.subheader(TEXTS[LANG]["list"])
df = st.session_state["expenses"]
st.dataframe(df, use_container_width=True)

if not df.empty:
    st.subheader(TEXTS[LANG]["summary"])
    total = df["Converted_CZK"].sum()
    st.metric(TEXTS[LANG]["total"], f"{total:.2f} CZK")

    grouped = df.groupby("Category")["Converted_CZK"].sum().reset_index()
    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("Category", sort="-y", title=TEXTS[LANG]["category"]),
            y=alt.Y("Converted_CZK", title="CZK"),
            tooltip=["Category", "Converted_CZK"]
        )
        .properties(width=600, height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    file_name = f"expenses_{dt_date.today().isoformat()}.csv"
    st.download_button(
        label=TEXTS[LANG]["export"],
        data=csv,
        file_name=file_name,
        mime="text/csv",
    )

