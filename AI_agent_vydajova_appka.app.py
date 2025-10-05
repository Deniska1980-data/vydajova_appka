import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date

st.set_page_config(page_title="Expense Diary / Výdavkový denník", layout="wide")

# -------------------------------------------------
# CSS (upravený panáčik)
# -------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 16px; line-height: 1.6; }
h1 { font-size: 28px !important; }
h2 { font-size: 24px !important; }
.stButton>button { font-size: 18px; padding: 10px 20px; }

.issuecoin-wrap { 
  display:flex; 
  align-items:flex-start; 
  gap:12px; 
  margin-top:14px; 
}

.issuecoin-bubble {
  background:#eaf6ff; 
  padding:12px 16px; 
  border-radius:14px;
  box-shadow:2px 2px 6px rgba(0,0,0,0.08); 
  font-size:16px;
}

/* 🔧 PANÁČIK UPRAVENÝ — hlava nad telom */
.issuecoin-figure {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  line-height: 1;
  min-width: 60px;
}
.issuecoin-head { 
  font-size: 40px; 
  position: relative; 
  top: 3px; 
  animation: wink 7s infinite; 
}
.issuecoin-body { 
  font-family: monospace; 
  font-size: 18px; 
  line-height: 1.2; 
}
@keyframes wink { 
  0%, 92%, 100% { opacity: 1; } 
  96% { opacity: 0.3; } 
}

.gdpr { 
  background:#f6faf7; 
  border-left:6px solid #42b883; 
  padding:12px 14px; 
  border-radius:10px; 
}
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
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "saved_ok": "✅ Záznam uložený!",
        "rate_info": "Použitý kurz",
        "rate_from": "k",
        "export": "💾 Exportovať do CSV",
        "gdpr": "ℹ️ Táto aplikácia neukladá ani neposiela žiadne osobné údaje. 💾",
        "holiday_prefix": "🎉 Dnes je sviatok:",
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
        "rate_err": "❌ Could not fetch exchange rate.",
        "saved_ok": "✅ Saved!",
        "rate_info": "Applied rate",
        "rate_from": "as of",
        "export": "💾 Export CSV",
        "gdpr": "ℹ️ This app does not store or send personal data. 💾",
        "holiday_prefix": "🎉 Today is a public holiday:",
    }
}

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

def get_rate_for(code: str):
    if code == "CZK":
        return 1.0, datetime.today().date().isoformat()
    txt = fetch_cnb_txt_latest()
    rate, qty, header_date = parse_rate_from_txt(txt, code)
    if rate is None or not qty:
        return None, None
    return rate / qty, datetime.strptime(header_date, "%d.%m.%Y").date().isoformat()

# -------------------------------------------------
# UI HEADER
# -------------------------------------------------
st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])
st.markdown(f'<div class="gdpr">{TEXTS[LANG]["gdpr"]}</div>', unsafe_allow_html=True)

# -------------------------------------------------
# PANÁČIK (upravený)
# -------------------------------------------------
def show_issuecoin_message(msg: str):
    st.markdown(f"""
        <div class="issuecoin-wrap">
            <div class="issuecoin-figure">
                <div class="issuecoin-head">🔵</div>
                <div class="issuecoin-body">/│\\<br>/ \\</div>
            </div>
            <div class="issuecoin-bubble">
                <strong>IssueCoin</strong><br>{msg}
            </div>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# FORM
# -------------------------------------------------
with st.form("form"):
    d = st.date_input(TEXTS[LANG]["date"], value=dt_date.today())
    country = st.text_input(TEXTS[LANG]["country"])
    category = st.text_input(TEXTS[LANG]["category"])
    amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0)
    shop = st.text_input(TEXTS[LANG]["shop"])
    note = st.text_input(TEXTS[LANG]["note"])
    submit = st.form_submit_button(TEXTS[LANG]["save"])

# -------------------------------------------------
# SAVE
# -------------------------------------------------
if submit:
    rate, rate_date = get_rate_for("EUR")
    if rate:
        converted = round(amount * rate, 2)
        st.session_state["expenses"] = pd.concat([
            st.session_state["expenses"],
            pd.DataFrame([{
                "Date": d.isoformat(), "Country": country, "Currency": "EUR",
                "Amount": amount, "Category": category, "Shop": shop, "Note": note,
                "Converted_CZK": converted, "Rate_value": rate, "Rate_date": rate_date
            }])
        ], ignore_index=True)
        st.success(f"{TEXTS[LANG]['saved_ok']} {converted} CZK — {TEXTS[LANG]['rate_info']}: {round(rate,4)} CZK/1 EUR ({TEXTS[LANG]['rate_from']} {rate_date})")
        show_issuecoin_message("🎉 Dnes je sviatok: Harvest Festival.")
    else:
        st.error(TEXTS[LANG]["rate_err"])

# -------------------------------------------------
# TABLE
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
        .encode(x="Category", y="Converted_CZK", tooltip=["Category", "Converted_CZK"])
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)
