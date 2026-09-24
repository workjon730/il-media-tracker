"""סיכום תקופתי בעברית (בוקר/ערב) - נשמר כקובץ markdown בתיקיית digests/.
אם מוגדר ANTHROPIC_API_KEY, מוסיף ניתוח קצר של קלוד לכל מטרה (אופציונלי)."""
import argparse, os
from collections import defaultdict
from datetime import timedelta
from .common import now_il, data_path

def build_digest(hours=12, use_llm=True):
    from .store import recent_items
    cutoff = (now_il() - timedelta(hours=hours)).isoformat()
    items = [i for i in recent_items(days=3) if i["ts"] >= cutoff]
    by_target = defaultdict(list)
    for i in items:
        by_target[i["target_display"]].append(i)

    now = now_il()
    part = "בוקר" if now.hour < 15 else "ערב"
    lines = [f"# סיכום {part} - {now.strftime('%d/%m/%Y %H:%M')}",
             f"סה\"כ {len(items)} אזכורים ב-{hours} השעות האחרונות\n"]
    for target, rows in sorted(by_target.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"## {target} ({len(rows)} אזכורים)")
        for r in sorted(rows, key=lambda x: -x["score"])[:10]:
            src = r["sub_source"] or r["source_display"]
            lines.append(f"- [{r['title']}]({r['link']}) - {src} (ציון {r['score']})")
        summary = llm_summary(target, rows) if use_llm else None
        if summary:
            lines.append(f"\n> ניתוח: {summary}")
        lines.append("")
    if not items:
        lines.append("אין אזכורים חדשים בחלון הזמן.")
    path = data_path("digests", f"{now.strftime('%Y-%m-%d')}-{part}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path

def llm_summary(target, rows):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        headlines = "\n".join("- " + r["title"] for r in rows[:25])
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=300,
            messages=[{"role": "user", "content":
                "להלן כותרות חדשותיות מהשעות האחרונות שעוקבות אחר המטרה "
                f"\"{target}\". כתוב 2-3 משפטים בעברית: מה הסיפור המרכזי, "
                "מה הטון הכללי, והאם יש משהו שדורש תשומת לב מיידית.\n\n" + headlines}])
        return resp.content[0].text.strip()
    except Exception as e:
        return f"(ניתוח AI נכשל: {e})"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=12)
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    print(build_digest(hours=a.hours, use_llm=not a.no_llm))
