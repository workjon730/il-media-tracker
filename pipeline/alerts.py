import json, logging, os, requests

log = logging.getLogger("alerts")

def send_telegram(text):
    """שולח התראה לטלגרם אם הוגדרו TELEGRAM_BOT_TOKEN ו-TELEGRAM_CHAT_ID
    (ב-GitHub: דרך Settings -> Secrets). בלי סודות - מדלג בשקט."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        log.warning("telegram send failed: %s", e)
        return False

def alert_for(item, target, source, score):
    text = (f"\u26a1 <b>{target['display']}</b> | {source['display']}\n"
            f"{item['title']}\n{item.get('link','')}\n"
            f"(ציון חשיבות: {score})")
    return send_telegram(text)
