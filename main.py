from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

import csv
import io
import os
from datetime import datetime
import markdown

from app.services.param_infer import infer_parametry
from app.services.csv_parser import decode_csv_bytes
from app.services.exporter import format_price, format_stock
from app.models.product import ProductDraft


app = FastAPI()

GENERATED_PRODUCTS = []


templates = Jinja2Templates(directory="app/templates")

TEMPLATE_PATH = "eshop_template.csv"

CEZAR_KOD = "Cislo_Pods"
CEZAR_NAZEV = "Nazevzbozi"
CEZAR_ZAKLADNI = "PC_AsDPH"
CEZAR_NASE = "PC_BsDPH"
CEZAR_MNOZSTVI = "Mnozstvi"
CEZAR_EAN = "Carkod"
CEZAR_POPIS = "Textpoznam"

CEZAR_POPIS_PRIMARY_FULL = "Textpoznam,C74,214"

CONST_KATEGORIE = "16-0-0-0"
CONST_NOVINKA = "1"
CONST_UVOD = "1"
CONST_DISKUZE = "1"
CONST_DPH = "1"

PARAM_KEYS = ["Výrobce","Příležitost","Druh","Materiál","Barva","Provedení","Tvar"]

PAGE_SIZE = 5

PARAM_OPTIONS = {
    "Výrobce": ["miš"],
    "Příležitost": ["celoroční","dušičky","jaro","valentýn","vánoce","velikonoce"],
    "Druh": ["bodec","cedule","konvička","koš","koš dárkový","kužel","lucerna","miska",
             "obal na květináč","ostatní","přízdoba","srdce","tác","truhlík",
             "umělá rostlina","věnec"],
    "Materiál": ["břidlice","dřevěné","filc","keramické","kovové","melamin","mikro plyš",
                 "ostatní","plastové","plyš","polyresin","polyston","polystyrenové",
                 "porcelán","přírodní","proutěné","skleněné","sklo","textil","dýha"],
    "Barva": ["antracit","béžová","bílá","bordó","černá","červená","čirá","fialová",
              "hnědá","krémová","mix","modrá","naturál","okrová","oranžová",
              "růžová","šedá","stříbrná","zelená","zlatá","žlutá"],
    "Provedení": ["bez ucha","kolíček","přírodní","s uchem","stolní","zápich","závěsný"],
    "Tvar": ["anděl","diamant","domečky","figurky","hnízdo","hranatý","hvězda",
             "kapka","kočka","koule","kulatý","kužel","mix","motýl","oliva",
             "ostatní","oválný","ptáček","raketa","rampouch","šiška","slepička",
             "srdce","vajíčko","větvičky","volné tvary","zajíc","žalud","zvonek"]
}
CATEGORIES = {
"16-0-0-0":("Novinky",None),
"17-0-0-0":("Aranžmá, dekorace",None),
"6-0-0-0":("Výprodej",None),

"26-0-0-0":("Výrobky chráněné dílny",None),
"26-147-0-0":("Výrobky ze dřeva","26-0-0-0"),
"26-148-0-0":("Výrobky z látky","26-0-0-0"),
"26-149-0-0":("Výrobky z proutí","26-0-0-0"),
"26-150-0-0":("Aranžování, dekorace","26-0-0-0"),

"3-0-0-0":("Floristické potřeby",None),
"3-5-0-0":("Aranžérské pomůcky","3-0-0-0"),
"3-3-0-0":("Stuhy, fólie, provazy, juta","3-0-0-0"),
"3-58-0-0":("Věnce, dekorační základy","3-0-0-0"),
"3-59-0-0":("Materiál pro dekorace","3-0-0-0"),
"3-146-0-0":("Tašky, boxy","3-0-0-0"),

"8-0-0-0":("Umělé a sušené květiny",None),
"8-14-0-0":("Exotika bez stopky","8-0-0-0"),
"8-21-0-0":("Exotika na stopce","8-0-0-0"),
"8-23-0-0":("Dekorace do vázy","8-0-0-0"),
"8-16-0-0":("Umělé květiny","8-0-0-0"),
"8-53-0-0":("Umělé dekorace, vazby, aranže","8-0-0-0"),

"19-0-0-0":("Koše a košíky",None),
"19-61-0-0":("proutěné","19-0-0-0"),
"19-62-0-0":("dřevěné","19-0-0-0"),
"19-151-0-0":("ostatní","19-0-0-0"),

"20-0-0-0":("Obaly na květináče, truhlíky",None),
"20-69-0-0":("dřevěné","20-0-0-0"),
"20-70-0-0":("proutěné","20-0-0-0"),
"20-73-0-0":("plechové","20-0-0-0"),
"20-74-0-0":("keramické","20-0-0-0"),
"20-75-0-0":("misky","20-0-0-0"),
"20-68-0-0":("plastové","20-0-0-0"),
"20-76-0-0":("ostatní","20-0-0-0"),

"21-0-0-0":("Bytové dekorace",None),
"21-77-0-0":("proutěné","21-0-0-0"),
"21-78-0-0":("dřevěné","21-0-0-0"),
"21-81-0-0":("látkové","21-0-0-0"),
"21-83-0-0":("plechové","21-0-0-0"),
"21-84-0-0":("keramické","21-0-0-0"),
"21-133-0-0":("svíčky","21-0-0-0"),
"21-85-0-0":("ostatní","21-0-0-0"),

"22-0-0-0":("Sezónní dekorace",None),
"22-86-0-0":("Valentýn, svatba","22-0-0-0"),
"22-87-0-0":("Jarní dekorace","22-0-0-0"),
"22-88-0-0":("Velikonoční dekorace","22-0-0-0"),
"22-89-0-0":("Podzimní dekorace","22-0-0-0"),
"22-90-0-0":("Dušičky","22-0-0-0"),
"22-134-0-0":("Vánoce a Advent","22-0-0-0"),

"24-0-0-0":("Dům a zahrada",None),
"24-109-0-0":("Zahradní doplňky","24-0-0-0"),
"24-110-0-0":("Ostatní","24-0-0-0"),
}

def build_category_tree():
    tree = {}

    for code,(name,parent) in CATEGORIES.items():
        if parent is None:
            tree.setdefault(code, {"name": name, "children": []})

    for code,(name,parent) in CATEGORIES.items():
        if parent:
            tree[parent]["children"].append((code, name))

    return tree

CATEGORY_TREE = build_category_tree()

GENERATED_PRODUCTS = []

# ------------------------------------------------

def load_eshop_header():
    with open(TEMPLATE_PATH,"r",encoding="utf-8-sig",newline="") as f:
        reader = csv.reader(f,delimiter=";")
        header = next(reader)
    return [str(h).strip() for h in header]

def clean_cezar_header(raw):
    return [str(h).split(",")[0].strip() for h in raw]

def norm_header(s):
    return " ".join(str(s or "").strip().lower().split())

# ------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<html>
<body style="font-family:sans-serif;max-width:1200px;margin:40px auto;">
<h2>Cezar → Editace textů → Parametry → Kategorie → Export</h2>
<form action="/convert" method="post" enctype="multipart/form-data">
<input type="file" name="file" accept=".csv" required>
<button type="submit">Načíst produkty</button>
</form>
</body>
</html>
"""

# ------------------------------------------------

@app.post("/convert", response_class=HTMLResponse)
async def convert(request: Request, file: UploadFile = File(...), page: int = 1):

    global GENERATED_PRODUCTS
    GENERATED_PRODUCTS = []

    _ = load_eshop_header()

    content = await file.read()
    decoded = decode_csv_bytes(content)

    rows = list(csv.reader(io.StringIO(decoded), delimiter=";"))

    raw_header = [str(h).strip() for h in rows[0]]
    header_clean = clean_cezar_header(raw_header)

    data = rows[1:]

    idx = {name:i for i,name in enumerate(header_clean)}

    for r in data:

        kod = r[idx[CEZAR_KOD]].strip()
        nazev = r[idx[CEZAR_NAZEV]].strip()

        popis = ""

        if CEZAR_POPIS in idx:
            popis = r[idx[CEZAR_POPIS]].strip()

        ean = r[idx.get(CEZAR_EAN,0)].strip()

        zakladni = format_price(r[idx[CEZAR_ZAKLADNI]])
        nase = format_price(r[idx[CEZAR_NASE]])
        stock = format_stock(r[idx[CEZAR_MNOZSTVI]])

        je_skladem = "1" if int(stock) > 0 else "0"

        cenove_hladiny = f"velkoobchod#-#{zakladni}"

        params = infer_parametry(f"{nazev} {popis}")

        GENERATED_PRODUCTS.append(
            ProductDraft(
                kod=kod,
                nazev=nazev,
                ean=ean,
                popis=popis,
                zakladni=zakladni,
                nase=nase,
                stock=stock,
                je_skladem=je_skladem,
                kategorie=CONST_KATEGORIE,
                novinka=CONST_NOVINKA,
                uvod=CONST_UVOD,
                diskuze=CONST_DISKUZE,
                dph=CONST_DPH,
                cenove_hladiny=cenove_hladiny,
                params=params,
            )
        )

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    products_page = GENERATED_PRODUCTS[start:end]

    return templates.TemplateResponse(
        "edit_text.html",
        {
            "request": request,
            "products": products_page,
            "param_keys": PARAM_KEYS,
            "param_options": PARAM_OPTIONS,
            "page": page
        },
    )

# ------------------------------------------------

@app.post("/edit-text", response_class=HTMLResponse)
async def edit_text(request: Request):

    global GENERATED_PRODUCTS

    form = await request.form()

    for i,p in enumerate(GENERATED_PRODUCTS):

        if f"name_{i}" in form:
            p.nazev = str(form[f"name_{i}"])

        if f"popis_{i}" in form:
            p.popis = str(form[f"popis_{i}"])

        p.params = infer_parametry(f"{p.nazev} {p.popis}")

    return templates.TemplateResponse(
        "edit_params.html",
        {
            "request": request,
            "products": GENERATED_PRODUCTS,
            "param_keys": PARAM_KEYS,
            "param_options": PARAM_OPTIONS,
        }
    )

# ------------------------------------------------

@app.post("/edit-categories", response_class=HTMLResponse)
async def edit_categories(request: Request):

    return templates.TemplateResponse(
        "edit_categories.html",
        {
            "request": request,
            "products": GENERATED_PRODUCTS,
            "category_tree": CATEGORY_TREE
        }
    )

# ------------------------------------------------

@app.post("/export")
async def export(request: Request):

    global GENERATED_PRODUCTS

    form = await request.form()
    selected_categories = form.getlist("cat")
    categories_string = "|".join(selected_categories)

    for i,p in enumerate(GENERATED_PRODUCTS):
        key = f"cat_{i}"
        if key in form:
            p.kategorie = form[key]

    header = load_eshop_header()

    idx = {name:i for i,name in enumerate(header)}

    def setv(row,col,val):
        if col in idx:
            row[idx[col]] = val

    rows=[]

    for p in GENERATED_PRODUCTS:

        row=[""]*len(header)
        
        p.kategorie = categories_string

        final_desc = markdown.markdown(p.popis)

        setv(row,"Kod vyrobku",p.kod)
        setv(row,"Nazev vyrobku",p.nazev)
        setv(row,"EAN kod",p.ean)
        setv(row,"Popis vyrobku",final_desc)

        setv(row,"Zakladni cena",p.zakladni)
        setv(row,"Nase cena",p.nase)

        setv(row,"Skladem (pocet kusu)",p.stock)
        setv(row,"Je skladem (1|0)",p.je_skladem)

        setv(row,"Novinka (1|0)",p.novinka)
        setv(row,"Umistit na uvod (1|0)",p.uvod)
        setv(row,"Povolit diskuzi (1|0)",p.diskuze)
        setv(row,"DPH (1|2|3|4|5)",p.dph)

        setv(row,"Zarazeni do kategorie (oddelujte znakem \"|\")",p.kategorie)
        setv(row,"Cenove hladiny",p.cenove_hladiny)
        setv(row,"Parametry","|-|".join([f"{k}#-#{(p.params.get(k,'') or '').strip()}" for k in PARAM_KEYS]))

        rows.append(row)

    out = io.StringIO(newline="")
    writer = csv.writer(out,delimiter=";",lineterminator="\r\n")

    writer.writerow(header)
    writer.writerows(rows)

    out.seek(0)

    filename=f"ESHOP_IMPORT_EXPORT_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"

    return StreamingResponse(
        out,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )