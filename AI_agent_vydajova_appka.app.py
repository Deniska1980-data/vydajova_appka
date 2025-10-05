import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date
import os

# --------------------------------------
# PAGE CONFIG
# --------------------------------------
st.set_page_config(page_title="Expense Diary", layout="wide")

# --------------------------------------
# LOAD ISSUECOIN MESSAGES
# --------------------------------------
# Načítanie CSV s hláškami IssueCoin
@st.cache_data
def load_messages_csv():
    try:
        return pd.read_csv("AI_agent_kategorie_hlasky.csv", delimiter=";", encoding="utf-8")
    except Exception as e:
        st.error(f"❌ Nepodarilo sa načítať súbor s hláškami IssueCoin: {e}")
        return pd.DataFrame()

messages_df = load_messages_csv()

# --------------------------------------
# CUSTOM CSS
# --------------------------------------
st.markdown("""
<style>
.issuecoin-container {
    display: flex;
    align-items: center;
    gap: 15px;
    background-color: #f0f8ff;
    border: 2px solid #0078D7;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 15px 0;
}
.issuecoin-img {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 2px solid #0078D7;
}
.issuecoin-text {
    font-size: 18px;
    color: #003366;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------
# CNB API – exchange rates
# --------------------------------------
@st.cache_data(ttl=3600)
def get_cnb_rates(selected_date):
    url = f"https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt?date={selected_date.strftime('%d.%m.%Y')}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"CZK": 1.0}

    rates = {"CZK": 1.0}
    for line in response.text.split("\n")[2:]:
        if not line.strip():
            continue
        parts = line.split("|")
        try:
            country, currency, amount, code, rate = parts
            rates[code.strip()] = float(rate.replace(",", ".")) / float(amount)
        except:
            continue
    return rates

# --------------------------------------
# COUNTRIES + CURRENCIES
# --------------------------------------
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

# --------------------------------------
# UI
# --------------------------------------
st.title("💰 Výdavkový denník / Výdajový deník")

language = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"])

today = dt_date.today()
selected_date = st.date_input("📅 Dátum nákupu / Datum nákupu", today)
selected_country = st.selectbox("🌍 Krajina + mena / Měna", COUNTRIES["sk"] if "Slovensky" in language else COUNTRIES["en"])
selected_currency = COUNTRY_TO_CODE[selected_country]

amount = st.number_input("💵 Suma / Částka", min_value=0.0, step=1.0)
shop = st.text_input("🏪 Obchod / miesto / Obchod / místo")
category = st.selectbox(
    "🧾 Kategória / Kategorie",
    [
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
    ]
)

note = st.text_input("📝 Poznámka")

# --------------------------------------
# Exchange conversion
# --------------------------------------
rates = get_cnb_rates(selected_date)
rate = rates.get(selected_currency, 1)
converted = amount * rate
st.write(f"💱 Prepočítaná hodnota v CZK: **{converted:.2f} Kč**")

# --------------------------------------
# AI Agent IssueCoin message
# --------------------------------------
def show_issuecoin_message():
    if messages_df.empty:
        return

    # výber správneho jazykového stĺpca
    if "slovensky" in language.lower():
        msg_col = "Hláška_SK_CZ"
        cat_col = "Kategória/kategorie (SK_CZ)"
    else:
        msg_col = "Hláška_EN"
        cat_col = "Category (EN)"

    # výber správneho riadku podľa kategórie
    if cat_col in messages_df.columns and msg_col in messages_df.columns:
        row = messages_df[messages_df[cat_col] == category]
        if not row.empty:
            msg = row[msg_col].sample(1).iloc[0]
            st.markdown(f"""
            <div class="issuecoin-container">
                <img src="obrazek_IssueCoin_by_Deny.JPG" class="issuecoin-img" />
                <div class="issuecoin-text">{msg}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Pre túto kategóriu zatiaľ nemám hlášku.")
    else:
        st.error("❌ CSV nemá očakávané názvy stĺpcov.")


# zobrazenie hlášky, ak je zadaná suma
if amount > 0:
    show_issuecoin_message()

# ----------------------------
# Uloženie záznamu do CSV
# ----------------------------

import pandas as pd
from datetime import datetime
import os

# Tlačidlo uloženia
if st.button("💾 Uložiť záznam"):
    if amount and category:
        # Pripravíme nový záznam
        new_record = {
            "Dátum nákupu": date.strftime("%Y-%m-%d") if "date" in locals() else datetime.now().strftime("%Y-%m-%d"),
            "Krajina + mena": country_currency,
            "Suma": amount,
            "Obchod / miesto": store if "store" in locals() else "",
            "Kategória": category,
            "Poznámka": note if "note" in locals() else "",
            "Prepočítaná hodnota v CZK": converted_value
        }

        file_name = "vydavky_data.csv"

        # Ak súbor existuje, pridaj riadok, inak vytvor nový
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        else:
            df = pd.DataFrame([new_record])

        df.to_csv(file_name, index=False, encoding="utf-8-sig")

        st.success("✅ Záznam bol úspešne uložený!")
    else:
        st.warning("⚠️ Zadaj aspoň sumu a kategóriu pred uložením.")




