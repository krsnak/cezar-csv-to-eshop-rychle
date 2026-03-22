"""
Advanced category inference for eshop-rychle.

Používá kombinaci:

1) textová pravidla
2) parametrová pravidla
3) materiálové subkategorie
4) priority

Výstup:
    "code|code|code"
"""

from typing import List, Tuple, Dict
from app.services.category_learning import load_learning_rules

# ------------------------------------------------
# DEFAULT
# ------------------------------------------------

DEFAULT_CATEGORY = "16-0-0-0"
MAX_CATEGORIES = 3

# ------------------------------------------------
# TEXT RULES
# ------------------------------------------------
# (priority, keywords, category)
# ------------------------------------------------

TEXT_RULES: List[Tuple[int, List[str], str]] = [

    # Vánoce
    (1, ["váno", "advent", "strome", "betlém", "santa", "sob"], "22-134-0-0"),

    # Velikonoce
    (1, ["velikon", "zajíc", "vajíčko", "slepička", "kuře"], "22-88-0-0"),

    # Podzim
    (1, ["podzim", "šiška", "žalud", "listí"], "22-89-0-0"),

    # Dušičky
    (1, ["dušič", "hřbitov", "urna"], "22-90-0-0"),

    # Valentýn
    (1, ["valent", "srdce"], "22-86-0-0"),

    # Věnce
    (2, ["věnec", "věneček"], "3-58-0-0"),

    # Umělé květiny
    (3, [
        "květ",
        "květina",
        "růže",
        "tulip",
        "pivoň",
        "hortenz",
        "gerbera",
        "orchid",
        "chryzant",
        "slunečn",
        "lilie"
    ], "8-16-0-0"),

    # Dekorace do vázy
    (3, [
        "větvi",
        "větvička",
        "větévka",
        "eukalypt",
        "gypsa"
    ], "8-23-0-0"),

    # Umělé aranže
    (3, [
        "aranž",
        "dekorace květ",
        "umělá dekorace"
    ], "8-53-0-0"),

    # Koše
    (4, [
        "koš",
        "košík",
        "košíček",
        "dárkový koš"
    ], "19-0-0-0"),

    # Květináče
    (5, [
        "květináč",
        "obal",
        "truhlík",
        "miska",
        "podmiska"
    ], "20-0-0-0"),

    # Bytové dekorace
    (6, [
        "lucerna",
        "svícen",
        "svíčka",
        "dekorace",
        "figur",
        "anděl",
        "ptáček",
        "soška"
    ], "21-0-0-0"),

    # Floristický materiál
    (7, ["stuha", "provaz", "fólie", "juta"], "3-3-0-0"),

    (7, ["oasis", "aranžovací hmota"], "3-5-0-0"),

    (7, ["box", "dárkový box", "taška"], "3-146-0-0"),
]

# ------------------------------------------------
# PARAMETER RULES
# ------------------------------------------------

PARAM_RULES: Dict[str, Dict[str, str]] = {

    "Materiál": {
        "proutěné": "19-61-0-0",
        "dřevěné": "19-62-0-0",
        "proutěné obaly": "20-70-0-0",
        "dřevěné obaly": "20-69-0-0",
        "plechové": "20-73-0-0",
        "keramické": "20-74-0-0",
        "plastové": "20-68-0-0",
    },

    "Druh": {
        "věnec": "3-58-0-0",
        "koš": "19-0-0-0",
        "umělá rostlina": "8-16-0-0",
        "truhlík": "20-0-0-0",
        "obal na květináč": "20-0-0-0",
    }
}

# ------------------------------------------------
# NORMALIZACE
# ------------------------------------------------


def normalize(text: str) -> str:
    return (text or "").lower().strip()

# ------------------------------------------------
# LEARNING ENGINE
# ------------------------------------------------

def apply_learning_rules(text: str):

    rules = load_learning_rules()

    best_match = []
    best_score = 0

    for rule in rules:

        keywords = rule.get("keywords", [])
        categories = rule.get("categories", [])

        if not keywords or not categories:
            continue

        # spočítáme kolik keywordů sedí
        matches = sum(1 for k in keywords if k in text)

        # chceme alespoň 2 shody
        if matches >= 2 and matches > best_score:
            best_score = matches
            best_match = categories

    return best_match


# ------------------------------------------------
# TEXT ENGINE
# ------------------------------------------------


def apply_text_rules(text: str):

    matches: List[Tuple[int, str]] = []

    for priority, keywords, category in TEXT_RULES:

        for k in keywords:
            if k in text:
                matches.append((priority, category))
                break

    matches.sort(key=lambda x: x[0])

    result = []
    seen = set()

    for _, cat in matches:

        if cat not in seen:
            seen.add(cat)
            result.append(cat)

    return result


# ------------------------------------------------
# PARAM ENGINE
# ------------------------------------------------


def apply_param_rules(params: Dict):

    result = []

    for param, mapping in PARAM_RULES.items():

        value = params.get(param)

        if not value:
            continue

        value = value.lower()

        for keyword, cat in mapping.items():

            if keyword in value:
                result.append(cat)

    return result


# ------------------------------------------------
# MERGE ENGINE
# ------------------------------------------------


def merge_categories(text_cats: List[str], param_cats: List[str]):

    result = []
    seen = set()

    for cat in text_cats + param_cats:

        if cat not in seen:
            seen.add(cat)
            result.append(cat)

    return result[:MAX_CATEGORIES]


# ------------------------------------------------
# PUBLIC API
# ------------------------------------------------


def infer_kategorie(text: str, params: Dict = None):

    text = normalize(text)

    # 1️⃣ LEARNING má nejvyšší prioritu
    learned = apply_learning_rules(text)
    if learned:
        return "|".join(learned), "LEARNING"

    # 2️⃣ TEXT RULES
    text_categories = apply_text_rules(text)

    # 3️⃣ PARAM RULES
    param_categories = []
    if params:
        param_categories = apply_param_rules(params)

    # 4️⃣ MERGE
    categories = merge_categories(text_categories, param_categories)

    if categories:
        return "|".join(categories), "RULES"

    return DEFAULT_CATEGORY, "DEFAULT"