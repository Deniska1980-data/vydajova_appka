# 💸 Food Expenses App / Výdavkový denník

[▶️ Spustiť aplikáciu online](https://vydajovaappka-yumqiidaqwjyf5kcauxygh.streamlit.app/)  
*(GDPR-friendly: dáta ostávajú len lokálne v prehliadači.)*

---

## 🇬🇧 TL;DR (Short English summary)
Bilingual expense tracker (SK/CZ ↔ EN) built with **Streamlit**.  
- **RAG-driven AI agent “IssueCoin by Deny”**: friendly tips, seasonal/holiday messages, gentle nudges to fill missing fields.  
- **Currencies**: CZK base = 1:1; other currencies via **CNB daily rates** (with graceful fallback).  
- **Holidays & observances**: **Calendarific (aka Calendarium)** + curated fallback list; clean language switching (no mixing).  
- Charts, CSV export, categories, countries, and smart messages tailored to seasonality (Xmas, New Year, Easter, Black Friday, etc.).

---

## 🇸🇰/🇨🇿 Stručne
Bilingválna appka vo **Streamlite** na správu výdavkov.  
- **RAG agent „IssueCoin by Deny“**: priateľské tipy, sezónne/sviatočné hlášky, pripomenutie chýbajúcich polí (dátum, krajina, suma, obchod).  
- **Meny**: CZK = 1:1; ostatné z **denných kurzov ČNB** (s fallbackom).  
- **Sviatky & pamätné/cirkevné dni**: **Calendarific/Calendarium** + náš fallback zoznam; jazyk sa **nemieša**.  
- Graf výdavkov, export CSV, kategórie, krajiny, sviatočné „moods“ (Vianoce, Silvester, Veľká noc, Black Friday).

---

## 🌟 Funkcie / Features
- 🌐 **Bilingválna UI** (Slovensky/Česky ↔ English) – prepínač priamo v appke  
- 💱 **Kurzy mien z ČNB** (TXT endpoint) + automatický fallback na posledný platný kurz  
- 📅 **Sviatky a observances** z **Calendarific (Calendarium)** + vlastný fallback (SK, CZ, PL, DE, HU, …)  
- 🤖 **RAG AI agent – IssueCoin by Deny**  
  - upozorní na chýbajúce polia pred uložením (dátum, krajina, suma, shop)  
  - po uložení povie krátku, kontextovú hlášku k **aktuálnej kategórii** (nikdy „mimo tému“)  
  - sviatočné módy:  
    - **20–27 Dec** Vianočne ladené rady  
    - **29–31 Dec** Silvester & “wrap-up”  
    - **15–25 Nov** Black-Friday nákupy s rozvahou  
    - **Zelený štvrtok → Veľkonočný pondelok** láskavé veľkonočné hlášky  
- 📊 **Graf výdavkov** a **CSV export**  
- 🔐 **GDPR-friendly**: všetko **lokálne** v prehliadači (Session State)

---

## 🧠 Ako funguje RAG v appke
- **Retriever**: jednoduché pravidlá + drobná “znalosť” (kategórie, sezónne okná, mapa sviatkov)  
- **Augmentácia**: k udalosti (dátum+krajina+kategória) priložíme kontext (či je sviatok, aká sezóna, koľko sa už v kategórii minulo vs. prah).  
- **Generovanie**: IssueCoin vyberie vhodný, **neútočný** a **k veci** tip/pochvalu; v SK/CZ alebo EN podľa UI.  
- **Bez miešania jazykov**: preklady sviatkov sú kurátorsky udržiavané (napr. *Maundy Thursday → Zelený štvrtok*, *Easter Monday → Veľkonočný pondelok*).

---

## 🔌 Integrované API
- **ČNB Daily FX** – `denni_kurz.txt` (+ `?date=DD.MM.YYYY`)  
  Žiadny API kľúč netreba; parsujeme TXT a držíme fallback na posledný známy kurz.  
- **Calendarific (Calendarium)** – sviatky, pamätné a cirkevné dni  
  - požaduje **API key**  
  - vybrané sviatky pre SK/CZ sú **preložené**; medzinárodné cirkevné/regionálne nechávame **v origináli**, aby nevznikali zvláštne preklady  
  - ak API nevráti nič, použijeme vlastný **fallback** (SK, CZ, PL, DE, HU, GB…)

**🔒 Súkromie**

Žiadny backend, žiadna databáza.
Údaje o výdavkoch žijú len vo vašom prehliadači (Streamlit Session State).

**🗺️ Roadmap**

Mobilné “add-purchase” mikro-UI
Týždenné/mesačné rozpočty a prehľady
Viac krajín/sviatkových fallbackov
Viac “RAG nápovedy” pre rozumné znižovanie výdavkov

**👩‍💻 Autor & agent**

Deny – návrh a implementácia
IssueCoin by Deny – priateľský AI agent s RAG, ktorý dohliada na sviatky a dobré návyky

**📸 Screenshots**

![RAG – prehľad](/obrazky_vytah_appka/RAG_obrazek1.JPG)


![IssueCoin – správny obrázok](/obrazky_vytah_appka/spravny_obrazek1.JPG)


## License
MIT — see [LICENSE](LICENSE) for details.

## 🛠️ Lokálne spustenie (voliteľné)
<details>
<summary>Klikni pre návod</summary>

**Požiadavky:** Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py        # alebo test_vydajova_appka_app.py

# .streamlit/secrets.toml
CAL_API_KEY = "tvoj_calendarific_api_key"


