import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    """
    Invia notifiche su Telegram con aggiornamenti sulle operazioni.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Token Telegram o Chat ID mancanti!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, params=params)
    
    if response.status_code == 200:
        logging.info(f"📩 Messaggio Telegram inviato: {message}")
    else:
        logging.error(f"❌ Errore nell'invio del messaggio Telegram: {response.text}")
