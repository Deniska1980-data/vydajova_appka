import streamlit as st
from datetime import date as dt_date, datetime, timedelta
import pandas as pd
import requests
import random
import altair as alt

# ───────────────────────────────────────────────────────────────────────────────
# LANG SWITCH (SK/CZ ↔ EN) – presunuté hore
# ───────────────────────────────────────────────────────────────────────────────
left, right = st.columns([7, 3])
with right:
    lang_choice = st.selectbox(
        "🌐 Language / Jazyk",
        ["Slovensky / Česky", "English"],
        index=0,
        key="language_selector"
    )

LANG = "sk" if "Slovensky" in lang_choice else "en"

# ───────────────────────────────────────────────────────────────────────────────
# 🧾 Hlavný nadpis a štýly
# ───────────────────────────────────────────────────────────────────────────────
# 🧾 Hlavný nadpis a štýly (béžové + a11y)
BG = "#F7F1E3"
PANEL = "#EFE8DA"
TEXT = "#1B1B1B"
ACCENT = "#0B65C2"
MUTED = "#6A6A6A"

st.markdown(f"""
<style>
html, body, [class*="css"] {{ font-size: 18px; line-height:1.5; }}
.stApp, [data-testid="stAppViewContainer"] {{ background:{BG} !important; }}
section[data-testid="stSidebar"] > div:first-child {{ background:{PANEL} !important; }}

h1 {{ font-size: 28px !important; margin-bottom: .25rem; color:{TEXT}; }}
h2 {{ font-size: 22px !important; color:{TEXT}; }}

.stButton>button {{ font-size:17px; padding:10px 16px; border-radius:10px; }}
.stButton>button:focus {{ box-shadow: 0 0 0 3px rgba(11,101,194,.25); }}

a {{ color:{ACCENT}; text-decoration: underline; }}

.issue-row {{ display:flex; gap:10px; align-items:flex-start; margin:.25rem 0 .75rem; }}
.issue-avatar {{ font-size:28px; line-height:1; min-width:2rem; text-align:center; }}
.issue-bubble {{ background:{PANEL}; border-radius:14px; padding:.7rem 1rem; color:{TEXT}; }}

.gdpr-note {{ color:{MUTED}; font-size:14px; text-align:center; margin-top:.75rem; }}
.small-cap {{ color:{MUTED}; font-size:13px; margin-top:-.25rem; }}

div[data-testid="stDataFrame"] div[role="grid"] {{
  background:{PANEL}; color:{TEXT}; border-radius:10px; border:1px solid rgba(0,0,0,.06);
}}

:focus-visible {{ outline:3px solid {ACCENT}; outline-offset:2px; }}
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────────────────
# Calendarific API
# ───────────────────────────────────────────────────────────────────────────────
CAL_API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"
CAL_BASE = "https://calendarific.com/api/v2/holidays"

# ───────────────────────────────────────────────────────────────────────────────
# TEXTS
# ───────────────────────────────────────────────────────────────────────────────
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
# Calendarific helpers – správne rozlíšené sviatky (štátne, cirkevné, pamätné)
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_holiday_name(date_obj: dt_date, iso2: str, lang: str):
    """
    Načíta sviatky pre daný dátum a krajinu z Calendarific API.
    Vracia správny jazykový výstup (bez miešania jazykov).
    """
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
        holidays = data.get("response", {}).get("holidays", [])
        if not holidays:
            return KNOWN_PUBLIC_HOLIDAYS.get((iso2, date_obj.strftime("%m-%d")), None)

        public_names, observance_names = [], []
        for h in holidays:
            name_en = h.get("name", "").strip()
            types = h.get("type", [])
            if any(t in ["National holiday", "Public holiday"] for t in types):
                public_names.append(name_en)
            elif any(t in ["Observance", "Religious", "Local holiday"] for t in types):
                observance_names.append(name_en)

        all_names = public_names + observance_names
        if not all_names:
            return KNOWN_PUBLIC_HOLIDAYS.get((iso2, date_obj.strftime("%m-%d")), None)

        # Preklady do SK/CZ
        trans_sk = {
            "New Year's Day": "Nový rok",
            "Epiphany": "Zjavenie Pána (Traja králi)",
            "Good Friday": "Veľký piatok",
            "Easter Monday": "Veľkonočný pondelok",
            "Labor Day": "Sviatok práce",
            "Liberation Day": "Deň víťazstva nad fašizmom",
            "Saints Cyril and Methodius Day": "Sviatok sv. Cyrila a Metoda",
            "Jan Hus Day": "Deň upálenia majstra Jána Husa",
            "National Day": "Deň Ústavy SR",
            "All Saints' Day": "Sviatok všetkých svätých",
            "Christmas Eve": "Štedrý deň",
            "Christmas Day": "Prvý sviatok vianočný",
            "St. Stephen's Day": "Druhý sviatok vianočný",
            "Boxing Day": "Druhý sviatok vianočný",
            "Day of the Fight for Freedom and Democracy": "Deň boja za slobodu a demokraciu",
            "Day of Slovak National Uprising": "Výročie SNP",
            "Our Lady of Sorrows": "Sedembolestná Panna Mária",
            "All Souls' Day": "Pamiatka zosnulých (Dušičky)",
        }

        if lang in ["sk", "cz"]:
            translated = [trans_sk.get(n, KNOWN_PUBLIC_HOLIDAYS.get((iso2, date_obj.strftime("%m-%d")), n)) for n in all_names]
            if observance_names and not public_names:
                return f"📅 Dnes je pamätný alebo cirkevný deň: {', '.join(translated)}"
            else:
                return f"🎉 Dnes je sviatok: {', '.join(translated)}"
        else:
            if observance_names and not public_names:
                return f"📅 Today is a memorial or religious observance: {', '.join(all_names)}"
            else:
                return f"🎉 Today is a public holiday: {', '.join(all_names)}"

    except Exception as e:
        print("Holiday check error:", e)
        return KNOWN_PUBLIC_HOLIDAYS.get((iso2, date_obj.strftime("%m-%d")), None)

# Fallback – ak Calendarific nič nevráti
KNOWN_PUBLIC_HOLIDAYS = {
    # Slovensko 🇸🇰
    ("SK", "01-01"): "Nový rok – Deň vzniku SR",
    ("SK", "01-06"): "Zjavenie Pána (Traja králi)",
    ("SK", "03-28"): "Deň učiteľov",
    ("SK", "05-01"): "Sviatok práce",
    ("SK", "05-08"): "Deň víťazstva nad fašizmom",
    ("SK", "06-01"): "Deň detí",
    ("SK", "07-05"): "Sviatok sv. Cyrila a Metoda",
    ("SK", "08-29"): "Výročie SNP",
    ("SK", "09-01"): "Deň Ústavy SR",
    ("SK", "09-15"): "Sedembolestná Panna Mária",
    ("SK", "11-01"): "Sviatok všetkých svätých",
    ("SK", "11-02"): "Pamiatka zosnulých (Dušičky)",
    ("SK", "11-17"): "Deň boja za slobodu a demokraciu",
    ("SK", "12-24"): "Štedrý deň",
    ("SK", "12-25"): "Prvý sviatok vianočný",
    ("SK", "12-26"): "Druhý sviatok vianočný",

    # Česko 🇨🇿
    ("CZ", "01-01"): "Nový rok – Deň obnovy samostatného českého štátu",
    ("CZ", "03-08"): "Mezinárodní den žen",
    ("CZ", "05-01"): "Svátek práce",
    ("CZ", "05-08"): "Den vítězství",
    ("CZ", "07-05"): "Den slovanských věrozvěstů Cyrila a Metoděje",
    ("CZ", "07-06"): "Den upálení mistra Jana Husa",
    ("CZ", "09-28"): "Den české státnosti (sv. Václav)",
    ("CZ", "10-28"): "Den vzniku samostatného československého státu",
    ("CZ", "11-17"): "Den boje za svobodu a demokracii",
    ("CZ", "12-24"): "Štědrý den",
    ("CZ", "12-25"): "1. svátek vánoční",
    ("CZ", "12-26"): "2. svátek vánoční",

    # Nemecko 🇩🇪
    ("DE", "01-01"): "Neujahr",
    ("DE", "05-01"): "Tag der Arbeit",
    ("DE", "10-03"): "Tag der Deutschen Einheit",
    ("DE", "12-25"): "Erster Weihnachtstag",
    ("DE", "12-26"): "Zweiter Weihnachtstag",

    # Poľsko 🇵🇱
    ("PL", "01-01"): "Nowy Rok",
    ("PL", "01-06"): "Święto Trzech Króli",
    ("PL", "05-01"): "Święto Pracy",
    ("PL", "05-03"): "Święto Konstytucji 3 Maja",
    ("PL", "08-15"): "Wniebowzięcie Najświętszej Maryi Panny",
    ("PL", "11-01"): "Wszystkich Świętych",
    ("PL", "11-11"): "Narodowe Święto Niepodległości",
    ("PL", "12-25"): "Boże Narodzenie",
    ("PL", "12-26"): "Drugi dzień Świąt Bożego Narodzenia",
}

# ───────────────────────────────────────────────────────────────────────────────
# IssueCoin avatar & messages (UI)
# ───────────────────────────────────────────────────────────────────────────────
def seasonal_avatar(d: dt_date, holiday_name: str | None):
    if (d.month == 12 and 20 <= d.day <= 26):
        return "🙂🎄"
    if d.month in (12,1,2):
        return "🙂🧣"
    if d.month in (3,4,5):
        return "🙂💪"
    if d.month in (6,7,8):
        return "😎"
    return "🙂🍁"

def issue_box(text: str, avatar: str):
    c1, c2 = st.columns([1, 12])
    with c1:
        st.markdown(f'<div class="issue-avatar">{avatar}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="issue-bubble"><b>IssueCoin</b><br>{text}</div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# Sezónna logika (Vianoce, Silvester, január, Black Friday, Veľká noc)
# ───────────────────────────────────────────────────────────────────────────────
def easter_sunday(year: int) -> dt_date:
    # Gaussov algoritmus (gregoriánsky)
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = 1 + ((h + l - 7*m + 114) % 31)
    return dt_date(year, month, day)

def seasonal_window(d: dt_date) -> str:
    # Christmas: 20–27 Dec
    if d.month == 12 and 20 <= d.day <= 27:
        return "christmas"
    # Silvester: 29–31 Dec
    if d.month == 12 and 29 <= d.day <= 31:
        return "silvester"
    # January sales: 1–31 Jan
    if d.month == 1:
        return "jan_sales"
    # Black Friday: 15–25 Nov
    if d.month == 11 and 15 <= d.day <= 25:
        return "black_friday"
    # Easter window: Maundy Thu – Easter Mon
    e = easter_sunday(d.year)
    maundy_thu = e - timedelta(days=3)
    easter_mon = e + timedelta(days=1)
    if maundy_thu <= d <= easter_mon:
        return "easter"
    return "none"

def seasonal_message(d: dt_date, lang: str) -> str:
    tag = seasonal_window(d)
    if lang == "sk":
        if tag == "christmas":
            return random.choice([
                "🎄 Krásne Vianoce! Pokojné dni a úsmev – to je tá najlepšia výbava.",
                "🎁 Vianočné nákupy? Nech sú s radosťou a mierou.",
                "✨ Nech je rozpočet vyvážený ako stromček – tak akurát."
            ])
        if tag == "silvester":
            return random.choice([
                "🎆 Koniec roka je tu – uži si oslavu s rozumom a úsmevom.",
                "🥂 Na zdravie! Nech je nový rok štedrý na radosť, nie na výdavky.",
            ])
        if tag == "jan_sales":
            return random.choice([
                "🛍️ Januárové výpredaje volajú – skvelé sú, keď vedia, čo hľadáš.",
                "💸 Zľavy potešia, rozvaha poteší rozpočet ešte viac."
            ])
        if tag == "black_friday":
            return random.choice([
                "🖤 Black Friday? Zľava nie je dar, ak to nepotrebuješ 😉",
                "💰 Sleduj graf, nie len % – ty si šéf rozpočtu."
            ])
        if tag == "easter":
            return random.choice([
                "🕊️ Pokojné veľkonočné sviatky – trošku koláčov a veľa pohody.",
                "🌿 Zelený štvrtok až Veľkonočný pondelok – pokoj pre dušu aj rozpočet."
            ])
    else:
        if tag == "christmas":
            return random.choice([
                "🎄 Merry Christmas! Calm days and warm smiles.",
                "🎁 Holiday shopping is lovely when mindful and joyful.",
            ])
        if tag == "silvester":
            return random.choice([
                "🎇 Happy New Year’s Eve! Celebrate wisely and with joy.",
                "🥂 Cheers to balance and happiness in the new year!"
            ])
        if tag == "jan_sales":
            return random.choice([
                "🛒 January sales! Great deals, smart choices.",
                "💸 Discounts are fun; smart budgeting is smarter."
            ])
        if tag == "black_friday":
            return random.choice([
                "🖤 Black Friday – don’t buy just because it’s cheap.",
                "💰 Watch your chart, not only the % off."
            ])
        if tag == "easter":
            return random.choice([
                "🌸 Peaceful Easter holidays – rest and smile.",
                "🐣 Easter time – a little sweetness and plenty of calm."
            ])
    return ""  # none

# ───────────────────────────────────────────────────────────────────────────────
# IssueCoin: kontrola chýbajúcich polí a post-save hlášky
# ───────────────────────────────────────────────────────────────────────────────
def missing_fields_message(missing, lang: str) -> str:
    if lang == "sk":
        mapping = {
            "date": "📅 Chýba dátum.",
            "country": "🌍 Vyber krajinu a menu.",
            "amount": "💵 Zadaj sumu (väčšiu než 0).",
            "category": "📂 Vyber kategóriu.",
            "shop": "🏬 Doplň obchod / miesto (krátky názov stačí).",
        }
        tip = "💡 Doplníš to a potom uložíme. Držím palce!"
    else:
        mapping = {
            "date": "📅 Missing date.",
            "country": "🌍 Select country and currency.",
            "amount": "💵 Enter an amount (> 0).",
            "category": "📂 Choose a category.",
            "shop": "🏬 Fill in shop / place (a short name is enough).",
        }
        tip = "💡 Add these and we’ll save it. You’ve got this!"
    parts = [mapping[m] for m in missing if m in mapping]
    return " ".join(parts) + " " + tip

def post_save_issuecoin_message(d: dt_date, total_today: float, count_today: int, category_label: str, lang: str) -> str:
    # Kategóriovo relevantné krátke pochvaly
    cat = category_label.lower()
    if lang == "sk":
        base_pool = [
            f"📊 Dnes máš spolu {total_today:.2f} CZK v {count_today} nákupoch.",
            "👍 Pekné tempo – rozumné nákupy robia silný rozpočet.",
            "🧠 Prehľad je základ – graf máš hneď nižšie 👇",
        ]
        if "potrav" in cat:
            sugg_pool = ["🥦 Skvelé potravinové nákupy.", "🍞 Domáca kuchyňa poteší aj peňaženku."]
        elif "reštaur" in cat or "restaur" in cat:
            sugg_pool = ["🍽️ Pekné – dobré jedlo, dobrá nálada.", "🍷 Uži si, pokojne a s mierou."]
        elif "zábav" in cat or "entertain" in cat:
            sugg_pool = ["🎉 Oddych je dôležitý – dobrá voľba.", "🎬 Vyvážený život, vyvážený rozpočet."]
        elif "odev" in cat or "oblečen" in cat or "clothing" in cat:
            sugg_pool = ["🛍️ Štýlovo a s rozvahou.", "👕 Nech ti to robí radosť dlho."]
        else:
            sugg_pool = ["💡 Malé kroky – veľký efekt.", "✅ Dobrá práca, pokračuj."]
        season_line = seasonal_message(d, lang)
        parts = [random.choice(sugg_pool), random.choice(base_pool)]
        if season_line:
            parts.insert(0, season_line)
        parts.append("📉 Pozri graf výdavkov nižšie 👇")
        return " ".join(parts)
    else:
        base_pool = [
            f"📊 Today you’re at {total_today:.2f} CZK across {count_today} purchase(s).",
            "👍 Nice pace – mindful spending builds strong budgets.",
            "🧠 Clarity first – your chart is below 👇",
        ]
        if "grocer" in cat:
            sugg_pool = ["🥦 Solid grocery choices.", "🍞 Home cooking often helps the wallet."]
        elif "restaur" in cat:
            sugg_pool = ["🍽️ Good food, good mood.", "🍷 Enjoy – calmly and within reason."]
        elif "entertain" in cat:
            sugg_pool = ["🎉 Relax matters – nice choice.", "🎬 Balanced life, balanced budget."]
        elif "cloth" in cat or "shoes" in cat:
            sugg_pool = ["🛍️ Stylish and sensible.", "👕 May it bring joy for long."]
        else:
            sugg_pool = ["💡 Small steps, big effect.", "✅ Nice work, keep going."]
        season_line = seasonal_message(d, lang)
        parts = [random.choice(sugg_pool), random.choice(base_pool)]
        if season_line:
            parts.insert(0, season_line)
        parts.append("📉 Check your spending chart below 👇")
        return " ".join(parts)

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
    # 1) RAG kontrola chýbajúcich polí
    missing = []
    if not d:
        missing.append("date")
    if not country:
        missing.append("country")
    if amount is None or amount <= 0:
        missing.append("amount")
    if not category:
        missing.append("category")
    if not shop.strip():
        missing.append("shop")

    if missing:
        issue_box(missing_fields_message(missing, LANG), seasonal_avatar(dt_date.today(), None))
    else:
        # 2) Výpočet a uloženie
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
                "Rate_value": round(rate, 2),
                "Rate_date": rate_date
            }])
            st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)

            # success line
            if LANG == "sk":
                st.success(f"{TEXTS[LANG]['saved_ok']} → {converted:.2f} CZK "
                           f"— {TEXTS[LANG]['rate_info']}: {rate:.2f} CZK/1 {code} ({TEXTS[LANG]['rate_from']} {rate_date})")
            else:
                st.success(f"{TEXTS[LANG]['saved_ok']} → {converted:.2f} CZK "
                           f"— {TEXTS[LANG]['rate_info']}: {rate:.2f} CZK/1 {code} ({TEXTS[LANG]['rate_from']} {rate_date})")

            # 3) HOLIDAY MESSAGE (priamo použijeme hotový text z get_holiday_name)
            hol_line = get_holiday_name(d, iso2, LANG)
            if hol_line:
                issue_box(hol_line, seasonal_avatar(d, hol_line))

            # 4) THRESHOLD alebo sezónna gentle správa (zostáva)
            df = st.session_state["expenses"]
            sums = df.groupby("Category")["Converted_CZK"].sum() if not df.empty else pd.Series(dtype=float)
            total_for_cat = float(sums.get(category, 0.0))

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

            key = category_key_for_threshold(category)
            limit = THRESHOLDS.get(key, THRESHOLDS["default"])
            if total_for_cat >= limit:
                issue_box(friendly_msg_for(category, total_for_cat - limit), seasonal_avatar(d, None))
            else:
                # vytiahneme jemnú sezónnu vetu (nebije sa s post-save summary)
                gentle = seasonal_message(d, LANG)
                if gentle:
                    issue_box(gentle, seasonal_avatar(d, None))

            # 5) POST-SAVE IssueCoin pochvala + upozornenie na graf
            today_df = df[df["Date"] == d.isoformat()]
            total_today = float(today_df["Converted_CZK"].sum()) if not today_df.empty else converted
            count_today = int(len(today_df)) if not today_df.empty else 1
            issue_box(
                post_save_issuecoin_message(d, total_today, count_today, category, LANG),
                seasonal_avatar(d, None)
            )
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
        alt.Chart(grouped, background=BG)
        .mark_bar()
        .encode(
            x=alt.X("Category", sort="-y", title=TEXTS[LANG]["category"]),
            y=alt.Y("Converted_CZK", title="CZK"),
            tooltip=["Category", "Converted_CZK"]
        )
        .properties(height=320)
        .configure_axis(labelColor=TEXT, titleColor=TEXT, gridColor="#D8D2C4")
        .configure_view(strokeWidth=0)
    )

    # 🧩 zobraz graf
    st.altair_chart(chart, use_container_width=True)

    # Export CSV
    csv = df.to_csv(index=False).encode("utf-8")
    file_name = f"expenses_{dt_date.today().isoformat()}.csv"
    st.download_button(
        label=TEXTS[LANG]["export"],
        data=csv,
        file_name=file_name,
        mime="text/csv",
        key="export_button"
    )



