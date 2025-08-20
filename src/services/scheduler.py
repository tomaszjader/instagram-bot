"""Nowy system harmonogramowania z wykorzystaniem klas"""

import time
import threading
import signal
import sys
import atexit
from datetime import datetime, time as dt_time
from typing import Optional, Dict, Any, Callable

from src.config import logger, log_with_context
from src.services.services import PublisherService


class Scheduler:
    """Klasa odpowiedzialna za harmonogramowanie publikacji postów"""
    
    def __init__(self, target_hour: int = 16, target_minute: int = 0, check_interval: int = 60) -> None:
        """
        Inicjalizuje scheduler
        
        Args:
            target_hour: Godzina publikacji (0-23)
            target_minute: Minuta publikacji (0-59)
            check_interval: Interwał sprawdzania w sekundach
        """
        self.target_hour = target_hour
        self.target_minute = target_minute
        self.check_interval = check_interval
        self.publisher_service = PublisherService()
        self.current_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.shutdown_event = threading.Event()
        self.cleanup_callbacks: list[Callable[[], None]] = []
        self._setup_signal_handlers()
        self._register_cleanup()
    
    def _setup_signal_handlers(self) -> None:
        """Konfiguruje obsługę sygnałów systemowych dla graceful shutdown"""
        def signal_handler(signum: int, frame) -> None:
            signal_name = signal.Signals(signum).name
            log_with_context('info', 'Otrzymano sygnał shutdown', 
                           signal=signal_name, pid=sys.getpid())
            self.graceful_shutdown()
        
        # Obsługa sygnałów na różnych platformach
        try:
            signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # Terminate
            if hasattr(signal, 'SIGHUP'):
                signal.signal(signal.SIGHUP, signal_handler)  # Hangup (Unix)
        except (OSError, ValueError) as e:
            logger.warning(f"Nie można zarejestrować niektórych sygnałów: {e}")
    
    def _register_cleanup(self) -> None:
        """Rejestruje funkcje cleanup przy wyjściu z programu"""
        atexit.register(self._cleanup_on_exit)
    
    def _cleanup_on_exit(self) -> None:
        """Funkcja cleanup wywoływana przy wyjściu z programu"""
        if self.is_running:
            log_with_context('info', 'Wykonywanie cleanup przy wyjściu z programu')
            self.graceful_shutdown()
    
    def add_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Dodaje funkcję callback do wykonania podczas cleanup"""
        self.cleanup_callbacks.append(callback)
    
    def _execute_cleanup_callbacks(self) -> None:
        """Wykonuje wszystkie zarejestrowane funkcje cleanup"""
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Błąd podczas wykonywania cleanup callback: {e}")
    
    def _publish_task(self) -> None:
        """Zadanie publikacji uruchamiane w osobnym wątku"""
        try:
            log_with_context('info', 'Rozpoczynanie zadania publikacji', 
                           thread_id=threading.current_thread().ident)
            self.publisher_service.publish_today_posts()
            log_with_context('info', 'Zakończono zadanie publikacji')
        except Exception as e:
            log_with_context('error', 'Błąd w zadaniu publikacji', 
                           error=str(e), error_type=type(e).__name__)
        finally:
            # Sprawdź czy nie ma żądania shutdown
            if self.shutdown_event.is_set():
                log_with_context('info', 'Zadanie publikacji przerwane przez shutdown')
                return
    
    def _should_run_now(self) -> bool:
        """Sprawdza czy zadanie powinno zostać uruchomione teraz"""
        current_time = datetime.now().time()
        target_time = dt_time(self.target_hour, self.target_minute)
        
        return (current_time.hour == target_time.hour and 
                current_time.minute == target_time.minute)
    
    def _is_task_running(self) -> bool:
        """Sprawdza czy zadanie jest aktualnie uruchomione"""
        return self.current_thread is not None and self.current_thread.is_alive()
    
    def _start_publish_task(self) -> None:
        """Uruchamia zadanie publikacji w osobnym wątku"""
        if not self._is_task_running():
            logger.info("Uruchamianie zaplanowanego zadania publikacji...")
            self.current_thread = threading.Thread(target=self._publish_task)
            self.current_thread.daemon = True
            self.current_thread.start()
        else:
            logger.info("Zadanie publikacji jest już uruchomione")
    
    def run_once(self) -> None:
        """Uruchamia zadanie publikacji jednorazowo"""
        logger.info("Uruchamianie jednorazowego zadania publikacji...")
        self._publish_task()
    
    def start(self) -> None:
        """Uruchamia scheduler w trybie ciągłym"""
        log_with_context('info', 'Uruchamianie schedulera', 
                        target_time=f"{self.target_hour:02d}:{self.target_minute:02d}",
                        check_interval=self.check_interval)
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # Uruchom pierwsze zadanie w osobnym wątku
        self._start_publish_task()
        
        try:
            while self.is_running and not self.shutdown_event.is_set():
                if self._should_run_now():
                    self._start_publish_task()
                
                # Użyj shutdown_event.wait() zamiast time.sleep() dla lepszej responsywności
                if self.shutdown_event.wait(timeout=self.check_interval):
                    break  # Shutdown event został ustawiony
                
        except KeyboardInterrupt:
            log_with_context('info', 'Scheduler zatrzymany przez użytkownika (KeyboardInterrupt)')
            self.graceful_shutdown()
        except Exception as e:
            log_with_context('error', 'Nieoczekiwany błąd w scheduler', 
                           error=str(e), error_type=type(e).__name__)
            self.graceful_shutdown()
        finally:
            log_with_context('info', 'Scheduler zakończył działanie')
    
    def stop(self) -> None:
        """Zatrzymuje scheduler (alias dla graceful_shutdown)"""
        self.graceful_shutdown()
    
    def graceful_shutdown(self, timeout: int = 30) -> None:
        """Wykonuje graceful shutdown schedulera z proper cleanup"""
        if not self.is_running:
            log_with_context('info', 'Scheduler już nie działa')
            return
        
        log_with_context('info', 'Rozpoczynanie graceful shutdown', timeout=timeout)
        
        # Ustaw flagę shutdown
        self.is_running = False
        self.shutdown_event.set()
        
        # Poczekaj na zakończenie aktualnego zadania
        if self._is_task_running():
            log_with_context('info', 'Oczekiwanie na zakończenie aktualnego zadania', 
                           timeout=timeout)
            self.current_thread.join(timeout=timeout)
            
            if self.current_thread.is_alive():
                log_with_context('warning', 'Zadanie nie zakończyło się w czasie', 
                               timeout=timeout, action='force_shutdown')
                # W rzeczywistej implementacji można by tutaj użyć bardziej agresywnych metod
        
        # Wykonaj cleanup callbacks
        log_with_context('info', 'Wykonywanie cleanup callbacks', 
                        callbacks_count=len(self.cleanup_callbacks))
        self._execute_cleanup_callbacks()
        
        # Cleanup zasobów
        self._cleanup_resources()
        
        log_with_context('info', 'Graceful shutdown zakończony pomyślnie')
    
    def _cleanup_resources(self) -> None:
        """Czyści zasoby schedulera"""
        try:
            # Cleanup publisher service jeśli ma taką metodę
            if hasattr(self.publisher_service, 'cleanup'):
                self.publisher_service.cleanup()
            
            # Reset thread reference
            self.current_thread = None
            
            log_with_context('info', 'Zasoby schedulera zostały wyczyszczone')
        except Exception as e:
            log_with_context('error', 'Błąd podczas czyszczenia zasobów', 
                           error=str(e), error_type=type(e).__name__)
    
    def get_status(self) -> Dict[str, Any]:
        """Zwraca status schedulera"""
        return {
            'is_running': self.is_running,
            'shutdown_requested': self.shutdown_event.is_set(),
            'target_time': f"{self.target_hour:02d}:{self.target_minute:02d}",
            'check_interval': self.check_interval,
            'task_running': self._is_task_running(),
            'last_run': getattr(self, 'last_run_time', None),
            'cleanup_callbacks_count': len(self.cleanup_callbacks)
        }


class TestScheduler:
    """Klasa pomocnicza do testowania funkcjonalności"""
    
    def __init__(self) -> None:
        self.publisher_service = PublisherService()
    
    def test_publication(self) -> bool:
        """Testuje publikację pierwszego posta"""
        return self.publisher_service.test_publish_first_post()
    
    def test_data_parsing(self) -> None:
        """Testuje parsowanie dat z arkusza"""
        from google_sheets import test_parsowania_dat
        test_parsowania_dat()
    
    def test_data_loading(self) -> None:
        """Testuje ładowanie danych z arkusza"""
        try:
            posts = self.publisher_service.data_service.get_posts_from_sheet()
            logger.info(f"✅ Pomyślnie załadowano {len(posts)} postów z arkusza")
            
            for i, post in enumerate(posts[:3]):  # Pokaż pierwsze 3 posty
                logger.info(f"Post {i+1}: {post}")
                
        except Exception as e:
            logger.error(f"❌ Błąd podczas ładowania danych: {e}")


def create_scheduler(target_hour: int = 16, target_minute: int = 0) -> Scheduler:
    """Factory function do tworzenia schedulera"""
    return Scheduler(target_hour, target_minute)


def create_test_scheduler() -> TestScheduler:
    """Factory function do tworzenia test schedulera"""
    return TestScheduler()