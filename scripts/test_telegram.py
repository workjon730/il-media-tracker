"""בדיקת חיבור לבוט הטלגרם - שולח הודעת בדיקה אחת ומדווח.

מריצים מ-GitHub: Actions -> telegram-test -> Run workflow
(אחרי שמגדירים את הסודות TELEGRAM_BOT_TOKEN ו-TELEGRAM_CHAT_ID).
או מקומית: TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python scripts/test_telegram.py
"""
import os, sys, requests

token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat = os.environ.get("TELEGRAM_CHAT_ID")
if not token or not chat:
    print("חסרים הסודות TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
    print("מגדירים ב: Settings -> Secrets and variables -> Actions")
    sys.exit(1)

r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat,
          "text": "✅ עין התקשורת: הבוט מחובר ועובד. מכאן יגיעו ההתראות והסיכומים."},
    timeout=15)
if r.ok:
    print("ההודעה נשלחה בהצלחה - בדוק את הטלגרם")
else:
    print(f"שליחה נכשלה: {r.status_code} {r.text[:200]}")
    sys.exit(1)
