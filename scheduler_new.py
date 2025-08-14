"""Nowy system harmonogramowania z wykorzystaniem klas"""

import time
import threading
from datetime import datetime, time as dt_time
from typing import Optional

from config import logger
from services import PublisherService


class Scheduler:
    """Klasa odpowiedzialna za harmonogramowanie publikacji postów"""
    
    def __init__(self, target_hour: int = 16, target_minute: int = 0, check_interval: int = 60):
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
    
    def _publish_task(self) -> None:
        """Zadanie publikacji uruchamiane w osobnym wątku"""
        try:
            self.publisher_service.publish_today_posts()
        except Exception as e:
            logger.error(f"Błąd w zadaniu publikacji: {e}")
    
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
        logger.info(f"🚀 Uruchamianie schedulera - publikacja codziennie o {self.target_hour:02d}:{self.target_minute:02d}")
        logger.info(f"⏰ Sprawdzanie co {self.check_interval} sekund")
        
        self.is_running = True
        
        # Uruchom pierwsze zadanie w osobnym wątku
        self._start_publish_task()
        
        try:
            while self.is_running:
                if self._should_run_now():
                    self._start_publish_task()
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("👋 Scheduler zatrzymany przez użytkownika")
            self.stop()
    
    def stop(self) -> None:
        """Zatrzymuje scheduler"""
        logger.info("Zatrzymywanie schedulera...")
        self.is_running = False
        
        # Poczekaj na zakończenie aktualnego zadania
        if self._is_task_running():
            logger.info("Oczekiwanie na zakończenie aktualnego zadania...")
            self.current_thread.join(timeout=30)
            
            if self.current_thread.is_alive():
                logger.warning("Zadanie nie zakończyło się w czasie - wymuszanie zatrzymania")
    
    def get_status(self) -> dict:
        """Zwraca status schedulera"""
        return {
            'is_running': self.is_running,
            'target_time': f"{self.target_hour:02d}:{self.target_minute:02d}",
            'check_interval': self.check_interval,
            'task_running': self._is_task_running(),
            'next_check': datetime.now().replace(
                hour=self.target_hour, 
                minute=self.target_minute, 
                second=0, 
                microsecond=0
            ).isoformat()
        }


class TestScheduler:
    """Klasa pomocnicza do testowania funkcjonalności"""
    
    def __init__(self):
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