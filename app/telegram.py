import requests
from typing import Dict, Any

def send_telegram_text(bot_token: str, chat_id: int | str, text: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()
