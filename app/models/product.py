from dataclasses import dataclass, field
from typing import Dict

# Product data model will be defined here

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
