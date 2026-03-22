import json
import os
from typing import List, Dict

# ------------------------------------------------

LEARNING_PATH = "app/data/category_learning.json"

# ------------------------------------------------


def load_learning_rules() -> List[Dict]:
    """
    Načte uložené learned rules.
    """

    if not os.path.exists(LEARNING_PATH):
        return []

    try:
        with open(LEARNING_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


# ------------------------------------------------


def save_learning_rules(rules: List[Dict]):
    """
    Uloží learned rules do JSON.
    """

    os.makedirs(os.path.dirname(LEARNING_PATH), exist_ok=True)

    with open(LEARNING_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


# ------------------------------------------------


def add_learning_rule(keywords: List[str], categories: List[str]):
    """
    Přidá nové pravidlo (pokud neexistuje).
    """

    # odstraníme "Novinky" z learned rules
    categories = [c for c in categories if c != "16-0-0-0"]

    rules = load_learning_rules()

    keywords = sorted(set([k.lower() for k in keywords if k]))

    if not keywords or not categories:
        return

    for r in rules:
        if sorted(r.get("keywords", [])) == keywords:
            r["categories"] = categories
            save_learning_rules(rules)
            return

    rules.append({
        "keywords": keywords,
        "categories": categories
    })

    save_learning_rules(rules)