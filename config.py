import os
import logging
import json
from datetime import datetime
from typing import Dict, Optional, Any
from dotenv import load_dotenv


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Dodaj informacje o wyjątku jeśli istnieją
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Dodaj dodatkowe pola jeśli istnieją
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    """Konfiguruje system logowania z obsługą różnych formatów i poziomów"""
    # Pobierz konfigurację z zmiennych środowiskowych
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'TEXT').upper()  # TEXT lub JSON
    
    # Konwersja poziomu logowania
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    numeric_level = level_mapping.get(log_level, logging.INFO)
    
    # Usuń istniejące handlery
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Utwórz nowy handler
    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)
    
    # Wybierz formatter
    if log_format == 'JSON':
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Konfiguruj root logger
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(handler)
    
    # Zwróć logger dla tego modułu
    return logging.getLogger(__name__)


# Konfiguracja logowania
logger = setup_logging()

# Załaduj zmienne środowiskowe
load_dotenv()

# ===== KONFIGURACJA =====
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Sprawdzenie wymaganych i opcjonalnych zmiennych środowiskowych
required_vars = {
    'INSTA_USERNAME': INSTA_USERNAME,
    'INSTA_PASSWORD': INSTA_PASSWORD,
    'GOOGLE_SHEET_ID': GOOGLE_SHEET_ID,
    'GOOGLE_API_KEY': GOOGLE_API_KEY
}

optional_vars = {
    'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
}

def validate_config() -> None:
    """Sprawdza czy wszystkie wymagane zmienne środowiskowe są ustawione"""
    missing_vars = []
    
    # Sprawdź wymagane zmienne
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"Brakujące wymagane zmienne środowiskowe: {', '.join(missing_vars)}")
    
    # Sprawdź opcjonalne zmienne i ostrzeż jeśli brakują
    missing_optional = []
    for var_name, var_value in optional_vars.items():
        if not var_value:
            missing_optional.append(var_name)
    
    if missing_optional:
        logger.warning(f"⚠️ Brakujące opcjonalne zmienne środowiskowe: {', '.join(missing_optional)}")
        logger.warning("Powiadomienia Telegram będą wyłączone")
    
    logger.info("✅ Wszystkie wymagane zmienne środowiskowe są ustawione")

def is_telegram_enabled() -> bool:
    """Sprawdza czy Telegram jest skonfigurowany"""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def log_with_context(level: str, message: str, **kwargs: Any) -> None:
    """Loguje wiadomość z dodatkowymi polami kontekstowymi dla structured logging"""
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level.upper()),
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    if kwargs:
        record.extra_fields = kwargs
    
    logger.handle(record)


def get_logging_config() -> Dict[str, str]:
    """Zwraca aktualną konfigurację logowania"""
    return {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'format': os.getenv('LOG_FORMAT', 'TEXT'),
        'current_level': logging.getLevelName(logger.level)
    }

# Automatyczna walidacja przy imporcie
validate_config()