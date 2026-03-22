from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ProductDraft:
    kod: str
    nazev: str
    ean: str
    popis: str

    zakladni: str
    nase: str

    stock: str
    je_skladem: str

    kategorie: str

    novinka: str
    uvod: str
    diskuze: str
    dph: str

    cenove_hladiny: str

    params: Dict[str, str] = field(default_factory=dict)

    # DEBUG / AI vysvětlení
    debug_category_reason: str = ""
    is_category_edited: bool = False