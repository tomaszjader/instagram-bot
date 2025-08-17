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
from monitoring import metrics_collector, HealthCheckServer


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
    # Uruchom serwer health check w tle
    health_server = None
    try:
        health_port = 8080
        health_server = HealthCheckServer(metrics_collector, port=health_port)
        health_thread = health_server.start_in_background()
        logger.info(f"🏥 Serwer health check uruchomiony na porcie {health_port}")
    except Exception as e:
        logger.warning(f"⚠️ Nie udało się uruchomić serwera health check: {e}")
    
    try:
        logger.info("🚀 Instagram Auto Publisher - Refaktoryzowana Wersja")
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "test":
                logger.info("🧪 Uruchamianie testu publikacji")
                metrics_collector.update_scheduler_status('testing')
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
                metrics_collector.update_scheduler_status('running_once')
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
            
            metrics_collector.update_scheduler_status('starting')
            scheduler = create_scheduler()
            scheduler.start()
            metrics_collector.update_scheduler_status('running')
            
    except KeyboardInterrupt:
        logger.info("👋 Program zatrzymany przez użytkownika")
        metrics_collector.update_scheduler_status('interrupted')
        print("\n✨ Dziękujemy za korzystanie z Instagram Auto Publisher!")
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        metrics_collector.update_scheduler_status('error')
        raise
    finally:
        metrics_collector.update_scheduler_status('stopped')


if __name__ == "__main__":
    main()