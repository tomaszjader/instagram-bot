#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test graceful shutdown functionality dla schedulera
"""

import time
import threading
from unittest.mock import Mock, patch
from scheduler import Scheduler
from config import log_with_context

def test_graceful_shutdown():
    """Test podstawowej funkcjonalności graceful shutdown"""
    print("\n=== Test Graceful Shutdown ===")
    
    # Utwórz scheduler z krótkim interwałem
    scheduler = Scheduler(
        target_hour=23,  # Godzina która nie nastąpi podczas testu
        target_minute=59,
        check_interval=1  # 1 sekunda dla szybkiego testu
    )
    
    # Mock publisher service cleanup method
    mock_cleanup = Mock()
    scheduler.publisher_service.cleanup = mock_cleanup
    
    # Dodaj cleanup callback
    cleanup_called = threading.Event()
    def test_cleanup():
        log_with_context('info', 'Test cleanup callback wykonany')
        cleanup_called.set()
    
    scheduler.add_cleanup_callback(test_cleanup)
    
    # Uruchom scheduler w osobnym wątku
    scheduler_thread = threading.Thread(target=scheduler.start)
    scheduler_thread.start()
    
    # Poczekaj chwilę na uruchomienie
    time.sleep(2)
    
    # Sprawdź status
    status = scheduler.get_status()
    print(f"Status przed shutdown: {status}")
    assert status['is_running'] == True
    assert status['shutdown_requested'] == False
    assert status['cleanup_callbacks_count'] == 1
    
    # Wykonaj graceful shutdown
    log_with_context('info', 'Rozpoczynanie testu graceful shutdown')
    scheduler.graceful_shutdown(timeout=5)
    
    # Poczekaj na zakończenie wątku schedulera
    scheduler_thread.join(timeout=10)
    
    # Sprawdź czy scheduler się zatrzymał
    status = scheduler.get_status()
    print(f"Status po shutdown: {status}")
    assert status['is_running'] == False
    assert status['shutdown_requested'] == True
    
    # Sprawdź czy cleanup callback został wywołany
    assert cleanup_called.wait(timeout=5), "Cleanup callback nie został wywołany"
    
    # Sprawdź czy cleanup publisher service został wywołany
    mock_cleanup.assert_called_once()
    
    print("✅ Test graceful shutdown zakończony pomyślnie")

def test_signal_handling():
    """Test obsługi sygnałów systemowych"""
    print("\n=== Test Signal Handling ===")
    
    scheduler = Scheduler(
        target_hour=23,
        target_minute=59,
        check_interval=1
    )
    
    # Test czy signal handlers zostały ustawione
    import signal
    
    # Sprawdź czy handler dla SIGTERM został ustawiony
    # (na Windows może nie być dostępny)
    try:
        current_handler = signal.signal(signal.SIGTERM, signal.SIG_DFL)
        if current_handler != signal.SIG_DFL:
            print("✅ SIGTERM handler został ustawiony")
        else:
            print("ℹ️ SIGTERM handler nie został ustawiony (może być niedostępny na Windows)")
    except AttributeError:
        print("ℹ️ SIGTERM nie jest dostępny na tej platformie")
    
    # Test SIGINT (Ctrl+C)
    try:
        current_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
        if current_handler != signal.SIG_DFL:
            print("✅ SIGINT handler został ustawiony")
        else:
            print("ℹ️ SIGINT handler używa domyślnej obsługi")
    except AttributeError:
        print("ℹ️ SIGINT nie jest dostępny na tej platformie")
    
    print("✅ Test signal handling zakończony")

def test_multiple_cleanup_callbacks():
    """Test wielu cleanup callbacks"""
    print("\n=== Test Multiple Cleanup Callbacks ===")
    
    # Utwórz nową instancję schedulera dla tego testu
    scheduler = Scheduler(
        target_hour=22,  # Inna godzina niż w poprzednich testach
        target_minute=30,
        check_interval=2
    )
    
    # Dodaj kilka cleanup callbacks
    callbacks_called = []
    
    def callback1():
        callbacks_called.append('callback1')
        log_with_context('info', 'Callback 1 wykonany')
    
    def callback2():
        callbacks_called.append('callback2')
        log_with_context('info', 'Callback 2 wykonany')
    
    def callback3():
        callbacks_called.append('callback3')
        log_with_context('info', 'Callback 3 wykonany')
    
    scheduler.add_cleanup_callback(callback1)
    scheduler.add_cleanup_callback(callback2)
    scheduler.add_cleanup_callback(callback3)
    
    # Sprawdź liczbę callbacks
    status = scheduler.get_status()
    assert status['cleanup_callbacks_count'] == 3
    print(f"Dodano {status['cleanup_callbacks_count']} cleanup callbacks")
    
    # Ustaw scheduler jako running aby graceful_shutdown działał
    scheduler.is_running = True
    
    # Wykonaj shutdown
    scheduler.graceful_shutdown()
    
    # Sprawdź czy wszystkie callbacks zostały wywołane
    print(f"Callbacks wywołane: {callbacks_called}")
    assert len(callbacks_called) == 3, f"Oczekiwano 3 callbacks, otrzymano {len(callbacks_called)}: {callbacks_called}"
    assert 'callback1' in callbacks_called
    assert 'callback2' in callbacks_called
    assert 'callback3' in callbacks_called
    
    print(f"✅ Wszystkie {len(callbacks_called)} cleanup callbacks zostały wykonane")

if __name__ == '__main__':
    log_with_context('info', 'Rozpoczynanie testów graceful shutdown')
    
    try:
        test_graceful_shutdown()
        test_signal_handling()
        test_multiple_cleanup_callbacks()
        
        log_with_context('info', 'Wszystkie testy graceful shutdown zakończone pomyślnie')
        print("\n🎉 Wszystkie testy przeszły pomyślnie!")
        
    except Exception as e:
        log_with_context('error', 'Błąd podczas testów graceful shutdown', 
                        error=str(e), error_type=type(e).__name__)
        print(f"\n❌ Test failed: {e}")
        raise