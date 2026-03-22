Dobře. Uděláme kvalitní README rovnou použitelné pro repo.

Níže máš hotový obsah — jen copy-paste do `README.md`.

---

# 📄 README.md

```markdown
# Cezar CSV → eshop-rychle

Aplikace pro převod CSV exportu dodavatele (Cezar) do importního formátu pro **eshop-rychle.cz**.

Součástí je polautomatický editor produktů s podporou:

- úpravy textů
- úpravy parametrů
- výběru kategorií
- automatického návrhu kategorií (learning systém)

---

## 🚀 Funkce

### 🔄 Workflow

```

CSV dodavatele
↓
automatické zpracování
↓
editace textů
↓
editace parametrů
↓
editace kategorií
↓
export CSV

```

---

### 🧠 Inteligentní kategorizace

Systém používá 3 vrstvy:

1. **LEARNING** – učí se z ručních úprav
2. **RULES** – pravidla podle názvu a parametrů
3. **DEFAULT** – fallback (Novinky)

---

### 📚 Learning systém

- ukládá vzory do JSON (`app/data/category_learning.json`)
- funguje na základě keywordů
- při opakovaném produktu automaticky doplní správnou kategorii

---

### 🛠 Editor

- stránkování (5 produktů)
- přehledná editace
- ✔ označení upravených kategorií
- debug info (LEARNING / RULES / DEFAULT)

---

## 🧱 Struktura projektu

```

eshop_app/

main.py

app/
├─ models/
│   └─ product.py
│
├─ services/
│   ├─ csv_parser.py
│   ├─ param_infer.py
│   ├─ category_infer.py
│   ├─ category_learning.py
│   └─ exporter.py
│
├─ templates/
│   ├─ edit_text.html
│   ├─ edit_params.html
│   ├─ edit_categories.html
│   └─ category_select.html
│
└─ data/
└─ category_learning.json

````

---

## ⚙️ Spuštění

### 1. Instalace

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn markdown
````

---

### 2. Spuštění

```bash
uvicorn main:app --reload
```

---

### 3. Otevři v prohlížeči

```
http://127.0.0.1:8000
```

---

## 📦 Export

Výstupní CSV je kompatibilní s:

```
eshop-rychle.cz
```

Podporuje:

* kategorie (| oddělené)
* parametry (`|-|` formát)
* cenové hladiny

---

## 🧠 Kategorie

Kategorie jsou definované v:

```python
CATEGORIES = {
    code: (name, parent)
}
```

a generuje se z nich strom pro UI.

---

## ⚠️ Omezení

* data jsou držena pouze v paměti (žádná DB)
* learning je jednoduchý (keyword match)
* neřeší pokročilou morfologii češtiny

---

## 🧩 Budoucí rozšíření

* lepší keyword matching (lemmatizace)
* váhování slov
* blacklist slov
* zvýraznění doporučených kategorií v UI

---

## 👤 Autor

Roman Kršňák

---

## 📄 Licence

Private / Internal use
