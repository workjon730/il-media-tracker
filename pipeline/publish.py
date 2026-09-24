"""בונה את קבצי ה-JSON שהדשבורד (docs/index.html) קורא."""
import json
from collections import Counter
from datetime import timedelta
from .common import data_path, now_il
from .store import recent_items

LEAN_DISPLAY = {"right": "ימין", "center": "מרכז", "left": "שמאל"}

def main():
    items = recent_items(days=3)
    cutoff = (now_il() - timedelta(hours=24)).isoformat()
    day_items = [i for i in items if i["ts"] >= cutoff]
    per_target = Counter(i["target_display"] for i in day_items)
    per_source = Counter(i["sub_source"] or i["source_display"] for i in day_items)
    per_lean = Counter(LEAN_DISPLAY.get(i.get("lean"), "אחר") for i in day_items)
    # הסיפורים הבולטים ביותר כרגע: אזכורים שזוהו בראש דף-בית של אתר
    leads = sorted(
        (i for i in day_items if (i.get("prominence") or 0) >= 3),
        key=lambda i: (-i["prominence"], i["ts"]),
    )[:12]
    payload = {
        "generated": now_il().isoformat(),
        "last_24h_total": len(day_items),
        "per_target": dict(per_target.most_common()),
        "per_source": dict(per_source.most_common()),
        "per_lean": dict(per_lean.most_common()),
        "leads": leads,
        "items": sorted(items, key=lambda i: (i["score"], i["ts"]), reverse=True)[:300],
    }
    out = data_path("docs", "data", "latest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
