# AI_agent_vydajova_appka.py
import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date, timedelta

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Expense Diary · IssueCoin", layout="wide")
CALENDARIFIC_API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"  # ← tvoj kľúč
CNB_TXT_DAILY = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
CNB_TXT_DAILY_AT = f"{CNB_TXT_DAILY}?date={{date}}"  # "?date=dd.mm.yyyy"

# ---------------------------
# MINI CSS
# ---------------------------
st.markdown("""
<style>
html, body, [class*="css"]  { font-size: 16px; line-height: 1.6; }
h1 { font-size: 28px !important; }
.issuecoin-wrap { display:flex; gap:16px; align-items:flex-start; margin:8px 0 16px 0;}
.issuecoin-svg { width:72px; height:90px; flex:0 0 auto; }
.issuecoin-bubble { background:#eef6ff; border:1px solid #d6e7ff; padding:14px 16px; border-radius:14px; }
.issuecoin-title { font-weight:700; color:#1f4b99; margin-bottom:6px; }
.gdpr { border-left:6px solid #0ea5e9; background:#eaf6ff; padding:10px 12px; border-radius:8px; }
.save-ok { border-left:6px solid #16a34a; background:#ecfdf5; padding:10px 12px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# LANG
# ---------------------------
left, right = st.columns([7,3])
with right:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

TEXTS = {
    "sk": {
        "title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB. Ak pre zvolený dátum chýba kurz, vezme sa posledný dostupný.",
        "gdpr": "Táto aplikácia neukladá ani neodosiela žiadne osobné údaje. Údaje zostávajú lokálne vo vašom zariadení.",
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "note": "📝 Poznámka",
        "category": "📂 Kategória / Kategorie",
        "save": "💾 Uložiť nákup / Uložit nákup",
        "saved": "Záznam uložený! → {czk:.1f} CZK — Použitý kurz: {rate:.2f} CZK/1 {code} (k {rdate})",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "holiday_today": "Dnes je sviatok: {name}.",
        "holiday_obs": "{name} je sviatok/udalosť v krajine.",
        "export": "💾 Export CSV",
    },
    "en": {
        "title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates. If the rate is missing for the day, the last available is used.",
        "gdpr": "This app does not store or send any personal data. All data stay local on your device.",
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "shop": "🏬 Shop / place",
        "note": "📝 Note",
        "category": "📂 Category",
        "save": "💾 Save purchase",
        "saved": "Saved! → {czk:.1f} CZK — Applied rate: {rate:.2f} CZK/1 {code} (as of {rdate})",
        "list": "🧾 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "rate_err": "❌ Could not fetch exchange rate.",
        "holiday_today": "Today is a public holiday: {name}.",
        "holiday_obs": "{name} is an observance in the country.",
        "export": "💾 Export CSV",
    }
}

# CATEGORIES (rozšírené)
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

# Krajiny + kód meny (CNB kódy) + ISO2 pre Calendarific
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

# Mapovanie label -> currency code + ISO2
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
        # fallback: posledné slovo mena → kód, ISO ponechaj prázdne
        code = lab.split("–")[-1].strip().split()[0]
        _reg(lab, code, "")

# ---------------------------
# STATE
# ---------------------------
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date","Country","Currency","Amount","Category","Shop","Note","Converted_CZK","Rate_value","Rate_date"
    ])

# ---------------------------
# CNB helpers
# ---------------------------
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
                    return rate/qty, header  # per 1 unit
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

# ---------------------------
# Calendarific
# ---------------------------
@st.cache_data(ttl=1800)
def calendarific_holidays(iso2: str, year: int, month: int=None, day: int=None):
    if not iso2: return []
    base = "https://calendarific.com/api/v2/holidays"
    params = {
        "api_key": CALENDARIFIC_API_KEY,
        "country": iso2,
        "year": year
    }
    if month: params["month"] = month
    if day: params["day"] = day
    try:
        r = requests.get(base, params=params, timeout=10)
        if r.status_code != 200: return []
        data = r.json()
        return data.get("response", {}).get("holidays", [])
    except:
        return []

def check_holiday(iso2: str, d: dt_date):
    hs = calendarific_holidays(iso2, d.year, d.month, d.day)
    if not hs: return None, None
    # prefer national over observance
    nat = [h for h in hs if "national" in [t.lower() for t in h.get("type", [])]]
    target = nat[0] if nat else hs[0]
    return target.get("name"), target.get("type", [])

# ---------------------------
# IssueCoin SVG (panáčik)
# ---------------------------
def season_for(d: dt_date):
    m = d.month
    if m in (12,1,2): return "winter"
    if m in (3,4,5): return "spring"
    if m in (6,7,8): return "summer"
    return "autumn"

def special_days(d: dt_date):
    # Black Friday = posledný piatok v novembri
    bf = None
    if d.month == 11:
        last = dt_date(d.year, 11, 30)
        while last.weekday() != 4:  # Friday
            last -= timedelta(days=1)
        bf = last
    # Christmas period / New Year / Easter (orientačne)
    xmas = (d.month == 12 and d.day in (24,25,26))
    newyear = (d.month == 12 and d.day in (31,) ) or (d.month == 1 and d.day == 1)
    return {"black_friday": (bf == d), "xmas": xmas, "newyear": newyear}

def issuecoin_svg(d: dt_date, holiday_types):
    season = season_for(d)
    sp = special_days(d)
    hat = ""
    # Holiday accessories
    if sp["xmas"] or (holiday_types and any("christ" in t.lower() or "religious" in t.lower() for t in holiday_types)):
        hat = '<polygon points="36,8 60,30 12,30" fill="#d22" /><rect x="22" y="30" width="18" height="5" fill="#fff"/>'
    elif sp["newyear"]:
        hat = '<circle cx="36" cy="12" r="6" fill="#ffd200"/>'
    # Seasonal accessories
    deco = ""
    if season == "winter":
        deco = '<rect x="20" y="62" width="32" height="8" rx="4" fill="#2aa3ff" />'  # scarf
    elif season == "summer":
        deco = '<rect x="18" y="28" width="36" height="6" rx="3" fill="#111"/> <rect x="24" y="34" width="10" height="6" rx="3" fill="#49f"/> <rect x="44" y="34" width="10" height="6" rx="3" fill="#49f"/>'
    elif season == "spring":
        deco = '<rect x="12" y="48" width="8" height="8" rx="2" fill="#8BC34A"/><rect x="52" y="48" width="8" height="8" rx="2" fill="#8BC34A"/>'
    elif season == "autumn":
        deco = '<circle cx="60" cy="64" r="8" fill="#a0522d"/><rect x="58" y="54" width="4" height="8" fill="#3e2723"/>'
    # Confetti on New Year or party vibe
    confetti = ""
    if sp["newyear"]:
        confetti = ''.join([f'<circle cx="{10+i*10}" cy="{10+(i%3)*8}" r="2" fill="#{c}"/>' for i,c in enumerate(["f44336","4caf50","2196f3","ff9800","9c27b0","00bcd4"])])
    # Body + head + limbs
    svg = f"""
<svg class="issuecoin-svg" viewBox="0 0 90 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="88" height="98" rx="12" fill="transparent"/>
  {confetti}
  <circle cx="36" cy="24" r="16" fill="#1e90ff" stroke="#0b4a8f" stroke-width="3" />
  {hat}
  <circle cx="30" cy="24" r="3" fill="#0b4a8f"/>
  <circle cx="42" cy="24" r="3" fill="#0b4a8f"/>
  <path d="M29,31 Q36,36 43,31" stroke="#0b4a8f" stroke-width="3" fill="none" stroke-linecap="round"/>
  <line x1="36" y1="40" x2="36" y2="70" stroke="#0b4a8f" stroke-width="4"/>
  <line x1="36" y1="48" x2="18" y2="58" stroke="#0b4a8f" stroke-width="4" stroke-linecap="round"/>
  <line x1="36" y1="48" x2="54" y2="58" stroke="#0b4a8f" stroke-width="4" stroke-linecap="round"/>
  <line x1="36" y1="70" x2="24" y2="88" stroke="#0b4a8f" stroke-width="4" stroke-linecap="round"/>
  <line x1="36" y1="70" x2="48" y2="88" stroke="#0b4a8f" stroke-width="4" stroke-linecap="round"/>
  {deco}
</svg>
"""
    return svg

def issuecoin_block(message: str, date_obj: dt_date, holiday_types=None, title="IssueCoin"):
    svg = issuecoin_svg(date_obj, holiday_types or [])
    st.markdown(f"""
<div class="issuecoin-wrap">
  <div>{svg}</div>
  <div class="issuecoin-bubble">
    <div class="issuecoin-title">{title}</div>
    <div>{message}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# HEADERS
# ---------------------------
st.title(TEXTS[LANG]["title"])
st.caption(TEXTS[LANG]["subtitle"])
st.markdown(f'<div class="gdpr">ℹ️ {TEXTS[LANG]["gdpr"]}</div>', unsafe_allow_html=True)

# ---------------------------
# FORM
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
# SAVE HANDLER
# ---------------------------
if submit:
    code = COUNTRY_TO_CODE.get(country, "CZK")
    per_unit, rate_date = get_rate_for(code, d)
    if per_unit is None:
        st.error(TEXTS[LANG]["rate_err"])
    else:
        converted = round(amount * per_unit, 1)
        row = pd.DataFrame([{
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
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], row], ignore_index=True)

        st.markdown(
            f'<div class="save-ok">{TEXTS[LANG]["saved"].format(czk=converted, rate=per_unit, code=code, rdate=rate_date)}</div>',
            unsafe_allow_html=True
        )

        # --- Holiday message (Calendarific)
        iso = COUNTRY_TO_ISO.get(country, "")
        hname, htypes = check_holiday(iso, d)
        if hname:
            msg = TEXTS[LANG]["holiday_today"].format(name=hname) if "sk" in LANG else TEXTS[LANG]["holiday_today"].format(name=hname)
            issuecoin_block(f"🎉 {msg}", d, holiday_types=htypes)

        # --- Budget friendly nudges (limits)
        df = st.session_state["expenses"]
        # CZK sums by category
        sums = df.groupby("Category")["Converted_CZK"].sum().to_dict()

        def over_limit(cat, thr):
            return sums.get(cat, 0) >= thr

        # map for localized categories
        cat_map_fun = {
            "sk": {
                "food": "Potraviny 🛒 / Potraviny 🛒",
                "rest": "Reštaurácie a bary 🍽️ / Restaurace a bary 🍽️",
                "ent": "Zábava 🎉 / Zábava 🎉",
            },
            "en": {
                "food": "Groceries 🛒",
                "rest": "Restaurants & Bars 🍽️",
                "ent": "Entertainment 🎉",
            }
        }
        m = cat_map_fun[LANG]
        # thresholds
        nudges = []
        if over_limit(m["rest"], 1000) or over_limit(m["ent"], 1000):
            if LANG == "sk":
                nudges.append("🍽️🎉 Vyzerá to na výdatný mesiac. Všetko je OK, keď je to dôležité — len mysli aj na rozpočet. 🙂")
            else:
                nudges.append("🍽️🎉 Looks like a fun month! All good when it matters — just keep an eye on the budget. 🙂")
        if over_limit(m["food"], 2500):
            if LANG == "sk":
                nudges.append("🛒 Nákupy idú – držíš to pod kontrolou. Ak chceš, skús menu plán a veľké balenia.")
            else:
                nudges.append("🛒 Groceries piling up? You’ve got this. Meal planning and bulk packs can help.")

        # Seasonal / festive extra friendly line
        s = season_for(d)
        sp = special_days(d)
        extra = ""
        if sp["black_friday"]:
            extra = "🖤 Black Friday je v plnom prúde – porovnaj ceny a kupuj to, čo dáva zmysel. 😉" if LANG=="sk" else \
                    "🖤 Black Friday is on – compare prices and buy what truly matters. 😉"
        elif s == "winter":
            extra = "❄️ Krásne sviatky! Teplý čaj a teplý rozpočet. ☕" if LANG=="sk" else "❄️ Happy holidays! Keep both tea and budget warm. ☕"
        elif s == "summer":
            extra = "🌞 Leto volá – uži si ho, výdaje máme na očiach. 😎" if LANG=="sk" else "🌞 Summer vibes – enjoy, we keep the expenses in sight. 😎"
        elif s == "spring":
            extra = "🌼 Jar sa hýbe – ľahké kroky aj v rozpočte." if LANG=="sk" else "🌼 Spring energy – keep steps light, budget too."
        elif s == "autumn":
            extra = "🍂 Jesenná pohoda – nech sú výdaje ako lesná vychádzka: pokojné." if LANG=="sk" else \
                    "🍂 Autumn calm – let expenses be like a forest walk: easy."

        for n in nudges:
            issuecoin_block(n, d, holiday_types=htypes or [])

        if extra:
            issuecoin_block(extra, d, holiday_types=htypes or [])

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
        .properties(width=700, height=320)
    )
    st.altair_chart(chart, use_container_width=True)

    # export
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(TEXTS[LANG]["export"], data=csv,
                       file_name=f"expenses_{dt_date.today().isoformat()}.csv",
                       mime="text/csv")

