#!/usr/bin/env python3
"""
Instagram Auto Publisher - Główny plik uruchomieniowy

Automatycznie publikuje posty na Instagramie na podstawie harmonogramu z Google Sheets.
Używa Google API Key (bez Service Account).

Użycie:
    python main.py          - uruchom harmonogram
    python main.py test     - test publikacji
    python main.py dates    - test parsowania dat
"""

import sys
from config import logger
from scheduler import harmonogram
from test_functions import test_publikacji
from google_sheets import test_parsowania_dat


def main():
    """Główna funkcja programu"""
    try:
        logger.info("🚀 Uruchamianie Instagram Auto Publisher")
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "test":
                logger.info("🧪 Uruchamianie testu publikacji")
                test_publikacji()
            elif command == "dates":
                logger.info("📅 Uruchamianie testu parsowania dat")
                test_parsowania_dat()
            else:
                print("❌ Nieznana komenda!")
                print("\nDostępne opcje:")
                print("  python main.py          - uruchom harmonogram")
                print("  python main.py test     - test publikacji")
                print("  python main.py dates    - test parsowania dat")
                return
        else:
            logger.info("⏰ Uruchamianie harmonogramu publikacji")
            harmonogram()
            
    except KeyboardInterrupt:
        logger.info("👋 Program zatrzymany przez użytkownika")
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        raise


if __name__ == "__main__":
    main()