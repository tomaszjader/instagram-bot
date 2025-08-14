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
from scheduler_new import create_scheduler, create_test_scheduler


def main():
    """Główna funkcja programu"""
    try:
        logger.info("🚀 Uruchamianie Instagram Auto Publisher")
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "test":
                logger.info("🧪 Uruchamianie testu publikacji")
                test_scheduler = create_test_scheduler()
                test_scheduler.test_publication()
            elif command == "dates":
                logger.info("📅 Uruchamianie testu parsowania dat")
                test_scheduler = create_test_scheduler()
                test_scheduler.test_data_parsing()
            elif command == "data":
                logger.info("📊 Uruchamianie testu ładowania danych")
                test_scheduler = create_test_scheduler()
                test_scheduler.test_data_loading()
            elif command == "once":
                logger.info("🎯 Uruchamianie jednorazowej publikacji")
                scheduler = create_scheduler()
                scheduler.run_once()
            else:
                print("❌ Nieznana komenda!")
                print("\nDostępne opcje:")
                print("  python main.py          - uruchom harmonogram")
                print("  python main.py test     - test publikacji")
                print("  python main.py dates    - test parsowania dat")
                print("  python main.py data     - test ładowania danych")
                print("  python main.py once     - jednorazowa publikacja")
                return
        else:
            logger.info("⏰ Uruchamianie harmonogramu publikacji")
            scheduler = create_scheduler()
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("👋 Program zatrzymany przez użytkownika")
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        raise


if __name__ == "__main__":
    main()