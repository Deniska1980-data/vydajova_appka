import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Expense Diary / Výdavkový denník", layout="wide")

# -------------------------------------------------
# CSS (panáčik, bublina, jemné „mrknutie“)
# -------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 16px; line-height: 1.6; }
h1 { font-size: 28px !important; }
h2 { font-size: 24px !important; }
.stButton>button { font-size: 18px; padding: 10px 20px; }

.issuecoin-wrap { display:flex; align-items:center; gap:12px; margin-top:14px; }
.issuecoin-bubble {
  background:#eaf6ff; padding:12px 16px; border-radius:14px;
  box-shadow:2px 2px 6px rgba(0,0,0,0.08); font-size:16px;
}
.issuecoin-head { display:inline-block; animation: wink 7s infinite; }
@keyframes wink { 0%, 92%,100%{opacity:1;} 96%{opacity:0.3;} }

.issuecoin-figure { text-align:center; line-height:1; }
.issuecoin-body { font-family:monospace; font-size:18px; }
.gdpr { background:#f6faf7; border-left:6px solid #42b883; padding:12px 14px; border-radius:10px; }

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# LANGUAGE SWITCH
# -------------------------------------------------
top_l, top_r = st.columns([7, 3])
with top_r:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

# -------------------------------------------------
# TEXTS
# -------------------------------------------------
TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB. Ak pre vybraný deň nie je kurz, použije sa posledný dostupný kurz.",
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
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "saved_ok": "✅ Záznam uložený!",
        "rate_info": "Použitý kurz",
        "rate_from": "k",
        "export": "💾 Exportovať do CSV",
        "gdpr": "ℹ️ Táto aplikácia neukladá ani neposiela žiadne osobné údaje. Všetko zostáva lokálne u teba v zariadení. 💾",
        "holiday_generic": "🎉 Dnes je sviatok – uži si oddych a buď k rozpočtu jemný/á. 😉",
        "holiday_prefix": "🎉 Dnes je sviatok:",
        "no_holiday": "",
    },
    "en": {
        "app_title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates. If no rate is available, the last known rate is used.",
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
        "saved_ok": "✅ Saved!",
        "rate_info": "Applied rate",
        "rate_from": "as of",
        "export": "💾 Export CSV",
        "gdpr": "ℹ️ This app does not store or send personal data. Everything stays locally on your device. 💾",
        "holiday_generic": "🎉 It’s a public holiday – relax and be gentle with your budget. 😉",
        "holiday_prefix": "🎉 Today is a public holiday:",
        "no_holiday": "",
    }
}

# -------------------------------------------------
# CATEGORIES (user’s set)
# -------------------------------------------------
CATEGORIES = {
    "sk": [
        "Potraviny 🛒 / Potraviny 🛒",
        "Drogérie 🧴 / Drogérie 🧴",
        "Doprava 🚌 / Doprava 🚌",
        "Reštaurácie a bary 🍽️ / Restaurace a bary 🍽️",
        "Zábava 🎉 / Zábava 🎉",
        "Odevy 👕 / Oblečení 👕",
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
        "Transport 🚌",
        "Restaurants & Bars 🍽️",
        "Entertainment 🎉",
        "Clothing 👕",
        "Shoes 👟",
        "Electronics 💻",
        "Household / Furniture 🛋️",
        "Sports & Leisure 🏀",
        "Health & Pharmacy 💊",
        "Travel / Holiday ✈️",
        "Education / Courses 📚"
    ]
}

# -------------------------------------------------
# COUNTRIES + currency labels (as you use with CNB)
# -------------------------------------------------
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

# currency code from the label (last token after "–")
COUNTRY_TO_CODE = {}
for label in COUNTRIES["sk"] + COUNTRIES["en"]:
    code = label.split("–")[-1].strip().split()[0]
    COUNTRY_TO_CODE[label] = code

# ISO-3166 for Calendarific (map by country name variant)
COUNTRYNAME_TO_ISO = {
    # CZ / SK / EN variants
    "Česko": "CZ", "Czechia": "CZ",
    "Slovensko": "SK", "Slovakia": "SK",
    "Nemecko": "DE", "Německo": "DE", "Germany": "DE",
    "Rakúsko": "AT", "Rakousko": "AT", "Austria": "AT",
    "Francúzsko": "FR", "Francie": "FR", "France": "FR",
    "Španielsko": "ES", "Španělsko": "ES", "Spain": "ES",
    "Taliansko": "IT", "Itálie": "IT", "Italy": "IT",
    "Holandsko": "NL", "Nizozemsko": "NL", "Netherlands": "NL",
    "Belgicko": "BE", "Belgie": "BE", "Belgium": "BE",
    "Fínsko": "FI", "Finsko": "FI", "Finland": "FI",
    "Írsko": "IE", "Irsko": "IE", "Ireland": "IE",
    "Portugalsko": "PT", "Portugal": "PT",
    "Grécko": "GR", "Řecko": "GR", "Greece": "GR",
    "Slovinsko": "SI", "Slovenia": "SI",
    "Litva": "LT", "Lithuania": "LT",
    "Lotyšsko": "LV", "Latvia": "LV",
    "Estónsko": "EE", "Estonia": "EE",
    "Malta": "MT", "Malta": "MT",
    "Cyprus": "CY", "Cyprus": "CY",
    "Chorvátsko": "HR", "Chorvatsko": "HR", "Croatia": "HR",
    "USA": "US", "United States": "US",
    "Veľká Británia": "GB", "Velká Británie": "GB", "United Kingdom": "GB",
    "Poľsko": "PL", "Polsko": "PL", "Poland": "PL",
    "Maďarsko": "HU", "Hungary": "HU",
    "Švajčiarsko": "CH", "Švýcarsko": "CH", "Switzerland": "CH",
    "Dánsko": "DK", "Dánsko": "DK", "Denmark": "DK",
    "Švédsko": "SE", "Švédsko": "SE", "Sweden": "SE",
    "Nórsko": "NO", "Norsko": "NO", "Norway": "NO",
    "Kanada": "CA", "Canada": "CA",
    "Japonsko": "JP", "Japan": "JP",
}

def label_to_iso(label: str):
    # take country name before "–" and if there are " / " variants, try each
    name_part = label.split("–")[0].strip()
    variants = [v.strip() for v in name_part.split("/")]
    for v in variants:
        if v in COUNTRYNAME_TO_ISO:
            return COUNTRYNAME_TO_ISO[v]
    # fallback try English side if present in EN list
    return None

# -------------------------------------------------
# STATE INIT
# -------------------------------------------------
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date", "Country", "Currency", "Amount", "Category", "Shop", "Note",
        "Converted_CZK", "Rate_value", "Rate_date"
    ])

# -------------------------------------------------
# CNB HELPERS
# -------------------------------------------------
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
                except:
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
    return rate/qty, rate_date_iso

# -------------------------------------------------
# HOLIDAY CHECK (Calendarific)
# -------------------------------------------------
CALENDARIFIC_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"

def calendarific_holiday(iso2: str, d: dt_date):
    if not iso2: return None
    url = f"https://calendarific.com/api/v2/holidays?api_key={CALENDARIFIC_KEY}&country={iso2}&year={d.year}&month={d.month}&day={d.day}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        holidays = data.get("response", {}).get("holidays", [])
        if holidays:
            return holidays[0].get("name", "")
    except:
        return None
    return None

# -------------------------------------------------
# UI HEADER
# -------------------------------------------------
st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])
st.markdown(f'<div class="gdpr">{TEXTS[LANG]["gdpr"]}</div>', unsafe_allow_html=True)

# -------------------------------------------------
# ISSUECOIN PANÁČIK (render)
# -------------------------------------------------
def show_issuecoin_message(msg: str, d: dt_date, holiday_name: str | None = None):
    # Season icons
    m = d.month
    addon = "🏋️" if m in [3,4,5] else ("😎" if m in [6,7,8] else ("🍄" if m in [9,10,11] else "🧣"))

    # Special holiday overlays
    msg_final = msg
    if holiday_name:
        name_low = holiday_name.lower()
        if any(k in name_low for k in ["christmas", "vianoce", "vánoce"]):
            addon = "🎅"
            msg_final = ("🎄 Krásne Vianoce! Nech máš plné brucho aj srdce. "
                         "Uži si deň v pokoji. 💙" if LANG=="sk"
                         else "🎄 Merry Christmas! May your heart (and belly) be full. Enjoy the day in peace. 💙")
        elif any(k in name_low for k in ["new year", "silvester", "nový rok"]):
            addon = "🎉"
            msg_final = ("🎆 Šťastný Nový rok! Malé kroky, veľké výsledky – aj v rozpočte. ✨"
                         if LANG=="sk" else
                         "🎆 Happy New Year! Small steps, big results – for your budget too. ✨")
        elif any(k in name_low for k in ["easter", "veľká noc", "velikonoce"]):
            addon = "🐣"
            msg_final = ("🐣 Veselú Veľkú noc! Dopraj si radosť, ale s mierou. 🙂"
                         if LANG=="sk" else
                         "🐣 Happy Easter! Treat yourself – gently. 🙂")

    # Black Friday (20–30 Nov)
    if m == 11 and 20 <= d.day <= 30 and not holiday_name:
        addon = "🛍️"
        msg_final = ("🛍️ Black Friday! Ak je ponuka dobrá, choď do toho – len nekupuj to, čo netreba. 😉"
                     if LANG=="sk" else
                     "🛍️ Black Friday! If it’s a good deal, go for it – just skip what you don’t need. 😉")

    # --- New: head aligned directly above the body ---
    st.markdown(f"""
        <div class="issuecoin-wrap">
            <div class="issuecoin-figure" style="text-align:center; line-height:1;">
                <div style="font-size:40px; position:relative; top:10px;">🔵{addon}</div>
                <div class="issuecoin-body" style="margin-top:-4px; font-family:monospace; font-size:18px;">
                    &nbsp;/│\\<br>&nbsp;/ \\
                </div>
            </div>
            <div class="issuecoin-bubble">
                <strong>IssueCoin</strong><br>{msg_final}
            </div>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# INPUT FORM
# -------------------------------------------------
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today(), min_value=dt_date(2024,1,1))
        country_label = st.selectbox(TEXTS[LANG]["country"], COUNTRIES[LANG])
        category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    with col2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, step=1.0)
        shop = st.text_input(TEXTS[LANG]["shop"])
        note = st.text_input(TEXTS[LANG]["note"])
    submit = st.form_submit_button(TEXTS[LANG]["save"])

# -------------------------------------------------
# SAVE ENTRY + LOGIC
# -------------------------------------------------
if submit:
    currency_code = COUNTRY_TO_CODE[country_label]
    per_unit, rate_date = (1.0, d.isoformat()) if currency_code == "CZK" else get_rate_for(currency_code, d)

    if per_unit is None:
        st.error(TEXTS[LANG]["rate_err"])
    else:
        converted = round(amount * per_unit, 2)
        new_row = pd.DataFrame([{
            "Date": d.isoformat(),
            "Country": country_label,
            "Currency": currency_code,
            "Amount": amount,
            "Category": category,
            "Shop": shop,
            "Note": note,
            "Converted_CZK": converted,
            "Rate_value": round(per_unit, 4),
            "Rate_date": rate_date
        }])
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)

        st.success(f"{TEXTS[LANG]['saved_ok']} {converted} CZK — {TEXTS[LANG]['rate_info']}: {round(per_unit,4)} CZK/1 {currency_code} ({TEXTS[LANG]['rate_from']} {rate_date})")

        # ---- HOLIDAY MESSAGE (only if holiday) ----
        iso2 = label_to_iso(country_label)
        hol_name = calendarific_holiday(iso2, d)
        if hol_name:
            prefix = TEXTS[LANG]["holiday_prefix"]
            msg = f"{prefix} <strong>{hol_name}</strong>."
            show_issuecoin_message(msg, d, holiday_name=hol_name)

        # ---- CATEGORY-BASED MESSAGES (friendly & only on thresholds) ----
        # Sum by category (in CZK)
        sums = st.session_state["expenses"].groupby("Category")["Converted_CZK"].sum()

        # Helper match for both lang variants
        def in_any(name, lst): 
            return any(name == x for x in lst)

        # Map category families
        rest_keys = ["Reštaurácie a bary 🍽️ / Restaurace a bary 🍽️", "Restaurants & Bars 🍽️"]
        fun_keys  = ["Zábava 🎉 / Zábava 🎉", "Entertainment 🎉"]

        # Current category sum (safe get)
        cat_sum = float(sums.get(category, 0.0))

        # Thresholds
        if category in rest_keys + fun_keys:
            if cat_sum >= 1000:
                msg = ("🎉 Zaslúžená zábava! Uži si to – a nech zostane aj na ďalší večer. 😉"
                       if LANG=="sk" else
                       "🎉 Well-deserved fun! Enjoy – and save a little for next time. 😉")
                show_issuecoin_message(msg, d)
        else:
            if cat_sum >= 2500:
                msg = ("💸 Vyzerá to na výdatný mesiac. Všetko je OK, keď je to dôležité. 🙂"
                       if LANG=="sk" else
                       "💸 Looks like a richer month. All good if it matters. 🙂")
                show_issuecoin_message(msg, d)

# -------------------------------------------------
# LIST + SUMMARY + CHART + EXPORT
# -------------------------------------------------
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
        .properties(height=340)
    )
    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(TEXTS[LANG]["export"], data=csv, file_name=f"expenses_{dt_date.today().isoformat()}.csv", mime="text/csv")

