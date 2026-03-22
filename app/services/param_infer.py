import re

# param inference functions will be moved here
def normalize(text):
    return str(text or "").lower()
# param inference functions will be moved here
def normalize(text):
    return str(text or "").lower()

def infer_barva(text: str) -> str:
    t = normalize(text)
    COLOR_MAP = {
        "bíl": "bílá",
        "šed": "šedá",
        "červen": "červená",
        "růž": "růžová",
        "oranž": "oranžová",
        "žlut": "žlutá",
        "modr": "modrá",
        "zelen": "zelená",
        "hněd": "hnědá",
        "čern": "černá",
}
    if "mix" in t:
        return "mix"
    for fragment, color in COLOR_MAP.items():
        if fragment in t:
            return color
    
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
    MATERIAL_MAP = {
        "dřevo": "dřevěné",
        "dřev": "dřevěné",
        "dýh": "dýha",
        "prout": "proutěné",
        "ratan": "ratanové",
        "plast": "plastové",
        "keram": "keramické",
        "kov": "kovové",
        "sklo": "skleněné",
}
    for fragment, material in MATERIAL_MAP.items():
        if fragment in t:
            return material
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
    TVAR_MAP = {
        "obdéln": "hranatý",
        "hranat": "hranatý",
        "ovál": "oválný",
        "kulat": "kulatý",
        "srd": "srdce",
        "hvězd": "hvězda",
}
    for fragment, shape in TVAR_MAP.items():
        if fragment in t:
            return shape
    
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
        ("obdéln", "hranatý"),
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
    elif "truhl" in t:
        druh = "truhlík"
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
