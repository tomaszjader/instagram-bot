import requests
from config import logger


def wyslij_telegram(token, chat_id, wiadomosc):
    """Wysyła wiadomość przez Telegram"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": wiadomosc,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info("Wysłano powiadomienie Telegram")
    except Exception as e:
        logger.error(f"Błąd podczas wysyłania wiadomości Telegram: {e}")