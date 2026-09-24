"""מחזור סריקה אחד: מושך מקורות, מזהה אזכורים של מטרות, שומר, מתריע, מפרסם."""
import argparse, logging
from .common import load_yaml, now_il, item_id
from .fetch import fetch_source
from .detect import match_targets
from .store import load_state, save_state, store_items
from .alerts import alert_for

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("run")

ALERT_THRESHOLD = 6  # ציון = משקל מטרה x משקל מקור + בונוס בולטות

# בונוס בולטות לפריטים מסריקת דף-בית (homepage), לפי משקל הבולטות x10/x5/x3/x1.
# זה ההבדל בין "אוזכר באיזה פיד" לבין "הסיפור המוביל של האתר".
PROMINENCE_BONUS = {10: 6, 5: 4, 3: 2, 1: 1}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-alerts", action="store_true")
    args = ap.parse_args()

    cfg = load_yaml("config/sources.yaml")
    sources = [s for s in cfg["sources"] if s.get("enabled")]
    # נטייה לפי שם האתר כפי שמופיע ב-Google News (תת-מקור), לניתוח האיזון בדשבורד
    outlet_lean = cfg.get("outlet_lean", {})
    targets = load_yaml("config/targets.yaml")["targets"]

    state = load_state()
    known = set(state["known_ids"])
    now = now_il()
    new_rows, alerts_sent, sources_ok, sources_fail = [], 0, 0, []

    for src in sources:
        try:
            raw = fetch_source(src, targets)
            sources_ok += 1
        except Exception as e:
            log.warning("source %s failed: %s", src["name"], e)
            sources_fail.append(src["name"])
            continue
        for it in raw:
            iid = item_id(src["name"], it["title"])
            if iid in known:
                continue
            known.add(iid)
            hits = match_targets(it["title"], targets)
            if not hits:
                continue
            prominence = it.get("prominence") or 0
            bonus = PROMINENCE_BONUS.get(prominence, 0)
            lean = outlet_lean.get(it.get("sub_source", ""), src.get("lean", ""))
            for t in hits:
                score = t["weight"] * src["weight"] + bonus
                row = {"id": iid, "ts": now.isoformat(), "source": src["name"],
                       "source_display": src["display"], "sub_source": it.get("sub_source", ""),
                       "target": t["id"], "target_display": t["display"],
                       "groups": t.get("groups", []), "score": score,
                       "lean": lean,
                       "title": it["title"], "link": it.get("link", "")}
                if prominence:
                    row["prominence"] = prominence
                    row["rank"] = it.get("rank")
                new_rows.append(row)
                if not args.no_alerts and score >= ALERT_THRESHOLD:
                    if alert_for(it, t, src, score):
                        alerts_sent += 1

    store_items(new_rows, now)
    state["runs"] = state.get("runs", 0) + 1
    state["known_ids"] = list(known)
    save_state(state)

    from . import publish
    publish.main()

    log.info("done: sources_ok=%d failed=%s new_items=%d alerts=%d",
             sources_ok, sources_fail, len(new_rows), alerts_sent)
    print(f"sources_ok={sources_ok} failed={sources_fail} new_items={len(new_rows)} alerts={alerts_sent}")

if __name__ == "__main__":
    main()
