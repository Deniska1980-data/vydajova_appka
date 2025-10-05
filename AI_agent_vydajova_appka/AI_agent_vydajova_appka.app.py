import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime, date as dt_date

st.set_page_config(page_title="Expense Diary", layout="wide")

# ---------------------------
# Custom CSS for readability + VÝŤAH
# ---------------------------
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 16px;
        line-height: 1.6;
        background-color: #f7f7f7;
    }
    h1 { font-size: 28px !important; }
    h2 { font-size: 24px !important; }
    h3 { font-size: 20px !important; }
    .stButton>button {
        font-size: 18px;
        padding: 10px 20px;
    }
    .stSelectbox>div>div {
        font-size: 16px;
    }
    .elevator-frame {
        border: 6px solid #888;
        border-radius: 16px;
        padding: 30px 20px;
        margin: 30px auto;
        max-width: 1000px;
        background-color: white;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='elevator-frame'>", unsafe_allow_html=True)

    # ---------------------------
    # Jazyk + Mikrofón prepínač
    # ---------------------------
    lang_col, mic_col = st.columns([7, 3])
    with lang_col:
        lang_choice = st.selectbox("🌐 Language / Jazyk", ["Slovensky / Česky", "English"], index=0)
    with mic_col:
        mic_enabled = st.toggle("🎙️ Mikrofón", value=False)
    LANG = "sk" if "Slovensky" in lang_choice else "en"

    # ---------------------------
    # Základné vstupy appky
    # ---------------------------
    st.header("Zadaj svoj výdavok")
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("📅 Dátum / Date", value=dt_date.today())
        country = st.selectbox("🌍 Krajina / Country", [
            "Česko – CZK", "Slovensko – EUR", "USA – USD", "Maďarsko – HUF", "Poľsko – PLN"
        ])
    with col2:
        amount = st.number_input("💵 Suma / Amount", min_value=0.0, step=1.0)
        category = st.selectbox("📂 Kategória / Category", [
            "Potraviny 🛒", "Zábava 🎉", "Drogéria 🧴", "Elektronika 💻"
        ])

    # Na konci uzavrieme výťahový rám:
    st.markdown("</div>", unsafe_allow_html=True)
