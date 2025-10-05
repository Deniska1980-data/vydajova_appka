# ----------------------------------------
# 📦 Importy
# ----------------------------------------
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, date as dt_date

# (sem patria aj ostatné tvoje importy – nič z toho nemaž)

# ----------------------------------------
# 🔒 GDPR / Local Storage Info Banner
# ----------------------------------------
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'SK'  # predvolený jazyk (SK/CZ/EN)

if st.session_state['lang'] == 'SK':
    st.info(
        "🔒 Táto aplikácia ukladá tvoje údaje **iba lokálne** na tvojom zariadení. "
        "Žiadne dáta sa neposielajú na server — všetko prebieha bezpečne a v súlade s GDPR. "
        "Tvoje dáta zostávajú len u teba. 💾",
        icon="ℹ️"
    )
elif st.session_state['lang'] == 'CZ':
    st.info(
        "🔒 Tato aplikace ukládá tvoje údaje **pouze lokálně** na tvém zařízení. "
        "Žádná data se neodesílají na server — vše probíhá bezpečně a v souladu s GDPR. "
        "Tvoje data zůstávají pouze u tebe. 💾",
        icon="ℹ️"
    )
else:
    st.info(
        "🔒 This app stores your data **locally only** on your device. "
        "No information is sent to any server — fully secure and GDPR compliant. "
        "Your data stays with you. 💾",
        icon="ℹ️"
    )

# ----------------------------------------
# 🧾 Hlavný nadpis a obsah appky
# ----------------------------------------
st.title("💰 Výdavkový denník / Expense Diary")

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 16px; }
h1 { font-size: 28px !important; margin-bottom: .25rem; }
h2 { font-size: 22px !important; }
.stButton>button { font-size: 16px; padding: 8px 14px; }
.issue-row { display:flex; gap:10px; align-items:flex-start; margin:.25rem 0 .75rem; }
.issue-avatar { font-size: 28px; line-height:1; min-width: 2rem; text-align:center; }
.issue-bubble { background:#eaf2ff; border-radius:12px; padding:.6rem .9rem; }
.gdpr-note { color:#666; font-size:14px; text-align:center; margin-top:.75rem; }
.small-cap { color:#6a6a6a; font-size: 13px; margin-top:-.25rem; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# CALENDARIFIC
# ───────────────────────────────────────────────────────────────────────────────
CAL_API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"
CAL_BASE = "https://calendarific.com/api/v2/holidays"

# ───────────────────────────────────────────────────────────────────────────────
# LANG SWITCH (SK/CZ ↔ EN)
# ───────────────────────────────────────────────────────────────────────────────
left, right = st.columns([7,3])
with right:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB. "
                    "Ak pre vybraný deň nie je kurz, použije sa posledný dostupný kurz. / "
                    "CZK = vždy 1:1. Ostatní měny podle denního kurzu ČNB. "
                    "Pokud kurz není k dispozici, použije se poslední známý kurz.",
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Země + měna",
        "amount": "💵 Suma / Částka",
        "category": "📂 Kategória / Kategorie",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť nákup / Uložit nákup",
        "saved_ok": "Záznam uložený!",
        "rate_info": "Použitý kurz",
        "rate_from": "k",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "export": "💾 Export CSV",
        "gdpr": "🔒 Údaje sa ukladajú len lokálne vo tvojom zariadení (žiadny server, GDPR friendly).",
        "holiday_today": "Dnes je sviatok:",
        "no_rate": "❌ Kurz sa nepodarilo načítať."
    },
    "en": {
        "app_title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates. "
                    "If a rate is missing for the selected day, the latest available rate is used.",
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "category": "📂 Category",
        "shop": "🏬 Shop / place",
        "note": "📝 Note",
        "save": "💾 Save purchase",
        "saved_ok": "Saved!",
        "rate_info": "Applied rate",
        "rate_from": "as of",
        "list": "🧾 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "export": "💾 Export CSV",
        "gdpr": "🔒 Your data are stored locally only (no server, GDPR friendly).",
        "holiday_today": "Today is a public holiday:",
        "no_rate": "❌ Could not fetch exchange rate."
    }
}

# ───────────────────────────────────────────────────────────────────────────────
# CATEGORIES (SK/CZ + EN)
# ───────────────────────────────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────────────────────────────
# COUNTRIES (ČNB codes + ISO2 for Calendarific)
# ───────────────────────────────────────────────────────────────────────────────
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

COUNTRY_TO_CODE = {}
COUNTRY_TO_ISO = {}

def _reg(label, code, iso):
    COUNTRY_TO_CODE[label] = code
    COUNTRY_TO_ISO[label] = iso

for lab in COUNTRIES["sk"] + COUNTRIES["en"]:
    t = lab.lower()
    if "česko" in t or "czechia" in t: _reg(lab, "CZK", "CZ")
    elif "slovensk" in t or "slovakia" in t: _reg(lab, "EUR", "SK")
    elif "nemeck" in t or "germany" in t: _reg(lab, "EUR", "DE")
    elif "rakús" in t or "austria" in t: _reg(lab, "EUR", "AT")
    elif "poľsko" in t or "poland" in t: _reg(lab, "PLN", "PL")
    elif "maďars" in t or "hungary" in t: _reg(lab, "HUF", "HU")
    elif "brit" in t or "kingdom" in t: _reg(lab, "GBP", "GB")
    elif "usa" in t: _reg(lab, "USD", "US")
    elif "švajč" in t or "switzer" in t: _reg(lab, "CHF", "CH")
    elif "dán" in t or "denmark" in t: _reg(lab, "DKK", "DK")
    elif "švéd" in t or "sweden" in t: _reg(lab, "SEK", "SE")
    elif "nór" in t or "norway" in t: _reg(lab, "NOK", "NO")
    elif "kanad" in t or "canada" in t: _reg(lab, "CAD", "CA")
    elif "japon" in t or "japan" in t: _reg(lab, "JPY", "JP")
    elif "holand" in t or "nether" in t: _reg(lab, "EUR", "NL")
    elif "belg" in t: _reg(lab, "EUR", "BE")
    elif "franc" in t or "france" in t: _reg(lab, "EUR", "FR")
    elif "špan" in t or "spain" in t: _reg(lab, "EUR", "ES")
    elif "tali" in t or "italy" in t: _reg(lab, "EUR", "IT")
    elif "írs" in t or "ireland" in t: _reg(lab, "EUR", "IE")
    elif "fín" in t or "finland" in t: _reg(lab, "EUR", "FI")
    elif "gréck" in t or "greece" in t: _reg(lab, "EUR", "GR")
    elif "chorv" in t or "croat" in t: _reg(lab, "EUR", "HR")
    else:
        # fallback: last token after "–" should be currency code
        code = lab.split("–")[-1].strip().split()[0]
        _reg(lab, code, "")

# ───────────────────────────────────────────────────────────────────────────────
# STATE
# ───────────────────────────────────────────────────────────────────────────────
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date","Country","Currency","Amount","Category","Shop","Note","Converted_CZK","Rate_value","Rate_date"
    ])

# ───────────────────────────────────────────────────────────────────────────────
# CNB helpers
# ───────────────────────────────────────────────────────────────────────────────
CNB_TXT_DAILY = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
CNB_TXT_DAILY_AT = CNB_TXT_DAILY + "?date={date}"

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
                    return rate/qty, header  # CZK per 1 unit
                except:
                    return None, header
    return None, header

def get_rate_for(code: str, d: dt_date):
    if code == "CZK":
        return 1.0, d.isoformat()
    d_str = d.strftime("%d.%m.%Y")
    txt = _fetch_txt(CNB_TXT_DAILY_AT.format(date=d_str))
    rate, header = _parse_cnb(txt, code)
    if rate is None:
        txt2 = _fetch_txt(CNB_TXT_DAILY)
        rate, header = _parse_cnb(txt2, code)
        rdate = datetime.today().date().isoformat()
    else:
        rdate = datetime.strptime(header, "%d.%m.%Y").date().isoformat()
    return rate, rdate

# ───────────────────────────────────────────────────────────────────────────────
# Calendarific helpers
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_holiday_name(date_obj: dt_date, iso2: str, lang: str):
    """Return a holiday name for given date & country or None. lang: 'sk' or 'en' (we'll request EN from API)."""
    try:
        params = {
            "api_key": CAL_API_KEY,
            "country": iso2,
            "year": date_obj.year,
            "month": date_obj.month,
            "day": date_obj.day,
        }
        r = requests.get(CAL_BASE, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        hols = data.get("response", {}).get("holidays", [])
        if not hols:
            return None
        name_en = hols[0].get("name", "").strip()
        # Hand translation of most common holidays to SK/CZ twin form
        translate = {
            "Christmas Eve": "Štedrý večer / Štědrý večer (Vianoce / Vánoce)",
            "Christmas Day": "Prvý sviatok vianočný / 1. svátek vánoční",
            "St. Stephen's Day": "Druhý sviatok vianočný / 2. svátek vánoční",
            "New Year's Day": "Nový rok / Nový rok",
            "Epiphany": "Zjavenie Pána (Traja králi) / Zjevení Páně (Tři králové)",
            "Good Friday": "Veľký piatok / Velký pátek",
            "Easter Monday": "Veľkonočný pondelok / Velikonoční pondělí",
            "Labor Day": "Sviatok práce / Svátek práce",
            "Independence Day": "Deň nezávislosti / Den nezávislosti",
            "All Saints' Day": "Sviatok všetkých svätých / Svátek Všech svatých",
            "Statehood Day": "Deň štátnosti / Den státnosti",
            "Harvest Festival": "Dožinky / Jesenný festival",
        }
        if lang == "sk":
            return translate.get(name_en, name_en)
        else:
            return name_en
    except:
        return None

# ───────────────────────────────────────────────────────────────────────────────
# IssueCoin avatar & messages
# ───────────────────────────────────────────────────────────────────────────────
def seasonal_avatar(d: dt_date, holiday_name: str | None):
    """Return an emoji avatar string based on season and holiday window."""
    # Christmas window
    if d.month == 12 and 20 <= d.day <= 26:
        return "🙂🎄"  # hlava + stromček (jednoduché, čitateľné)
    # Seasons
    if d.month in (12,1,2):
        return "🙂🧣"   # zima – šál/čiapka
    if d.month in (3,4,5):
        return "🙂💪"   # jar – chuť cvičiť
    if d.month in (6,7,8):
        return "😎"     # leto – okuliare
    return "🙂🍁"        # jeseň – lístok/huby by boli moc drobné

def issue_box(text: str, avatar: str):
    c1, c2 = st.columns([1, 12])
    with c1:
        st.markdown(f'<div class="issue-avatar">{avatar}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="issue-bubble"><b>IssueCoin</b><br>{text}</div>', unsafe_allow_html=True)

# thresholds (CZK)
THRESHOLDS = {
    "restaurants": 1000,
    "entertainment": 1000,
    "groceries": 6500,
    "default": 2500
}

def category_key_for_threshold(cat_label: str):
    tl = cat_label.lower()
    if "reštaur" in tl or "restaur" in tl: return "restaurants"
    if "zábav" in tl or "entertain" in tl: return "entertainment"
    if "potrav" in tl or "grocer" in tl: return "groceries"
    return "default"

def friendly_msg_for(cat_label: str, over_by: float):
    if LANG == "sk":
        if "reštaur" in cat_label.lower() or "restaur" in cat_label.lower():
            return "🧾 Účty v podnikoch rastú – skús sledovať akcie alebo obedové menu. 😉"
        if "zábav" in cat_label.lower():
            return "🎈 Zábava je fajn – daj jej však rozumný rozpočet, nech ostane aj na iné radosti."
        if "potrav" in cat_label.lower() or "grocer" in cat_label.lower():
            return "🧺 Nákupy potravín sú vyššie. Pomôže zoznam a akciové balenia."
        return "💡 Výdavky v tejto kategórii rastú. Malé úpravy spravia veľký rozdiel."
    else:
        if "restaur" in cat_label.lower():
            return "🧾 Dining costs are rising—lunch deals or specials can help. 😉"
        if "entertain" in cat_label.lower():
            return "🎈 Fun is great—just give it a budget so there’s room for everything else."
        if "grocer" in cat_label.lower():
            return "🧺 Groceries are up. A simple list and multi-packs can help."
        return "💡 Spending in this category is increasing. Small tweaks go a long way."

def seasonal_line(d: dt_date):
    if LANG == "sk":
        if d.month in (12,1,2):  return "❄️ Zimná pohoda — teplý čaj a teplý rozpočet."
        if d.month in (3,4,5):   return "🌼 Jarný štart — malé kroky robia silný rozpočet."
        if d.month in (6,7,8):   return "😎 Letná pohoda — uži si slnko a účtenky drž v chládku."
        return "🍂 Jesenná pohoda — nech sú výdavky ako lesná prechádzka: pokojné."
    else:
        if d.month in (12,1,2):  return "❄️ Winter calm—keep both tea and budget warm."
        if d.month in (3,4,5):   return "🌼 Spring start—small steps make a strong budget."
        if d.month in (6,7,8):   return "😎 Summer chill—enjoy the sun and keep receipts cool."
        return "🍂 Autumn calm—let expenses be like a forest walk: easy."

# ───────────────────────────────────────────────────────────────────────────────
# HEADER
# ───────────────────────────────────────────────────────────────────────────────
st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])
st.markdown(f'<div class="small-cap">{TEXTS[LANG]["gdpr"]}</div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# FORM
# ───────────────────────────────────────────────────────────────────────────────
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today(), min_value=dt_date(2024,1,1))
        country = st.selectbox(TEXTS[LANG]["country"], COUNTRIES[LANG])
        category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    with col2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, step=1.0, format="%.2f")
        shop = st.text_input(TEXTS[LANG]["shop"])
        note = st.text_input(TEXTS[LANG]["note"])
    submitted = st.form_submit_button(TEXTS[LANG]["save"])

if submitted:
    code = COUNTRY_TO_CODE.get(country, "CZK")
    iso2 = COUNTRY_TO_ISO.get(country, "CZ")
    rate, rate_date = get_rate_for(code, d)
    if rate is None:
        st.error(TEXTS[LANG]["no_rate"])
    else:
        converted = round(amount * rate, 2)
        new_row = pd.DataFrame([{
            "Date": d.isoformat(),
            "Country": country,
            "Currency": code,
            "Amount": amount,
            "Category": category,
            "Shop": shop,
            "Note": note,
            "Converted_CZK": converted,
            "Rate_value": round(rate, 4),
            "Rate_date": rate_date
        }])
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)

        # success line
        if LANG == "sk":
            st.success(f"{TEXTS[LANG]['saved_ok']} → {converted:.2f} CZK "
                       f"— {TEXTS[LANG]['rate_info']}: {rate:.4f} CZK/1 {code} ({TEXTS[LANG]['rate_from']} {rate_date})")
        else:
            st.success(f"{TEXTS[LANG]['saved_ok']} → {converted:.2f} CZK "
                       f"— {TEXTS[LANG]['rate_info']}: {rate:.4f} CZK/1 {code} ({TEXTS[LANG]['rate_from']} {rate_date})")

        # HOLIDAY MESSAGE (only if there is a holiday)
        hol_name = get_holiday_name(d, iso2, LANG)
        if hol_name:
            prefix = "🎉 " + (TEXTS[LANG]["holiday_today"])
            issue_box(f"{prefix} <b>{hol_name}</b>.", seasonal_avatar(d, hol_name))

        # THRESHOLD-BASED CATEGORY MESSAGES
        df = st.session_state["expenses"]
        sums = df.groupby("Category")["Converted_CZK"].sum() if not df.empty else pd.Series(dtype=float)
        total_for_cat = float(sums.get(category, 0.0))
        key = category_key_for_threshold(category)
        limit = THRESHOLDS.get(key, THRESHOLDS["default"])
        if total_for_cat >= limit:
            issue_box(friendly_msg_for(category, total_for_cat - limit), seasonal_avatar(d, None))
        else:
            # seasonal gentle line (always friendly, not scolding)
            issue_box(seasonal_line(d), seasonal_avatar(d, None))

# ───────────────────────────────────────────────────────────────────────────────
# LIST + SUMMARY + CHART + EXPORT
# ───────────────────────────────────────────────────────────────────────────────
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
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)

    # Export CSV
    csv = df.to_csv(index=False).encode("utf-8")
    file_name = f"expenses_{dt_date.today().isoformat()}.csv"
    st.download_button(
        label=TEXTS[LANG]["export"],
        data=csv,
        file_name=file_name,
        mime="text/csv",
    )


