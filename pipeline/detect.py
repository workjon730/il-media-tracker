import re
from .common import normalize

# התאמה מותאמת-עברית: מילת מפתח נמצאת גם כשמדביקים אליה אותיות קידומת
# (לנתניהו, שאיראן, ובינה), אבל לא כשהיא חלק ממילה ארוכה יותר מימין.
def _pattern(kw):
    kw = normalize(kw)
    return re.compile(r"(?:^|[^\w\u0590-\u05ea])(?:[\u05d5\u05dc\u05d1\u05db\u05de\u05e9\u05d4]{0,2})"
                      + re.escape(kw) + r"(?![\w\u0590-\u05ea])")

def match_targets(text, targets):
    text_n = normalize(text)
    hits = []
    for t in targets:
        for kw in t.get("keywords", []):
            if _pattern(kw).search(text_n):
                hits.append(t)
                break
    return hits
