# CSV parsing functions will be moved here

def normalize(text):
    return str(text or "").lower()

def norm_header(s: str) -> str:
    return " ".join(str(s or "").strip().lower().split())

def decode_csv_bytes(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1250")
