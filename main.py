#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Auto Publisher - Główny plik uruchomieniowy

Automatycznie publikuje posty na Instagramie na podstawie harmonogramu z Google Sheets.
Używa refaktoryzowanej architektury opartej na klasach.

Użycie:
    python main.py          - uruchom harmonogram
    python main.py test     - test publikacji
    python main.py dates    - test parsowania dat
    python main.py data     - test ładowania danych
    python main.py once     - jednorazowa publikacja
    python main.py status   - status schedulera
    python main.py help     - pomoc
"""

import sys
from config import logger
from scheduler import create_scheduler, create_test_scheduler


def show_usage():
    """Pokazuje dostępne opcje użycia"""
    print("\n🚀 DOSTĘPNE KOMENDY:")
    print("  python main.py                - uruchom harmonogram")
    print("  python main.py test           - test publikacji")
    print("  python main.py dates          - test parsowania dat")
    print("  python main.py data           - test ładowania danych")
    print("  python main.py once           - jednorazowa publikacja")
    print("  python main.py status         - status schedulera")
    print("  python main.py help           - ta pomoc")


def show_scheduler_status():
    """Pokazuje status schedulera"""
    try:
        scheduler = create_scheduler()
        status = scheduler.get_status()
        
        print("\n📊 STATUS SCHEDULERA:")
        print(f"  🔄 Uruchomiony: {'✅ Tak' if status['is_running'] else '❌ Nie'}")
        print(f"  ⏰ Czas publikacji: {status['target_time']}")
        print(f"  🔍 Interwał sprawdzania: {status['check_interval']}s")
        print(f"  🎯 Zadanie aktywne: {'✅ Tak' if status['task_running'] else '❌ Nie'}")
        print(f"  📅 Następne sprawdzenie: {status['next_check']}")
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statusu: {e}")


def main():
    """Główna funkcja programu"""
    try:
        logger.info("🚀 Instagram Auto Publisher - Refaktoryzowana Wersja")
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "test":
                logger.info("🧪 Uruchamianie testu publikacji")
                test_scheduler = create_test_scheduler()
                success = test_scheduler.test_publication()
                print(f"\n{'✅ Test zakończony sukcesem!' if success else '❌ Test zakończony niepowodzeniem!'}")
                
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
                
            elif command == "status":
                show_scheduler_status()
                
            elif command == "help":
                show_usage()
                
            else:
                print(f"❌ Nieznana komenda: {command}")
                show_usage()
                print("  python main.py once     - jednorazowa publikacja")
                return
        else:
            logger.info("⏰ Uruchamianie harmonogramu publikacji")
            print("\n🎯 Uruchamianie schedulera opartego na klasach...")
            print("💡 Użyj 'python main.py help' aby zobaczyć wszystkie opcje")
            
            scheduler = create_scheduler()
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("👋 Program zatrzymany przez użytkownika")
        print("\n✨ Dziękujemy za korzystanie z Instagram Auto Publisher!")
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        raise


if __name__ == "__main__":
    main()