import json, os
from .common import data_path, append_jsonl, read_jsonl

STATE = "data/state.json"

def load_state():
    p = data_path(STATE)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"known_ids": [], "runs": 0}

def save_state(state):
    # שומרים רק 50,000 מזהים אחרונים כדי שהקובץ לא יתנפח
    state["known_ids"] = state["known_ids"][-50000:]
    with open(data_path(STATE), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def month_file(dt):
    return data_path("data", "items", f"{dt.year:04d}-{dt.month:02d}.jsonl")

def store_items(rows, dt):
    append_jsonl(month_file(dt), rows)

def recent_items(days=2):
    import glob
    items = []
    for path in sorted(glob.glob(data_path("data", "items", "*.jsonl")))[-3:]:
        items.extend(read_jsonl(path))
    return items
