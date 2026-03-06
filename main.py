from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import csv
import io
import os
import re
from datetime import datetime
import markdown  # ← přidáno pro převod Markdown → HTML

# --- soubor s hlavičkou eshop-rychle (161 sloupců) ---
TEMPLATE_PATH = "eshop_template.csv"

# --- Cezar vstupní sloupce ---
CEZAR_KOD = "Cislo_Pods"
CEZAR_NAZEV = "Nazevzbozi"
CEZAR_ZAKLADNI = "PC_AsDPH"
CEZAR_NASE = "PC_BsDPH"
CEZAR_MNOZSTVI = "Mnozstvi"
CEZAR_EAN = "Carkod"
CEZAR_POPIS = "Textpoznam"

CEZAR_POPIS_PRIMARY_FULL = "Textpoznam,C74,214"

# --- pevné hodnoty (v1) ---
CONST_KATEGORIE = "16-0-0-0"
CONST_NOVINKA = "1"
CONST_UVOD = "1"
CONST_DISKUZE = "1"
CONST_DPH = "1"

PARAM_KEYS = ["Výrobce", "Příležitost", "Druh", "Materiál", "Barva", "Provedení", "Tvar"]

PARAM_OPTIONS = {
    "Výrobce": ["miš"],
    "Příležitost": ["celoroční", "dušičky", "jaro", "valentýn", "vánoce", "velikonoce"],
    "Druh": [
        "bodec", "cedule", "konvička", "koš", "koš dárkový", "kužel", "lucerna", "miska",
        "obal na květináč", "ostatní", "přízdoba", "srdce", "tác", "truhlík",
        "umělá rostlina", "věnec"
    ],
    "Materiál": [
        "břidlice", "dřevěné", "filc", "keramické", "kovové", "melamin", "mikro plyš",
        "ostatní", "plastové", "plyš", "polyresin", "polyston", "polystyrenové",
        "porcelán", "přírodní", "proutěné", "skleněné", "sklo", "textil",
        "dýha"
    ],
    "Barva": [
        "antracit", "béžová", "bílá", "bílohnědá", "bílohnědý", "bordó", "černá",
        "červená", "čirá", "fialková", "fialová", "hnědá", "hnědobílá", "hnědožlutá",
        "krémová", "lila", "lososová", "mix", "modrá", "naturál", "okrová", "oranžová",
        "perleťová", "přírodní", "růžová", "růžová světlá", "růžovofialová",
        "růžovozelená", "šampaň", "šedá", "starorůžová", "stříbrná", "zelená",
        "zelenorůžová", "zlatá", "žlutá"
    ],
    "Provedení": ["bez ucha", "kolíček", "přírodní", "s uchem", "stolní", "zápich", "závěsný"],
    "Tvar": [
        "anděl", "diamant", "domečky", "figurky", "hnízdo", "hranatý", "husa", "hvězda",
        "kapka", "kočka", "koule", "kulatý", "kužel", "mix", "motýl", "oliva",
        "ostatní", "oválný", "ovečka", "plot", "ptáček", "raketa", "rampouch",
        "šiška", "slepička",
        "špice", "srdce", "vajíčko", "větvičky", "volné tvary", "zajíc", "žalud", "zvonek"
    ]
}

app = FastAPI()
GENERATED_PRODUCTS = []

# -------------------------
# Helper funkce
# -------------------------

def load_eshop_header():
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f'Chybí "{TEMPLATE_PATH}" ve stejné složce jako main.py')

    with open(TEMPLATE_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)

    if not header:
        raise ValueError("eshop_template.csv nemá hlavičku")

    return [str(h).strip() for h in header]


def decode_csv_bytes(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1250")


def clean_cezar_header(raw_header):
    return [str(h).strip().split(",")[0].strip() for h in raw_header]


def format_price(v):
    if v is None:
        return ""
    s = str(v).strip()
    if s == "":
        return ""
    try:
        num = float(s.replace(",", "."))
        return f"{num:.2f}"
    except:
        return ""


def format_stock(v):
    if v is None:
        return "0"
    s = str(v).strip()
    if s == "":
        return "0"
    try:
        num = float(s.replace(",", "."))
        return str(int(num))
    except:
        return "0"


def normalize(text):
    return str(text or "").lower()


def norm_header(s: str) -> str:
    return " ".join(str(s or "").strip().lower().split())

# -------------------------
# Infer funkce
# -------------------------

def infer_barva(text: str) -> str:
    t = normalize(text)
    if "mix" in t:
        return "mix"
    rules = [
        ("růžovozelen", "růžovozelená"),
        ("růžovofial", "růžovofialová"),
        ("zelenorůž", "zelenorůžová"),
        ("bílohněd", "bílohnědá"),
        ("hnědobíl", "hnědobílá"),
        ("hnědožlut", "hnědožlutá"),
        ("starorůž", "starorůžová"),
        ("růžová světl", "růžová světlá"),
        ("šampaň", "šampaň"),
        ("perleť", "perleťová"),
        ("bord", "bordó"),
        ("antracit", "antracit"),
        ("béž", "béžová"),
        ("krém", "krémová"),
        ("čern", "černá"),
        ("bíl", "bílá"),
        ("šed", "šedá"),
        ("stříbr", "stříbrná"),
        ("zlat", "zlatá"),
        ("červen", "červená"),
        ("modr", "modrá"),
        ("zelen", "zelená"),
        ("žlut", "žlutá"),
        ("oranž", "oranžová"),
        ("fialkov", "fialková"),
        ("fial", "fialová"),
        ("lila", "lila"),
        ("losos", "lososová"),
        ("hněd", "hnědá"),
        ("okrov", "okrová"),
        ("natur", "naturál"),
        ("přírod", "přírodní"),
        ("čir", "čirá"),
    ]
    for needle, val in rules:
        if needle in t:
            return val
    return ""


def infer_material(text: str) -> str:
    t = normalize(text)
    if "dýh" in t:
        return "dýha"
    rules = [
        ("polyresin", "polyresin"),
        ("polyston", "polyston"),
        ("polystyren", "polystyrenové"),
        ("mikro plyš", "mikro plyš"),
        ("mikroplyš", "mikro plyš"),
        ("plyš", "plyš"),
        ("melamin", "melamin"),
        ("porcel", "porcelán"),
        ("keramik", "keramické"),
        ("sklen", "skleněné"),
        ("sklo", "sklo"),
        ("plech", "kovové"),
        ("drát", "kovové"),
        ("drat", "kovové"),
        ("kovov", "kovové"),
        ("břidlic", "břidlice"),
        ("filc", "filc"),
        ("prout", "proutěné"),
        ("dřevo", "dřevěné"),
        ("dřev", "dřevěné"),
        ("plast", "plastové"),
        ("přírod", "přírodní"),
        ("textil", "textil"),
        ("látk", "textil"),
    ]
    for needle, val in rules:
        if needle in t:
            return val
    if re.search(r"\bkov\b", t):
        return "kovové"
    return ""


def infer_tvar(text: str) -> str:
    t = normalize(text)
    if "ovál" in t:
        return "oválný"
    rules = [
        ("větvičk", "větvičky"),
        ("větev", "větvičky"),
        ("srdc", "srdce"),
        ("anděl", "anděl"),
        ("andilek", "anděl"),
        ("hvězd", "hvězda"),
        ("hnízd", "hnízdo"),
        ("domečk", "domečky"),
        ("figur", "figurky"),
        ("motýl", "motýl"),
        ("ptáč", "ptáček"),
        ("ptak", "ptáček"),
        ("zají", "zajíc"),
        ("ovečk", "ovečka"),
        ("husa", "husa"),
        ("kočk", "kočka"),
        ("žalud", "žalud"),
        ("šišk", "šiška"),
        ("vají", "vajíčko"),
        ("zvonek", "zvonek"),
        ("rampouch", "rampouch"),
        ("diamant", "diamant"),
        ("kapk", "kapka"),
        ("koule", "koule"),
        ("kulat", "kulatý"),
        ("hranat", "hranatý"),
        ("ováln", "oválný"),
        ("kužel", "kužel"),
        ("oliv", "oliva"),
        ("raket", "raketa"),
        ("plot", "plot"),
        ("špic", "špice"),
        ("mix", "mix"),
    ]
    for needle, val in rules:
        if needle in t:
            return val
    return ""


def infer_parametry(text: str) -> dict:
    t = normalize(text)
    if ("košík" in t) or ("kosik" in t) or ("koš" in t):
        druh = "koš"
    elif "květ" in t or "rostlin" in t:
        druh = "umělá rostlina"
    else:
        druh = "ostatní"

    if "váno" in t:
        prilezitost = "vánoce"
    elif "velikonoc" in t:
        prilezitost = "velikonoce"
    elif "valent" in t:
        prilezitost = "valentýn"
    elif "duš" in t:
        prilezitost = "dušičky"
    elif "jaro" in t:
        prilezitost = "jaro"
    else:
        prilezitost = "celoroční"

    barva = infer_barva(text)
    material = infer_material(text)
    tvar = infer_tvar(text)

    provedeni = "stolní"

    if druh == "umělá rostlina":
        if not material:
            material = "plastové"
        provedeni = "zápich"
        if not tvar:
            tvar = "větvičky"

    return {
        "Výrobce": "miš",
        "Příležitost": prilezitost,
        "Druh": druh,
        "Materiál": material,
        "Barva": barva,
        "Provedení": provedeni,
        "Tvar": tvar,
    }


def format_parametry_string(params: dict) -> str:
    parts = []
    for k in PARAM_KEYS:
        v = str(params.get(k, "") or "").strip().lower()
        parts.append(f"{k}#-#{v}")
    return "|-|".join(parts)


CATEGORY_TREE = [
    {"name": "Novinky", "id": "16-0-0-0", "children": []},
    {"name": "Aranžmá, dekorace", "id": "17-0-0-0", "children": []},
    {"name": "Výrobky chráněné dílny", "id": "26-0-0-0", "children": [
        {"name": "Výrobky ze dřeva", "id": "26-147-0-0"},
        {"name": "Výrobky z látky", "id": "26-148-0-0"},
        {"name": "Výrobky z proutí", "id": "26-149-0-0"},
        {"name": "Aranžování, dekorace", "id": "26-150-0-0"},
    ]},
    {"name": "Floristické potřeby", "id": "3-0-0-0", "children": [
        {"name": "Aranžérské pomůcky", "id": "3-5-0-0"},
        {"name": "Stuhy, fólie, provazy, juta", "id": "3-3-0-0"},
        {"name": "Věnce, dekorační základy", "id": "3-58-0-0"},
        {"name": "Materiál pro dekorace", "id": "3-59-0-0"},
        {"name": "Tašky, boxy", "id": "3-146-0-0"},
    ]},
    {"name": "Umělé a sušené květiny", "id": "8-0-0-0", "children": [
        {"name": "Exotika bez stopky", "id": "8-14-0-0"},
        {"name": "Exotika na stopce", "id": "8-21-0-0"},
        {"name": "Dekorace do vázy", "id": "8-23-0-0"},
        {"name": "Umělé květiny", "id": "8-16-0-0"},
        {"name": "Umělé dekorace, vazby, aranže", "id": "8-53-0-0"},
    ]},
    {"name": "Koše a košíky", "id": "19-0-0-0", "children": [
        {"name": "proutěné", "id": "19-61-0-0"},
        {"name": "dřevěné", "id": "19-62-0-0"},
        {"name": "ostatní", "id": "19-151-0-0"},
    ]},
    {"name": "Obaly na květináče, truhlíky", "id": "20-0-0-0", "children": [
        {"name": "dřevěné", "id": "20-69-0-0"},
        {"name": "proutěné", "id": "20-70-0-0"},
        {"name": "plechové", "id": "20-73-0-0"},
        {"name": "keramické", "id": "20-74-0-0"},
        {"name": "misky", "id": "20-75-0-0"},
        {"name": "plastové", "id": "20-68-0-0"},
        {"name": "ostatní", "id": "20-76-0-0"},
    ]},
    {"name": "Bytové dekorace", "id": "21-0-0-0", "children": [
        {"name": "proutěné", "id": "21-77-0-0"},
        {"name": "dřevěné", "id": "21-78-0-0"},
        {"name": "látkové", "id": "21-81-0-0"},
        {"name": "plechové", "id": "21-83-0-0"},
        {"name": "keramické", "id": "21-84-0-0"},
        {"name": "svíčky", "id": "21-133-0-0"},
        {"name": "ostatní", "id": "21-85-0-0"},
    ]},
    {"name": "Sezónní dekorace", "id": "22-0-0-0", "children": [
        {"name": "Valentýn, svatba", "id": "22-86-0-0"},
        {"name": "Jarní dekorace", "id": "22-87-0-0"},
        {"name": "Velikonoční dekorace", "id": "22-88-0-0"},
        {"name": "Podzimní dekorace", "id": "22-89-0-0"},
        {"name": "Dušičky", "id": "22-90-0-0"},
        {"name": "Vánoce a Advent", "id": "22-134-0-0"},
    ]},
    {"name": "Dům a zahrada", "id": "24-0-0-0", "children": [
        {"name": "Zahradní doplňky", "id": "24-109-0-0"},
        {"name": "Ostatní", "id": "24-110-0-0"},
    ]},
    {"name": "Výprodej", "id": "6-0-0-0", "children": []},
]


# -------------------------
# ROUTES
# -------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
    <head><meta charset="utf-8"><title>Cezar → Eshop</title></head>
    <body style="font-family:sans-serif;max-width:1200px;margin:40px auto;">
      <h2>Cezar → Editace parametrů → Editace textů → Export</h2>
      <form action="/convert" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".csv" required>
        <button type="submit">Načíst produkty</button>
      </form>
    </body>
    </html>
    """


@app.post("/convert", response_class=HTMLResponse)
async def convert(file: UploadFile = File(...)):
    global GENERATED_PRODUCTS
    GENERATED_PRODUCTS = []

    _ = load_eshop_header()

    content = await file.read()
    decoded = decode_csv_bytes(content)

    rows = list(csv.reader(io.StringIO(decoded), delimiter=";"))
    if len(rows) < 2:
        return HTMLResponse("Vstupní CSV je prázdné.", status_code=400)

    raw_header_full = [str(h).strip() for h in rows[0]]
    header_clean = clean_cezar_header(raw_header_full)
    data = rows[1:]

    idx_first = {}
    for i, name in enumerate(header_clean):
        if name not in idx_first:
            idx_first[name] = i

    required = [CEZAR_KOD, CEZAR_NAZEV, CEZAR_ZAKLADNI, CEZAR_NASE, CEZAR_MNOZSTVI]
    missing = [c for c in required if c not in idx_first]
    if missing:
        return HTMLResponse(f"Chybí sloupce ve vstupu: {', '.join(missing)}", status_code=400)

    textpoznam_indices = [
        i for i, h in enumerate(raw_header_full)
        if norm_header(h).startswith(norm_header(CEZAR_POPIS + ","))
    ]

    primary_textpoznam_index = None
    for i, h in enumerate(raw_header_full):
        if norm_header(h) == norm_header(CEZAR_POPIS_PRIMARY_FULL):
            primary_textpoznam_index = i
            break

    for r in data:
        kod = r[idx_first[CEZAR_KOD]].strip() if idx_first[CEZAR_KOD] < len(r) else ""
        if not kod:
            continue

        nazev = r[idx_first[CEZAR_NAZEV]].strip() if idx_first[CEZAR_NAZEV] < len(r) else ""

        popis = ""
        if primary_textpoznam_index is not None and primary_textpoznam_index < len(r):
            v = r[primary_textpoznam_index].strip()
            if v:
                popis = v

        if not popis:
            for i in textpoznam_indices:
                if i < len(r):
                    v = r[i].strip()
                    if v:
                        popis = v
                        break

        ean = r[idx_first[CEZAR_EAN]].strip() if CEZAR_EAN in idx_first and idx_first[CEZAR_EAN] < len(r) else ""
        zakladni = format_price(r[idx_first[CEZAR_ZAKLADNI]])
        nase = format_price(r[idx_first[CEZAR_NASE]])
        stock = format_stock(r[idx_first[CEZAR_MNOZSTVI]])

        je_skladem = "1" if int(stock) > 0 else "0"
        cenove_hladiny = f"velkoobchod#-#{zakladni}" if zakladni else ""

        params = infer_parametry(f"{nazev} {popis}")

        GENERATED_PRODUCTS.append({
            "kod": kod,
            "nazev": nazev,
            "ean": ean,
            "popis": popis,
            "zakladni": zakladni,
            "nase": nase,
            "stock": stock,
            "je_skladem": je_skladem,
            "kategorie": CONST_KATEGORIE,
            "novinka": CONST_NOVINKA,
            "uvod": CONST_UVOD,
            "diskuze": CONST_DISKUZE,
            "dph": CONST_DPH,
            "cenove_hladiny": cenove_hladiny,
            "params": params,
        })

    html = """
    <html>
    <head><meta charset="utf-8"><title>Editace parametrů</title></head>
    <body style="font-family:sans-serif;max-width:1600px;margin:40px auto;">
      <h2>Editace parametrů</h2>
      <form method="post" action="/edit-text">
        <table border="1" cellpadding="6" cellspacing="0">
          <tr>
            <th>Kód</th>
            <th>Název</th>
    """

    for key in PARAM_KEYS:
        html += f"<th>{key}</th>"
    html += "</tr>"

    for i, p in enumerate(GENERATED_PRODUCTS):
        html += "<tr>"
        html += f"<td>{p['kod']}</td>"
        html += f"<td>{p['nazev']}</td>"

        for key in PARAM_KEYS:
            options = PARAM_OPTIONS.get(key, [])
            current = (p["params"].get(key, "") or "").strip().lower()

            html += f"<td><select name='{key}_{i}'>"
            if current and current not in options:
                html += f"<option selected>{current}</option>"
            for option in options:
                selected = "selected" if option == current else ""
                html += f"<option {selected}>{option}</option>"
            html += "</select></td>"

        html += "</tr>"

    html += """
        </table>
        <br>
        <button type="submit">Pokračovat na editaci názvů a popisů</button>
      </form>
    </body>
    </html>
    """
    return html


@app.post("/edit-text", response_class=HTMLResponse)
async def edit_text(request: Request):
    global GENERATED_PRODUCTS

    form = await request.form()

    for i, p in enumerate(GENERATED_PRODUCTS):
        for key in PARAM_KEYS:
            field = f"{key}_{i}"
            if field in form:
                p["params"][key] = str(form[field]).strip().lower()

        if (p["params"].get("Druh", "") or "").strip().lower() == "umělá rostlina":
            if not (p["params"].get("Materiál", "") or "").strip():
                p["params"]["Materiál"] = "plastové"
            if not (p["params"].get("Provedení", "") or "").strip():
                p["params"]["Provedení"] = "zápich"
            if not (p["params"].get("Tvar", "") or "").strip():
                p["params"]["Tvar"] = "větvičky"

    html = """
    <html>
    <head><meta charset="utf-8"><title>Editace textů</title></head>
    <body style="font-family:sans-serif;max-width:1600px;margin:40px auto;">
      <h2>Editace názvů a HTML popisů (podporuje Markdown)</h2>
      <form method="post" action="/edit-categories">
        <table border="1" cellpadding="6" cellspacing="0">
          <tr>
            <th>Kód</th>
            <th>Název</th>
            <th>Popis (Markdown)</th>
          </tr>
    """

    for i, p in enumerate(GENERATED_PRODUCTS):
        html += f"""
        <tr>
          <td>{p['kod']}</td>
          <td><input type="text" name="name_{i}" value="{p['nazev']}" style="width:400px;"></td>
          <td><textarea name="desc_{i}" rows="8" style="width:700px;">{p['popis']}</textarea></td>
        </tr>
        """

    html += """
        </table>
        <br>
        <button type="submit">Exportovat finální CSV</button>
      </form>
    </body>
    </html>
    """

    return html


@app.post("/edit-categories", response_class=HTMLResponse)
async def edit_categories(request: Request):
    global GENERATED_PRODUCTS

    form = await request.form()

    for i, p in enumerate(GENERATED_PRODUCTS):
        name_field = f"name_{i}"
        desc_field = f"desc_{i}"

        if name_field in form:
            p["nazev"] = str(form[name_field])
        if desc_field in form:
            p["popis"] = str(form[desc_field])

    html = """
    <html>
    <head><meta charset="utf-8"><title>Editace kategorií</title></head>
    <body style="font-family:sans-serif;max-width:1200px;margin:40px auto;">
      <h2>Editace kategorií</h2>
    """

    for p in GENERATED_PRODUCTS:
        html += f"""
      <p>
        Produkt: {p['kod']} – {p['nazev']}<br>
        Navržené kategorie: {p['kategorie_auto']}
      </p>
        """

    html += """
      <form method="post" action="/export">
        <button type="submit">Pokračovat na export</button>
      </form>
    </body>
    </html>
    """

    return html


@app.post("/export")
async def export(request: Request):
    global GENERATED_PRODUCTS

    if not GENERATED_PRODUCTS:
        return HTMLResponse("Nejdřív nahraj CSV přes /convert.", status_code=400)

    form = await request.form()

    out_header = load_eshop_header()
    out_index = {name: i for i, name in enumerate(out_header)}

    def setv(row, colname, value):
        if colname in out_index:
            row[out_index[colname]] = value

    output_rows = []
    for i, p in enumerate(GENERATED_PRODUCTS):
        row = [""] * len(out_header)

        final_name = form.get(f"name_{i}", p["nazev"])
        raw_desc = form.get(f"desc_{i}", p["popis"])

        # Markdown → HTML převod
        final_desc = markdown.markdown(raw_desc)

        setv(row, "Kod vyrobku", p["kod"])
        setv(row, "Nazev vyrobku", final_name)
        setv(row, "EAN kod", p["ean"])
        setv(row, "Popis vyrobku", final_desc)

        setv(row, "Zakladni cena", p["zakladni"])
        setv(row, "Nase cena", p["nase"])

        setv(row, "Skladem (pocet kusu)", p["stock"])
        setv(row, "Je skladem (1|0)", p["je_skladem"])

        setv(row, "Novinka (1|0)", p["novinka"])
        setv(row, "Umistit na uvod (1|0)", p["uvod"])
        setv(row, "Povolit diskuzi (1|0)", p["diskuze"])
        setv(row, "DPH (1|2|3|4|5)", p["dph"])

        setv(row, "Zarazeni do kategorie (oddelujte znakem \"|\")", p["kategorie"])
        setv(row, "Cenove hladiny", p["cenove_hladiny"])
        setv(row, "Parametry", format_parametry_string(p["params"]))

        output_rows.append(row)

    out_io = io.StringIO(newline="")
    writer = csv.writer(out_io, delimiter=";", lineterminator="\r\n")
    writer.writerow(out_header)
    writer.writerows(output_rows)
    out_io.seek(0)

    filename = f"ESHOP_IMPORT_EXPORT_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"

    return StreamingResponse(
        out_io,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
