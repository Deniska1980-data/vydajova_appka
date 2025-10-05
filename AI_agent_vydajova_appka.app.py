# app.py
import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import datetime, date as dt_date

st.set_page_config(page_title="Expense Diary · IssueCoin", layout="wide")

# =========================
# ---- Constants/Config ----
# =========================
CALENDARIFIC_KEY = st.secrets.get("CALENDARIFIC_KEY", "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE")
CALENDARIFIC_URL = "https://calendarific.com/api/v2/holidays"

CNB_TXT_DAILY = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
CNB_TXT_DAILY_AT = CNB_TXT_DAILY + "?date={date}"

# =========================
# --------- CSS -----------
# =========================
st.markdown("""
<style>
:root{
  --bubble:#eaf3ff;
  --bubble-en:#eaf7ea;
  --avatarW:72px;
}
h1{margin-bottom:.25rem}
.stButton>button{font-size:16px;padding:.5rem 1rem;border-radius:10px}
.label-small{opacity:.8;font-size:.9rem}
.gdpr-note{background:#eef6ff;border:1px solid #dbe9ff;padding:.5rem .75rem;border-radius:10px;color:#0b3a63}
.msg-row{display:flex;gap:12px;align-items:flex-start;margin:.35rem 0}
.msg-av{width:var(--avatarW);min-width:var(--avatarW);display:flex;justify-content:center}
.msg-bubble{background:var(--bubble);border:1px solid #dce9ff;padding:.65rem .8rem;border-radius:14px;box-shadow:0 1px 0 rgba(0,0,0,.04)}
.msg-bubble.en{background:var(--bubble-en);border-color:#d8f0d6}
.msg-title{font-weight:700;margin-bottom:.2rem}
.ic-pre{font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        line-height:1.05; white-space:pre; font-size:20px;}
hr.soft{opacity:.15;margin:1rem 0}
</style>
""", unsafe_allow_html=True)

# =========================
# ------ Translations -----
# =========================
TEXTS = {
    "sk": {
        "lang": "Slovensky / Česky",
        "title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB.",
        "gdpr": "🔒 Táto aplikácia neukladá žiadne osobné údaje. Dáta sa spracovávajú len lokálne vo tvojom zariadení (žiadny server, GDPR friendly).",
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "category": "📂 Kategória / Kategorie",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť nákup / Uložit nákup",
        "saved": "Záznam uložený!",
        "applied": "— Použitý kurz",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčných výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "category_axis": "Kategória / Kategorie",
        "export": "⬇️ Export CSV",
        "holiday_today": "🎉 Dnes je sviatok:",
        "no_holiday": "",
    },
    "en": {
        "lang": "English",
        "title": "💰 Expense Diary",
        "subtitle": "CZK = always 1:1. Other currencies follow CNB daily rates.",
        "gdpr": "🔒 This app does not store or send any personal data. Everything runs locally on your device (GDPR friendly).",
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "category": "📂 Category",
        "shop": "🏬 Shop / place",
        "note": "📝 Note",
        "save": "💾 Save purchase",
        "saved": "Saved!",
        "applied": "— Applied rate",
        "list": "🧾 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "category_axis": "Category",
        "export": "⬇️ Export CSV",
        "holiday_today": "🎉 Today is a public holiday:",
        "no_holiday": "",
    }
}

# =========================
# ---- Countries (CNB) ----
# =========================
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

COUNTRY_TO_CODE, COUNTRY_TO_ISO = {}, {}

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

# =========================
# ------ Categories -------
# =========================
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
        "Vzdelávanie / kurzy 📚 / Vzdělávání / kurzy 📚",
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
        "Education / Courses 📚",
    ],
}

# mapa na "core" kategóriu pre prahy
def to_core_cat(lang, label):
    t = label.lower()
    if ("potraviny" in t) or ("grocer" in t): return "groceries"
    if ("reštaur" in t) or ("restaur" in t): return "restaurants"
    if ("zábav" in t) or ("entertain" in t): return "entertainment"
    return "other"

def limit_for(core):
    if core in ("restaurants", "entertainment"): return 1000
    if core == "groceries": return 6500
    return 2500

# =========================
# ----- State / Storage ----
# =========================
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(columns=[
        "Date","Country","Currency","Amount","Category","Shop","Note","Converted_CZK","Rate_value","Rate_date"
    ])

# =========================
# ------- CNB rates -------
# =========================
@st.cache_data(ttl=600)
def _fetch_txt(url: str):
    try:
        r = requests.get(url, timeout=10)
        return r.text if r.status_code == 200 else None
    except Exception:
        return None

def _parse_cnb(txt: str, code: str):
    if not txt: return None, None
    lines = txt.splitlines()
    head = lines[0].split(" #")[0].strip() if lines else None
    for line in lines[2:]:
        parts = line.strip().split("|")
        if len(parts) == 5:
            _, _, qty, ccode, rate = parts
            if ccode == code:
                try:
                    q = float(qty.replace(",", "."))
                    r = float(rate.replace(",", "."))
                    return r / q, head
                except Exception:
                    return None, head
    return None, head

def get_rate_for(code: str, d: dt_date):
    """Return (rate per 1 unit in CZK, rate_date_iso)"""
    if code == "CZK":
        return 1.0, d.isoformat()
    dstr = d.strftime("%d.%m.%Y")
    txt = _fetch_txt(CNB_TXT_DAILY_AT.format(date=dstr))
    rate, head = _parse_cnb(txt, code)
    if rate is None:
        txt2 = _fetch_txt(CNB_TXT_DAILY)  # fallback latest
        rate, head = _parse_cnb(txt2, code)
        rdate = datetime.today().date().isoformat()
    else:
        rdate = datetime.strptime(head, "%d.%m.%Y").date().isoformat()
    return rate, rdate

# =========================
# ---- Calendarific API ----
# =========================
@st.cache_data(ttl=24*3600)
def holiday_name_on(iso2: str, d: dt_date):
    """Vráti názov sviatku (ak existuje), s prekladom pre SK/CZ."""
    if not iso2 or not CALENDARIFIC_KEY:
        return ""
    params = {
        "api_key": CALENDARIFIC_KEY,
        "country": iso2,
        "year": d.year,
        "month": d.month,
        "day": d.day
    }
    try:
        r = requests.get(CALENDARIFIC_URL, params=params, timeout=10)
        if r.status_code != 200:
            return ""
        js = r.json()
        hol = js.get("response", {}).get("holidays", [])
        if not hol:
            return ""
        name = hol[0].get("name", "")
        # Preklady niektorých známych sviatkov
        translations = {
            "Christmas Eve": "Štedrý večer / Štědrý večer (Vianoce / Vánoce)",
            "Christmas Day": "1. sviatok vianočný / 1. svátek vánoční",
            "Boxing Day": "2. sviatok vianočný / 2. svátek vánoční",
            "New Year's Day": "Nový rok",
            "Easter Sunday": "Veľkonočná nedeľa / Velikonoční neděle",
            "Easter Monday": "Veľkonočný pondelok / Velikonoční pondělí",
            "Good Friday": "Veľký piatok / Velký pátek",
        }
        if name in translations:
            name = translations[name]
        return name
    except Exception:
        return ""

# =========================
# ----- IssueCoin UI ------
# =========================
def season_for(d: dt_date):
    m = d.month
    if m in (12,1,2): return "winter"
    if m in (3,4,5): return "spring"
    if m in (6,7,8): return "summer"
    return "autumn"

def avatar_ascii(d: dt_date):
    """Panáčik s doplnkami podľa obdobia (šál okolo krku, čiapka, okuliare...)"""
    s = season_for(d)
    hat = "  🎅\n" if (d.month == 12 and 20 <= d.day <= 26) else ""
    head = "   🔵\n"
    scarf = "  🧣\n" if s == "winter" else ""
    arms = "  /│\\\n"
    legs = "  / \\\n"

    if s == "summer":
        head = "   😎\n"
    if s == "spring":
        arms = "  💪│💪\n"
    if s == "autumn":
        legs = "   🍄\n"

    # Panáčik má šál pod hlavou, aby vyzeral realisticky
    return f"{hat}{head}{scarf}{arms}{legs}"

def bubble(text: str, lang: str, d: dt_date):
    css_extra = "" if lang=="sk" else " en"
    st.markdown(
        f"""
        <div class="msg-row">
          <div class="msg-av"><pre class="ic-pre">{avatar_ascii(d)}</pre></div>
          <div class="msg-bubble{css_extra}">
            <div class="msg-title">IssueCoin</div>
            <div>{text}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def nudge_message(lang: str, core: str, total_czk: float, d: dt_date):
    s = season_for(d)
    if lang=="en":
        if core=="restaurants":
            if total_czk>=1000: return "Treats are great — maybe pace them a little next week. 😉"
        elif core=="entertainment":
            if total_czk>=1000: return "Fun is important! Keep an eye so it stays fun for your budget too. 🙂"
        elif core=="groceries":
            if total_czk>=6500: return "Groceries add up — all good if it's planned. 👍"
        else:
            if total_czk>=2500: return "Nice month of spending — looks reasonable so far."
        # seasonal nicety
        if s=="winter": return "Happy holidays! Keep both tea and budget warm. ☺️"
        if s=="summer": return "Summer vibes — enjoy the sun, and keep receipts cool. 😎"
        if s=="spring": return "Fresh start — small steps make strong budgets. 💪"
        if s=="autumn": return "Autumn calm — let expenses be like a forest walk: easy."
        return ""
    else:
        if core=="restaurants":
            if total_czk>=1000: return "Dobroty sú super — skús ich budúci týždeň trošku pribrzdiť. 😉"
        elif core=="entertainment":
            if total_czk>=1000: return "Zábava je dôležitá! Nech je fajn aj pre rozpočet. 🙂"
        elif core=="groceries":
            if total_czk>=6500: return "Potraviny vedia narást — fajn, ak je to v pláne. 👍"
        else:
            if total_czk>=2500: return "Vyzerá to na vydarený mesiac. Zatiaľ rozumne. 🙂"
        if s=="winter": return "Krásne sviatky! Teplý čaj a teplý rozpočet. ☺️"
        if s=="summer": return "Letná pohoda — uži si slnko a účtenky drž v chládku. 😎"
        if s=="spring": return "Jarný štart — malé kroky robia silný rozpočet. 💪"
        if s=="autumn": return "Jesenná pohoda — nech sú výdaje ako lesná vychádzka: pokojné."
        return ""

# =========================
# --------- UI ------------
# =========================
colL, colR = st.columns([7,3], vertical_alignment="center")
with colR:
    lang_choice = st.selectbox("🌐 Language / Jazyk", [TEXTS["sk"]["lang"], TEXTS["en"]["lang"]], index=0)
LANG = "sk" if "Slovensky" in lang_choice else "en"

st.title(TEXTS[LANG]["title"])
st.caption(TEXTS[LANG]["subtitle"])
st.markdown(f'<div class="gdpr-note">{TEXTS[LANG]["gdpr"]}</div>', unsafe_allow_html=True)

# form
with st.form("entry"):
    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today(), min_value=dt_date(2024,1,1))
        country = st.selectbox(TEXTS[LANG]["country"], COUNTRIES[LANG])
        category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    with c2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, step=1.0, value=0.0, format="%.2f")
        shop = st.text_input(TEXTS[LANG]["shop"])
        note = st.text_input(TEXTS[LANG]["note"])
    submit = st.form_submit_button(TEXTS[LANG]["save"])

if submit:
    code = COUNTRY_TO_CODE[country]
    iso2 = COUNTRY_TO_ISO[country]
    rate, rdate = get_rate_for(code, d)
    if rate is None:
        st.error("❌ CNB rate could not be fetched.")
    else:
        converted = round(amount * rate, 2)
        new_row = pd.DataFrame([{
            "Date": d.isoformat(),
            "Country": country,
            "Currency": code,
            "Amount": round(amount,2),
            "Category": category,
            "Shop": shop,
            "Note": note,
            "Converted_CZK": converted,
            "Rate_value": round(rate,4),
            "Rate_date": rdate
        }])
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)
        if LANG=="en":
            st.success(f"{TEXTS[LANG]['saved']} ({converted:.2f} CZK) {TEXTS[LANG]['applied']} {rate:.2f} CZK/1 {code} (as of {rdate})")
        else:
            st.success(f"{TEXTS[LANG]['saved']} ({converted:.2f} CZK) {TEXTS[LANG]['applied']} {rate:.2f} CZK/1 {code} (k {rdate})")

        # ---- Holiday message
        hol = holiday_name_on(iso2, d)
        if hol:
            txt = f"{TEXTS[LANG]['holiday_today']} <b>{hol}</b>."
            bubble(txt, LANG, d)

        # ---- Spending nudge per month/category
        df = st.session_state["expenses"]
        month_mask = (pd.to_datetime(df["Date"]).dt.to_period("M") == pd.Period(d.strftime("%Y-%m")))
        dfm = df.loc[month_mask].copy()
        core = to_core_cat(LANG, category)
        total_czk = float(dfm.loc[dfm["Category"]==category, "Converted_CZK"].sum())
        msg = nudge_message(LANG, core, total_czk, d)
        if msg:
            bubble(msg, LANG, d)

st.markdown("<hr class='soft'/>", unsafe_allow_html=True)

# ======= Table + Summary =======
st.subheader(TEXTS[LANG]["list"])
df = st.session_state["expenses"].copy()
st.dataframe(df, use_container_width=True)

if not df.empty:
    st.subheader(TEXTS[LANG]["summary"])
    total = df["Converted_CZK"].sum()
    st.metric(TEXTS[LANG]["total"], f"{total:.2f} CZK")

    # graf – sumy podľa kategórie (aktuálny mesiac)
    cur_month = datetime.today().strftime("%Y-%m")
    month_mask = (pd.to_datetime(df["Date"]).dt.to_period("M") == pd.Period(cur_month))
    g = df.loc[month_mask].groupby("Category", as_index=False)["Converted_CZK"].sum()
    if not g.empty:
        ch = (
            alt.Chart(g)
            .mark_bar()
            .encode(
                x=alt.X("Category:N", sort="-y", title=TEXTS[LANG]["category_axis"]),
                y=alt.Y("Converted_CZK:Q", title="CZK"),
                tooltip=["Category","Converted_CZK"]
            )
            .properties(height=300)
        )
        st.altair_chart(ch, use_container_width=True)

    # export
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(TEXTS[LANG]["export"], data=csv, file_name=f"expenses_{dt_date.today().isoformat()}.csv", mime="text/csv")

