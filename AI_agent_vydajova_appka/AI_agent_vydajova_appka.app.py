import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date
import os

st.set_page_config(page_title="Expense Diary", layout="wide")

# ---------------------------
# 💅 CSS: výťahová kabína
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
# 🔁 Jazykový a mikrofónový prepínač
# ---------------------------
with st.container():
    col_lang, col_mic = st.columns([8,2])
    with col_lang:
        lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
    with col_mic:
        mic_toggle = st.toggle("🎤 Mikrofón")

LANG = "sk" if "Slovensky" in lang_choice else "en"

# ---------------------------
# 🔤 Texty
# ---------------------------
TEXTS = {
    "sk": {
        "app_title": "💰 Výdavkový denník / Výdajový deník",
        "subtitle": "CZK = vždy 1:1. Ostatné meny podľa denného kurzu ČNB.",
        "date": "📅 Dátum nákupu",
        "country": "🌍 Krajina + mena",
        "amount": "💵 Suma",
        "category": "📂 Kategória",
        "shop": "🏬 Obchod / miesto",
        "note": "📝 Poznámka",
        "save": "💾 Uložiť nákup",
        "list": "🧾 Zoznam nákupov",
        "summary": "📊 Súhrn mesačných výdavkov",
        "total": "Celkové výdavky",
        "rate_err": "❌ Kurz sa nepodarilo načítať.",
        "saved_ok": "Záznam uložený!",
        "rate_info": "Použitý kurz",
        "rate_from": "k",
        "export": "💾 Exportovať do CSV"
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
        "saved_ok": "Saved!",
        "rate_info": "Applied rate",
        "rate_from": "as of",
        "export": "💾 Export CSV"
    }
}

# ---------------------------
# 🚪 Otvorenie výťahu
# ---------------------------
st.markdown('<div class="lift-top"></div>', unsafe_allow_html=True)
st.markdown('<div class="lift-container">', unsafe_allow_html=True)

st.title(TEXTS[LANG]["app_title"])
st.caption(TEXTS[LANG]["subtitle"])

# ➕ Tu bude nasledovať FORMULÁR, ULOŽENIE, ČNB API, ZOZNAM, GRAFY...

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="lift-bottom"></div>', unsafe_allow_html=True)

# 📌 Pokračovanie pripravíme v ďalšom kroku...
