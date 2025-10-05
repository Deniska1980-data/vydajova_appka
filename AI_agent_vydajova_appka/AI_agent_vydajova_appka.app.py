import streamlit as st
import pandas as pd
import os
from datetime import date as dt_date

st.set_page_config(page_title="Expense Diary", layout="wide")

# ---------------------------
# 💅 CSS dizajn výťahu
# ---------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f2f2f2;
        padding: 0;
    }
    .lift-container {
        background: linear-gradient(180deg, #dcdcdc 0%, #f7f7f7 100%);
        border: 6px solid #6b6b6b;
        border-radius: 12px;
        box-shadow: 0 0 30px rgba(0,0,0,0.2);
        padding: 30px;
        margin-top: 20px;
    }
    .lift-top {
        background: #6b6b6b;
        height: 15px;
        border-radius: 12px 12px 0 0;
    }
    .lift-bottom {
        background: #6b6b6b;
        height: 15px;
        border-radius: 0 0 12px 12px;
        margin-bottom: 20px;
    }
    html, body, [class*="css"]  {
        font-size: 16px;  
        line-height: 1.6;
    }
    h1 { font-size: 28px !important; text-align: center; }
    h2 { font-size: 24px !important; text-align: center; }
    .stButton>button {
        font-size: 18px;
        padding: 10px 20px;
    }
    .stSelectbox>div>div {
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------
# Jazykový prepínač + mikrofón
# ---------------------------
col_lang, col_mic = st.columns([8, 2])
with col_lang:
    lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
with col_mic:
    mic_on = st.toggle("🎤 Mikrofón", value=False)
LANG = "sk" if "Slovensky" in lang_choice else "en"

# ---------------------------
# Preklady
# ---------------------------
TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB.",
        "date": "📅 Dátum nákupu / Datum nákupu",
        "country": "🌍 Krajina + mena / Měna",
        "amount": "💵 Suma / Částka",
        "category": "📂 Kategória / Kategorie",
        "shop": "🏬 Obchod / miesto / Obchod / místo",
        "note": "📝 Poznámka",
        "save": "📂 Uložiť nákup / Uložit nákup",
        "list": "🛒 Zoznam nákupov / Seznam nákupů",
        "summary": "📊 Súhrn mesačných výdavkov / Souhrn měsíčních výdajů",
        "total": "Celkové výdavky / Celkové výdaje",
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "saved_ok": "Záznam uložený!",
        "no_data": "Zatiaľ žiadne záznamy.",
        "mic_status": "🎤 Mikrofón je zapnutý" if mic_on else "🎤 Mikrofón je vypnutý"
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
        "save": "📂 Save purchase",
        "list": "🛒 Purchase list",
        "summary": "📊 Monthly expenses summary",
        "total": "Total expenses",
        "rate_err": "❌ Could not fetch exchange rate.",
        "saved_ok": "Saved!",
        "no_data": "No data yet.",
        "mic_status": "🎤 Microphone is ON" if mic_on else "🎤 Microphone is OFF"
    }
}

# ---------------------------
# Výťah – začiatok
# ---------------------------
st.markdown('<div class="lift-top"></div>', unsafe_allow_html=True)
st.markdown('<div class="lift-container">', unsafe_allow_html=True)

st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])

# Stav jazyka a mikrofónu
st.write(f"**{TEXTS[LANG]['mic_status']}**  |  🌐 **{LANG.upper()}**")

# ---------------------------
# Formulár pre zadanie výdavku
# ---------------------------
with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input(TEXTS[LANG]["date"], value=dt_date.today(), key="purchase_date")
        currency = st.selectbox(TEXTS[LANG]["country"], ["CZK", "EUR", "USD"], key="currency")
        category = st.text_input(TEXTS[LANG]["category"], key="category")
    with col2:
        amount = st.number_input(TEXTS[LANG]["amount"], min_value=0.0, key="amount")
        shop = st.text_input(TEXTS[LANG]["shop"], key="shop")
        note = st.text_input(TEXTS[LANG]["note"], key="note")

    submitted = st.form_submit_button(TEXTS[LANG]["save"])

# ---------------------------
# Ukladanie do CSV
# ---------------------------
csv_file = "expenses.csv"
if submitted:
    new_row = {
        "date": date,
        "currency": currency,
        "amount": amount,
        "category": category,
        "shop": shop,
        "note": note
    }

    df_new = pd.DataFrame([new_row])

    if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(csv_file, index=False)
    st.success(TEXTS[LANG]["saved_ok"])

# ---------------------------
# Zobrazenie zoznamu nákupov
# ---------------------------
if st.button(TEXTS[LANG]["list"]):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        st.dataframe(df)
        st.info(f"{TEXTS[LANG]['total']}: {df['amount'].sum():.2f} {df['currency'].iloc[-1]}")
    else:
        st.warning(TEXTS[LANG]["no_data"])

# ---------------------------
# Výťah – koniec
# ---------------------------
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="lift-bottom"></div>', unsafe_allow_html=True)

