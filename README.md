# 💰 Výdavkový denník / Výdajový deník — s AI agentom IssueCoin

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Google%20Cloud%20Run-blue)](https://vydajova-appka-84817292369.europe-central2.run.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Bilingválny výdavkový denník (SK/CZ + EN) v **Streamlite s AI agentom IssueCoin**. Aplikácia využíva **RAG (Retrieval-Augmented Generation)** 
nad lokálnymi znalosťami + 2 externé **API** (ČNB – denné kurzy, Calendarific – sviatky), má sezónne hlášky, a beží GDPR-friendly
(dáta ostávajú lokálne v session).
Celá aplikácia je plne kontajnerizovaná pomocou **Dockeru** a nasadená na **Google Cloud Run** ako serverless služba s automatickým škálovaním.

<p align="center">
  <a href="https://vydajova-appka-84817292369.europe-central2.run.app/">
    <img
      src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=https%3A%2F%2Fvydajova-appka-84817292369.europe-central2.run.app%2F"
      alt="QR – otvor aplikáciu"
      width="220" height="220"
    />
  </a>
</p>

---

![IssueCoin – sviatočné hlášky a úspešné uloženie záznamu](obrazky_vytah_appka/spravny_obrazek1.JPG)

![IssueCoin – sviatočné hlášky]


## ✨ Funkcie

- **Bilingválna appka**: prepínač *Slovensky/Česky* ↔ *English* (texty sú oddelené, nemiešajú sa).
- **Meny**: všetko sa prepočítava do CZK (CZK=1:1), ostatné meny podľa **denných kurzov ČNB** (s fallbackom na posledný dostupný kurz).
- **Sviatky**: **Calendarific** (public holiday vs. observance), pre SK/CZ vlastné preklady + lokálny fallback.
- **AI agent IssueCoin**:
  - pred uložením upozorní na chýbajúce polia (dátum, suma, obchod…),
  - po uložení dá krátku, priateľskú spätnú väzbu k **danej kategórii** (bez „mimo témy“),
  - upozorní na **graf** nižšie a zhrnie **dnešný súčet a počet nákupov**.
- **Sezónne okná** (špeciálny tón hlášok):  
  Vianoce **20.–27.12.**, Silvester **29.–31.12.**, januárové výpredaje, **Black Friday 15.–25.11.**, **Veľká noc: Zelený štvrtok (Maundy Thursday) → Veľkonočný pondelok (Easter Monday)**.
- **Prehľad**: Altair stĺpcový graf podľa kategórií + **CSV export**.  
- **GDPR-friendly**: bez serverového úložiska; dáta ostávajú u používateľa (session).

---

## 🧠 RAG – pragmaticky


![Ako funguje RAG](obrazky_vytah_appka/RAG_obrazek1.JPG)

![IssueCoin – upozorňuje na doplnenie údajov]

- **Retrieval**: fakty beriem z lokálnej znalostnej bázy (kategórie, prahy, sezónne okná), z **ČNB** a **Calendarific** (s fallback tabuľkou).
- **Augmentation**: poskladám kontext (jazyk, dátum, krajina, kategória, sviatok/sezóna).
- **Generation**: krátke, ľudské hlášky IssueCoin-a – k veci, bez miešania tém, vždy slušné a neútočné.

Tento prístup je rýchly, stabilný a predvídateľný pre produkčné UI.

---
## API

| Služba | Na čo slúži | Poznámky |
|---|---|---|
| **Česká národná banka (ČNB)** | Denné textové kurzy | Použije sa kurz k zvolenému dátumu; ak chýba, vezme sa **posledný dostupný**. Všetko sa konvertuje do **CZK (CZK=1:1)**. |
| **Calendarific** | Štátne sviatky + observances | Rozlišujem **public holiday** vs. **observance/religious**. Pre SK/CZ mapujem známe sviatky (preklad), ak API nič nevráti, mám **lokálny fallback**. |

> API kľúč pre Calendarific je uložený v `st.secrets`.
> 
##Stručná architektúra

- UI (Streamlit) – i18n slovníky (SK/CZ + EN)
- IssueCoin – pravidlá + RAG kontext (kategórie, prahy, sviatky, sezónne okná)
- Kurzy ČNB – requests + cache (@st.cache_data, ~10 min)
- Calendarific – requests + cache (~60 min), + lokálna fallback tabuľka pre vybrané krajiny
- Graf & export – Altair (sumy podľa kategórie) + CSV download

---
**Tech: Streamlit · Python · pandas · Altair · requests · RAG (lokálne dáta + API: ČNB, Calendarific)· Docker · Google Cloud**

**☁️ Docker & Google Cloud Deployment**

Aplikácia Výdavkový denník / Výdajový deník je plne kontajnerizovaná pomocou Dockeru a beží na Google Cloud Run.
Nižšie je postup, ako bola zabalená a nasadená 

🐳 1️⃣ **Vytvorenie Docker image**

*V koreňovom adresári projektu je súbor Dockerfile*:

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "test_vydajova_appka_app.py", "--server.port=8080", "--server.address=0.0.0.0"]

**Build Docker image lokálne**:
docker build -t vydajova_appka .
**Spustenie kontajnera**:
docker run -p 8501:8080 vydajova_appka
**Aplikácia bude dostupná na**:
http://0.0.0.0:8080

☁️ 2️⃣ **Nasadenie na Google Cloud Run**
a) Nahratie image do Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/vydajova_appka
(nahrať svoj Docker image do cloudu)

b) Spustenie služby na Cloud Run
gcloud run deploy vydajova-appka \
  --image gcr.io/PROJECT_ID/vydajova_appka \
  --platform managed \
  --region europe-central2 \
  --allow-unauthenticated

**Google Cloud automaticky**:
vytvorí serverless inštanciu kontajnera,
priradí HTTPS adresu,
škáluje podľa dopytu (platíš len, keď appka beží)

🧰 Použité služby

| Komponent                           | Účel                        | Poznámka                       |
| ----------------------------------- | --------------------------- | ------------------------------ |
| **Docker**                          | Kontajnerizácia aplikácie   | Izolované, prenosné prostredie |
| **Google Cloud Build**              | Build Docker image v cloude | Vytvára a ukladá image do GCR  |
| **Google Cloud Run**                | Serverless hosting          | Automatické škálovanie, HTTPS  |
| **Google Container Registry (GCR)** | Ukladanie Docker image      | Centrálne úložisko image-ov    |

---
##Licencia
Projekt je pod licenciou MIT [LICENSE](LICENSE)
---

<details>
<summary>Konfigurácia kľúča (skryté)</summary>

```toml
# .streamlit/secrets.toml
CAL_API_KEY = "tvoj_calendarific_api_key"

---

## 🖥️ Lokálne spustenie

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run test_vydajova_appka_app.py
CAL_API_KEY = "tvoj_calendarific_api_key"
