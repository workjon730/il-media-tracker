"""חילוץ כותרות מדפי בית של אתרי חדשות, עם דירוג בולטות לפי מיקום בעמוד.

הגישה מבוססת על הכלי המקורי (הריפו של אוריך): הסדר שבו קישורים מופיעים
ב-DOM של דף הבית מקרב את הבולטות העיתונאית - הסיפור הראשי מופיע ראשון.
ככה מקבלים לא רק "אם" הוזכרה מטרה, אלא גם כמה בולט האזכור.
"""
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# טקסט קצר מזה נחשב ניווט ולא כותרת. בעברית אפשר למנות מ-15 תווים.
MIN_HEADLINE_LEN = {"he": 15, "en": 25}
# אזורים בעמוד שאינם תוכן עיתונאי
SKIP_ANCESTORS = {"nav", "footer", "aside", "form"}
SKIP_HREF_PAT = re.compile(
    r"/(video|videos|live-tv|newsletters?|podcasts?|games|crosswords?|recipes|"
    r"horoscopes?|account|subscribe|login|signin|register|terms|privacy|about|"
    r"contact|advertis|shop|store|deals|coupons|tags?|category|redmail)(/|$)",
    re.I,
)


def fetch_html(url, timeout=25):
    resp = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": UA,
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.7,en;q=0.6",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    resp.raise_for_status()
    return resp.text


def _clean(s):
    return re.sub(r"\s+", " ", s).strip()


def extract_items(html, base_url, selector=None, lang="he"):
    """מחזיר פריטי כותרות לפי סדר הופעה בעמוד: [{rank, headline, url}]."""
    soup = BeautifulSoup(html, "html.parser")
    scope = soup.select_one(selector) if selector else None
    scope = scope or soup.body or soup
    host = urlparse(base_url).netloc.split(":")[0].removeprefix("www.")
    min_len = MIN_HEADLINE_LEN.get(lang, MIN_HEADLINE_LEN["en"])

    items, seen_text, seen_urls = [], set(), set()
    for a in scope.find_all("a", href=True):
        # דילוג על קישורים בתוך chrome של האתר (תפריטים, פוטר וכו')
        if any(p.name in SKIP_ANCESTORS for p in a.parents):
            continue
        text = _clean(a.get_text(" "))
        if len(text) < min_len or len(text) > 300:
            continue
        href = urljoin(base_url, a["href"].split("#")[0])
        pu = urlparse(href)
        if pu.scheme not in ("http", "https"):
            continue
        link_host = pu.netloc.split(":")[0].removeprefix("www.")
        # רק קישורים לאותו אתר (כולל תת-דומיינים)
        if not (link_host == host or link_host.endswith("." + host) or host.endswith("." + link_host)):
            continue
        if SKIP_HREF_PAT.search(pu.path):
            continue
        key = text.lower()
        if key in seen_text or href in seen_urls:
            continue
        seen_text.add(key)
        seen_urls.add(href)
        items.append({"rank": len(items) + 1, "headline": text, "url": href})
    return items


def prominence_weight(rank):
    """משקל בולטות תלול (כמו בכלי המקורי): מקום 1 = x10, 2-5 = x5,
    6-10 = x3, 11-20 = x1, מעבר לכך = 0."""
    if rank == 1:
        return 10
    if rank <= 5:
        return 5
    if rank <= 10:
        return 3
    if rank <= 20:
        return 1
    return 0
