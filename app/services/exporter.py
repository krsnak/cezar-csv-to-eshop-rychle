# export helper functions will be moved here
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

def format_parametry_string(params: dict) -> str:
    parts = []
    for k in PARAM_KEYS:
        v = str(params.get(k, "") or "").strip().lower()
        parts.append(f"{k}#-#{v}")
    return "|-|".join(parts)
