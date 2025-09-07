import os
import logging
from dotenv import load_dotenv

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Załaduj zmienne środowiskowe
load_dotenv()

# ===== KONFIGURACJA =====
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Sprawdzenie czy wszystkie wymagane zmienne środowiskowe są ustawione
required_vars = {
    'INSTA_USERNAME': INSTA_USERNAME,
    'INSTA_PASSWORD': INSTA_PASSWORD,
    'GOOGLE_SHEET_ID': GOOGLE_SHEET_ID,
    'GOOGLE_API_KEY': GOOGLE_API_KEY,
    'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
}

def validate_config():
    """Sprawdza czy wszystkie wymagane zmienne środowiskowe są ustawione"""
    for var_name, var_value in required_vars.items():
        if not var_value:
            raise ValueError(f"Zmienna środowiskowa {var_name} nie jest ustawiona!")
    
    logger.info("✅ Wszystkie wymagane zmienne środowiskowe są ustawione")

# Automatyczna walidacja przy imporcie
validate_config()