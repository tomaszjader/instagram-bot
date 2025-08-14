#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refaktoryzowana wersja Instagram Auto Publisher

Ta wersja demonstruje poprawki trzech głównych problemów:
1. Monolityczna funkcja harmonogram() - zastąpiona klasą Scheduler
2. Duplikacja kodu - scentralizowane w klasach serwisowych
3. Brak klas i enkapsulacji - wprowadzono architekturę opartą na klasach

Struktura:
- models.py: Modele danych (Post, ColumnMapper)
- services.py: Logika biznesowa (DataService, ImageService, NotificationService, PublisherService)
- scheduler_new.py: Harmonogramowanie (Scheduler, TestScheduler)
- main.py: Punkt wejścia aplikacji
"""

import sys
from config import logger
from scheduler_new import create_scheduler, create_test_scheduler


def show_comparison():
    """Pokazuje porównanie starej i nowej architektury"""
    print("\n" + "="*60)
    print("📊 PORÓWNANIE ARCHITEKTURY")
    print("="*60)
    
    print("\n🔴 STARA ARCHITEKTURA:")
    print("  ❌ Monolityczna funkcja harmonogram() (160+ linii)")
    print("  ❌ Duplikacja kodu w scheduler.py i test_functions.py")
    print("  ❌ Brak klas - tylko funkcje")
    print("  ❌ Trudne testowanie i utrzymanie")
    print("  ❌ Mieszanie logiki harmonogramowania z publikacją")
    
    print("\n🟢 NOWA ARCHITEKTURA:")
    print("  ✅ Klasa Scheduler - odpowiedzialność za harmonogramowanie")
    print("  ✅ Klasy serwisowe - podział odpowiedzialności")
    print("  ✅ Model Post - enkapsulacja danych")
    print("  ✅ ColumnMapper - centralne mapowanie kolumn")
    print("  ✅ Łatwe testowanie każdego komponentu")
    print("  ✅ Możliwość rozszerzania funkcjonalności")
    
    print("\n📁 NOWE PLIKI:")
    print("  📄 models.py - Modele danych")
    print("  📄 services.py - Logika biznesowa")
    print("  📄 scheduler_new.py - Nowy scheduler")
    print("  📄 refactored_main.py - Ten plik demonstracyjny")
    
    print("\n🔧 KORZYŚCI:")
    print("  🎯 Single Responsibility Principle")
    print("  🔄 Łatwiejsze testowanie jednostkowe")
    print("  📈 Lepsza skalowalność")
    print("  🛠️ Prostsze debugowanie")
    print("  📚 Czytelniejszy kod")
    
    print("\n" + "="*60)


def show_usage():
    """Pokazuje dostępne opcje użycia"""
    print("\n🚀 DOSTĘPNE KOMENDY:")
    print("  python refactored_main.py                - uruchom harmonogram")
    print("  python refactored_main.py test           - test publikacji")
    print("  python refactored_main.py dates          - test parsowania dat")
    print("  python refactored_main.py data           - test ładowania danych")
    print("  python refactored_main.py once           - jednorazowa publikacja")
    print("  python refactored_main.py compare        - porównanie architektury")
    print("  python refactored_main.py status         - status schedulera")
    print("  python refactored_main.py help           - ta pomoc")


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
    """Główna funkcja refaktoryzowanej aplikacji"""
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
                
            elif command == "compare":
                show_comparison()
                
            elif command == "status":
                show_scheduler_status()
                
            elif command == "help":
                show_usage()
                
            else:
                print(f"❌ Nieznana komenda: {command}")
                show_usage()
                return
        else:
            logger.info("⏰ Uruchamianie harmonogramu publikacji")
            print("\n🎯 Uruchamianie nowego schedulera opartego na klasach...")
            print("💡 Użyj 'python refactored_main.py compare' aby zobaczyć różnice")
            
            scheduler = create_scheduler()
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("👋 Program zatrzymany przez użytkownika")
        print("\n✨ Dziękujemy za korzystanie z refaktoryzowanej wersji!")
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        raise


if __name__ == "__main__":
    main()