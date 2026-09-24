import logging, re, requests, feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .common import normalize
from .extract import fetch_html, extract_items, prominence_weight

log = logging.getLogger("fetch")
UA = {"User-Agent": "Mozilla/5.0 (compatible; il-media-tracker/1.0)"}
TIMEOUT = 20

def fetch_rss(src):
    """מחזיר רשימת פריטים: {title, link, published}"""
    d = feedparser.parse(src["url"])
    items = []
    for e in d.entries:
        title = normalize(getattr(e, "title", ""))
        if not title:
            continue
        items.append({
            "title": title,
            "link": getattr(e, "link", ""),
            "published": getattr(e, "published", "") or getattr(e, "updated", ""),
        })
    return items

# ניקוי רעשים טיפוסיים בכותרות שחולצו מדף-בית:
# מילה כפולה ברצף ("דיווח דיווח") ומטא צמוד בסוף ("... 12:44 שם הכתב").
DUP_WORD = re.compile(r"\b(\S+)( \1\b)+")
TRAIL_META = re.compile(r"\s+\d{1,2}:\d{2}(?:\s+\S+){0,3}$")

def _clean_homepage_title(t):
    t = DUP_WORD.sub(r"\1", t)
    t = TRAIL_META.sub("", t)
    return t.strip()

def fetch_homepage(src):
    """סריקת דף בית עם דירוג בולטות לפי מיקום בעמוד (הגישה של הכלי המקורי).
    לכל פריט נוספים rank (מיקום בעמוד) ו-prominence (משקל בולטות x10/x5/x3/x1)."""
    html = fetch_html(src["url"])
    items = []
    for it in extract_items(html, src["url"], src.get("selector"), src.get("lang", "he")):
        title = _clean_homepage_title(normalize(it["headline"]))
        if not title:
            continue
        items.append({
            "title": title,
            "link": it["url"],
            "published": "",
            "rank": it["rank"],
            "prominence": prominence_weight(it["rank"]),
        })
    log.info("homepage %s: %d headlines", src["name"], len(items))
    return items

def fetch_gnews(src, target):
    """חיפוש Google News בעברית עבור מטרה אחת - מכסה את כל האתרים הישראליים."""
    # Google News מתחמק משאילתות OR מרובות מילים בעברית - שולחים רק את
    # מילת המפתח הראשית (שם המטרה), והסינון המדויק קורה אצלנו ב-detect.
    q = target["keywords"][0]
    url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=he&gl=IL&ceid=IL:he"
    d = feedparser.parse(url)
    items = []
    for e in d.entries:
        title = normalize(getattr(e, "title", ""))
        # Google News מוסיף " - שם האתר" בסוף הכותרת; נשמור את שם האתר כתת-מקור
        outlet = ""
        m = re.match(r"^(.*) - ([^-]{2,40})$", title)
        if m:
            title, outlet = m.group(1).strip(), m.group(2).strip()
        if title:
            items.append({"title": title, "link": getattr(e, "link", ""),
                          "published": getattr(e, "published", ""),
                          "sub_source": outlet})
    return items

def fetch_telegram(src):
    """סריקת עמוד ה-web הציבורי של ערוץ טלגרם (ללא התחברות)."""
    r = requests.get(src["url"], headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for msg in soup.select(".tgme_widget_message"):
        txt = msg.select_one(".tgme_widget_message_text")
        link_tag = msg.select_one("a.tgme_widget_message_date")
        time_tag = msg.select_one("time")
        if not txt:
            continue
        title = normalize(txt.get_text(" ", strip=True))
        if not title:
            continue
        items.append({
            "title": title,
            "link": link_tag["href"] if link_tag else src["url"],
            "published": time_tag.get("datetime", "") if time_tag else "",
        })
    return items

def fetch_source(src, targets):
    if src["type"] == "rss":
        return fetch_rss(src)
    if src["type"] == "homepage":
        return fetch_homepage(src)
    if src["type"] == "telegram":
        return fetch_telegram(src)
    if src["type"] == "gnews":
        out = []
        for t in targets:
            out.extend(fetch_gnews(src, t))
        return out
    raise ValueError(f"unknown source type: {src['type']}")
