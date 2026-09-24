import hashlib, json, os, re, unicodedata, yaml
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IL_TZ = timezone(timedelta(hours=3), name="IDT")  # קיץ; בחורף UTC+2 - ראו README

def load_yaml(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return yaml.safe_load(f)

def normalize(text):
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace("\u05be", " ").replace("\u2013", " ").replace("\u2014", " ")
    return re.sub(r"\s+", " ", text).strip()

def item_id(source, text):
    return hashlib.sha1(f"{source}|{normalize(text).lower()}".encode("utf-8")).hexdigest()[:16]

def now_il():
    return datetime.now(IL_TZ)

def data_path(*parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def append_jsonl(path, rows):
    if not rows:
        return
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
