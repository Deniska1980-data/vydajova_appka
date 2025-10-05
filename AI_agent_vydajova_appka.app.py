# app.py
# ──────────────────────────────────────────────────────────────────────────────
# Expense Diary (SK/CZ + EN) with CNB rates, Calendarific holidays,
# IssueCoin agent messages, saving + chart + export
# ──────────────────────────────────────────────────────────────────────────────

import os
import json
from datetime import datetime, date as dt_date

import altair as alt
import pandas as pd
import requests
import streamlit as st


# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + a bit of CSS (incl. IssueCoin bubble)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Expense Diary", layout="wide", page_icon="💰")

st.markdown(
    """
    <style>
      :root { --pri:#2563eb; --bg:#f8fafc; --txt:#0f172a; }
      html, body, [class*="css"] { font-size:16px; }
      h1 { font-size:28px !important; }
      h2 { font-size:22px !important; }
      .stButton>button { font-size:16px; padding:.6rem 1.1rem; border-radius:10px; }
      .IssueCoin {
         display:flex; gap:14px; align-items:center;
         border:1px solid #cbd5e1; background:#eef6ff;
         border-radius:16px; padding:14px 16px; margin-top:6px;
      }
      .IssueCoin img { width:56px; height:56px; border-radius:50%; object-fit:cover; }
      .IssueCoin .txt { font-size:16px; }
      .smallcaps { font-variant: all-small-caps; letter-spacing:.04em; color:#475569; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# LANGUAGE SWITCH
# ──────────────────────────────────────────────────────────────────────────────
header_l, header_r = st.columns([7, 3])
with header_r:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)

LANG = "sk" if "Slovensky" in lang_choice else "en"

TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": (
            "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB. "
            "Ak pre vybraný deň nie je kurz, použije sa posledný dostupný kurz. "
            "/ CZK = vždy 1:1. Ostatní měny podle denního kurzu ČNB. "
            "Pokud kurz pro den chýba, použije se poslední známý kurz."
        ),
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "category": "📂 Kategória / Kategorie",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť záznam",
        "saved_ok": "Záznam uložený!",
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "list": "🧾 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "category_axis": "Kategória / Kategorie",
        "czk": "CZK",
        "export": "💾 Exportovať do CSV",
        "holiday_title": "🎉 Dnes je sviatok / voľno",
        "holiday_none": "Dnes nie je štátny sviatok.",
        "issuecoin_no_cat": "Pre túto kategóriu zatiaľ nemám hlášku.",
        "issuecoin_csv_bad": "CSV s hláškami má nečakané stĺpce (názvy)."
    },
    "en": {
        "app_title": "💰 Expense Diary",
        "subtitle": (
            "CZK = always 1:1. Other currencies follow CNB daily rates. "
            "If a rate is missing for the day, the last available rate is used."
        ),
        "date": "📅 Purchase date",
        "country": "🌍 Country + currency",
        "amount": "💵 Amount",
        "category": "📂 Category",
        "shop": "🏬 Shop / place",
        "note": "📝 Note",
        "save": "💾 Save entry",
        "saved_ok": "Saved!",
        "rate_err": "❌ Could not fetch exchange rate.",
        "list": "🧾 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "category_axis": "Category",
        "czk": "CZK",
        "export": "💾 Export CSV",
        "holiday_title": "🎉 It's a holiday today",
        "holiday_none": "No public holiday today.",
        "issuecoin_no_cat": "I don't have a message for this category yet.",
        "issuecoin_csv_bad": "Messages CSV doesn't have expected column names."
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# CATEGORY LISTS (rozšírené podľa tvojho zoznamu)
# ──────────────────────────────────────────────────────────────────────────────
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
        "Vzdelávanie / kurzy 📚 / Vzdělávání / kurzy 📚",
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
        "Education / Courses 📚",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# COUNTRIES + currency code (CNB codes) – zoznam, ktorý si poslala
# ──────────────────────────────────────────────────────────────────────────────
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
        "Japonsko – JPY ¥",
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
        "Japan – JPY ¥",
    ],
}

# valuta code (CNB) z popisu v labeli
COUNTRY_TO_CODE = {}
for label in COUNTRIES["sk"] + COUNTRIES["en"]:
    code = label.split("–")[-1].strip().split()[0]
    COUNTRY_TO_CODE[label] = code

# ISO2 kódy krajín pre Calendarific
ISO2 = {
    "Czechia – CZK Kč": "CZ",
    "Česko – CZK Kč": "CZ",
    "Slovakia – EUR €": "SK",
    "Slovensko – EUR €": "SK",
    "Germany – EUR €": "DE",
    "Nemecko – EUR € / Německo – EUR €": "DE",
    "Austria – EUR €": "AT",
    "Rakúsko – EUR € / Rakousko – EUR €": "AT",
    "France – EUR €": "FR",
    "Francúzsko – EUR € / Francie – EUR €": "FR",
    "Spain – EUR €": "ES",
    "Španielsko – EUR € / Španělsko – EUR €": "ES",
    "Italy – EUR €": "IT",
    "Taliansko – EUR € / Itálie – EUR €": "IT",
    "Netherlands – EUR €": "NL",
    "Holandsko – EUR € / Nizozemsko – EUR €": "NL",
    "Belgium – EUR €": "BE",
    "Belgicko – EUR € / Belgie – EUR €": "BE",
    "Finland – EUR €": "FI",
    "Fínsko – EUR € / Finsko – EUR €": "FI",
    "Ireland – EUR €": "IE",
    "Írsko – EUR € / Irsko – EUR €": "IE",
    "Portugal – EUR €": "PT",
    "Grécko – EUR € / Řecko – EUR €": "GR",
    "Greece – EUR €": "GR",
    "Slovenia – EUR €": "SI",
    "Slovinsko – EUR €": "SI",
    "Lithuania – EUR €": "LT",
    "Litva – EUR €": "LT",
    "Latvia – EUR €": "LV",
    "Lotyšsko – EUR €": "LV",
    "Estonia – EUR €": "EE",
    "Estónsko – EUR €": "EE",
    "Malta – EUR €": "MT",
    "Cyprus – EUR €": "CY",
    "Croatia – EUR €": "HR",
    "Chorvátsko – EUR € / Chorvatsko – EUR €": "HR",
    "USA – USD $": "US",
    "United Kingdom – GBP £": "GB",
    "Veľká Británia – GBP £ / Velká Británie – GBP £": "GB",
    "Poland – PLN zł": "PL",
    "Poľsko – PLN zł / Polsko – PLN zł": "PL",
    "Hungary – HUF Ft": "HU",
    "Maďarsko – HUF Ft / Maďarsko – HUF Ft": "HU",
    "Switzerland – CHF ₣": "CH",
    "Švajčiarsko – CHF ₣ / Švýcarsko – CHF ₣": "CH",
    "Denmark – DKK kr": "DK",
    "Dánsko – DKK kr / Dánsko – DKK kr": "DK",
    "Sweden – SEK kr": "SE",
    "Švédsko – SEK kr / Švédsko – SEK kr": "SE",
    "Norway – NOK kr": "NO",
    "Nórsko – NOK kr / Norsko – NOK kr": "NO",
    "Canada – CAD $": "CA",
    "Japan – JPY ¥": "JP",
}

# ──────────────────────────────────────────────────────────────────────────────
# INITIAL STATE
# ──────────────────────────────────────────────────────────────────────────────
if "expenses" not in st.session_state:
    st.session_state["expenses"] = pd.DataFrame(
        columns=[
            "Date",
            "Country",
            "Currency",
            "Amount",
            "Category",
            "Shop",
            "Note",
            "Converted_CZK",
            "Rate_value",
            "Rate_date",
        ]
    )

# ──────────────────────────────────────────────────────────────────────────────
# CNB RATES (TXT feed)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def cnb_txt_for(date_str: str | None):
    """Return denni_kurz.txt as text for given date (or latest if None)."""
    if date_str:
        url = (
            "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/"
            "kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
            f"?date={date_str}"
        )
    else:
        url = (
            "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/"
            "kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
        )
    r = requests.get(url, timeout=10)
    return r.text if r.status_code == 200 else None


def parse_rate_from_txt(txt: str | None, code: str):
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
                except Exception:
                    return None, None, header_date
    return None, None, header_date


def get_rate_for(code: str, d: dt_date):
    """Return (rate_per_one_unit_in_CZK, rate_date_iso) or (None, None)"""
    if code == "CZK":
        return 1.0, d.isoformat()
    d_str = d.strftime("%d.%m.%Y")
    txt = cnb_txt_for(d_str)
    rate, qty, header_date = parse_rate_from_txt(txt, code)
    if rate is None:
        txt2 = cnb_txt_for(None)  # latest available
        rate, qty, header_date = parse_rate_from_txt(txt2, code)
        rate_date_iso = datetime.today().date().isoformat()
    else:
        rate_date_iso = (
            datetime.strptime(header_date, "%d.%m.%Y").date().isoformat()
            if header_date
            else d.isoformat()
        )
    if rate is None or not qty:
        return None, None
    return rate / qty, rate_date_iso


# ──────────────────────────────────────────────────────────────────────────────
# HOLIDAYS – Calendarific
# ──────────────────────────────────────────────────────────────────────────────
CALENDARIFIC_API_KEY = "SspqB3Ivo4c9xnvpAgX6XGyJMdOHMXRE"  # tvoj kľúč
CAL_BASE = "https://calendarific.com/api/v2/holidays"


@st.cache_data(ttl=60 * 60)  # cache 1h
def is_public_holiday(iso2: str, d: dt_date) -> dict | None:
    """
    Returns holiday dict if the given date is a (national/local) holiday in country iso2,
    else None. We restrict by year/month/day to keep the payload small.
    """
    try:
        params = {
            "api_key": CALENDARIFIC_API_KEY,
            "country": iso2,
            "year": d.year,
            "month": d.month,
            "day": d.day,
            # we let all types come back and then filter typical public holiday classes:
        }
        r = requests.get(CAL_BASE, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        holidays = data.get("response", {}).get("holidays", [])
        for h in holidays:
            # Typical classes that mean voľno
            types = [t.lower() for t in h.get("type", [])]
            if any(t in types for t in ("national", "public", "bank", "local", "observance")):
                # exact date match safeguard
                iso = h.get("date", {}).get("iso", "")
                if iso.startswith(str(d)):
                    return h
        return None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# LOAD IssueCoin messages CSV (kategórie) – robustné čítanie
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_issuecoin_messages():
    """
    Expect CSV in root:
      AI_agent_kategorie_hlasky.csv
    Columns:
      'Kategória/kategorie (SK_CZ)','Hláška_SK_CZ','Category (EN)','Hláška_EN'
    (Ak je použitý iný oddeľovač, pokúsime sa o auto fallback.)
    """
    fname = "AI_agent_kategorie_hlasky.csv"
    if not os.path.exists(fname):
        return pd.DataFrame()

    def _try_read(sep):
        return pd.read_csv(fname, sep=sep, encoding="utf-8")

    try:
        df = _try_read(",")
        if df.shape[1] == 1:  # vyzerá to skôr na ;
            df = _try_read(";")
    except Exception:
        try:
            df = _try_read(";")
        except Exception:
            return pd.DataFrame()

    # normalize columns (strip)
    df.columns = [c.strip() for c in df.columns]
    return df


MESSAGES_DF = load_issuecoin_messages()


def show_issuecoin_bubble(text: str):
    st.markdown(
        f"""
        <div class="IssueCoin">
            <img src="obrazek_IssuaCoin_by_Deny.JPG" alt="IssueCoin"/>
            <div class="txt">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def issuecoin_for(category_label: str):
    """
    Z CSV vyberie správu podľa kategórie a jazyka. Fallback ak CSV/chýba.
    """
    if MESSAGES_DF.empty:
        # fallback vtipné hlášky:
        fallback = {
            "sk": "Agent IssueCoin hlási: držíme rozpočet 👍",
            "en": "IssueCoin says: staying on budget 👍",
        }
        show_issuecoin_bubble(fallback[LANG])
        return

    # očakávané názvy
    sk_cat_col = "Kategória/kategorie (SK_CZ)"
    sk_msg_col = "Hláška_SK_CZ"
    en_cat_col = "Category (EN)"
    en_msg_col = "Hláška_EN"

    if not all(c in MESSAGES_DF.columns for c in [sk_cat_col, sk_msg_col, en_cat_col, en_msg_col]):
        st.warning(TEXTS[LANG]["issuecoin_csv_bad"])
        return

    if LANG == "sk":
        row = MESSAGES_DF[MESSAGES_DF[sk_cat_col] == category_label]
        if not row.empty:
            msg = row[sk_msg_col].sample(1).iloc[0]
            show_issuecoin_bubble(msg)
        else:
            st.info(TEXTS[LANG]["issuecoin_no_cat"])
    else:  # EN
        row = MESSAGES_DF[MESSAGES_DF[en_cat_col] == category_label]
        if not row.empty:
            msg = row[en_msg_col].sample(1).iloc[0]
            show_issuecoin_bubble(msg)
        else:
            st.info(TEXTS[LANG]["issuecoin_no_cat"])


# ──────────────────────────────────────────────────────────────────────────────
# UI HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])

# ──────────────────────────────────────────────────────────────────────────────
# INPUT FORM
# ──────────────────────────────────────────────────────────────────────────────
with st.form("form"):
    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today(), min_value=dt_date(2020, 1, 1))
        country = st.selectbox(TEXTS[LANG]["country"], COUNTRIES[LANG])
        category = st.selectbox(TEXTS[LANG]["category"], CATEGORIES[LANG])
    with c2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, step=1.0, value=0.0)
        shop = st.text_input(TEXTS[LANG]["shop"])
        note = st.text_input(TEXTS[LANG]["note"])

    submit = st.form_submit_button(TEXTS[LANG]["save"])

# ──────────────────────────────────────────────────────────────────────────────
# AFTER SAVE
# ──────────────────────────────────────────────────────────────────────────────
if submit:
    code = COUNTRY_TO_CODE.get(country, "CZK")
    per_unit, rate_date = get_rate_for(code, d)
    if per_unit is None:
        st.error(TEXTS[LANG]["rate_err"])
    else:
        converted = round(amount * per_unit, 2)
        # uloženie do session
        new_row = pd.DataFrame(
            [
                {
                    "Date": d.isoformat(),
                    "Country": country,
                    "Currency": code,
                    "Amount": amount,
                    "Category": category,
                    "Shop": shop,
                    "Note": note,
                    "Converted_CZK": converted,
                    "Rate_value": round(per_unit, 4),
                    "Rate_date": rate_date,
                }
            ]
        )
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_row], ignore_index=True)
        st.success(
            f"{TEXTS[LANG]['saved_ok']}  →  {converted:.2f} {TEXTS[LANG]['czk']} "
            f"(1 {code} = {per_unit:.4f} CZK, {rate_date})"
        )

        # 1) IssueCoin: hláška podľa kategórie
        issuecoin_for(category)

        # 2) Sviatok – Calendarific
        iso2 = ISO2.get(country)
        if iso2:
            hol = is_public_holiday(iso2, d)
            if hol:
                title = hol.get("name", TEXTS[LANG]["holiday_title"])
                desc = hol.get("description") or ""
                show_issuecoin_bubble(f"🎉 <b>{title}</b><br>{desc}")
            # ak nie je sviatok – žiadna hláška (presne ako chceš)

# ──────────────────────────────────────────────────────────────────────────────
# LIST + SUMMARY + CHART + EXPORT
# ──────────────────────────────────────────────────────────────────────────────
st.subheader(TEXTS[LANG]["list"])
df = st.session_state["expenses"]
st.dataframe(df, use_container_width=True)

if not df.empty:
    st.subheader(TEXTS[LANG]["summary"])
    total = df["Converted_CZK"].sum()
    st.metric(TEXTS[LANG]["total"], f"{total:.2f} CZK")

    grouped = df.groupby("Category", as_index=False)["Converted_CZK"].sum()
    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("Category", sort="-y", title=TEXTS[LANG]["category_axis"]),
            y=alt.Y("Converted_CZK", title="CZK"),
            tooltip=["Category", "Converted_CZK"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)

    # export
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=TEXTS[LANG]["export"],
        data=csv,
        file_name=f"expenses_{dt_date.today().isoformat()}.csv",
        mime="text/csv",
    )
