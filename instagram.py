import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, RateLimitError
from config import logger
from google_sheets import gdrive_to_direct
from image_utils import pobierz_i_zapisz_zdjecie, przetworz_lokalny_obraz
from utils import retry_with_backoff, instagram_rate_limiter


class InstagramManager:
    """Zarządza sesjami Instagram z persistence"""
    
    def __init__(self, username: str, password: str, session_file: str = "instagram_session.json") -> None:
        self.username = username
        self.password = password
        self.session_file = Path(session_file)
        self.client: Optional[Client] = None
    
    def _save_session(self) -> bool:
        """Zapisuje sesję do pliku"""
        if self.client:
            try:
                session_data = self.client.get_settings()
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                logger.info(f"Sesja zapisana do {self.session_file}")
            except Exception as e:
                logger.warning(f"Nie można zapisać sesji: {e}")
    
    def _load_session(self) -> bool:
        """Ładuje sesję z pliku"""
        if not self.session_file.exists():
            return False
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            self.client = Client()
            self.client.set_settings(session_data)
            
            # Sprawdź czy sesja jest nadal ważna
            self.client.get_timeline_feed()
            logger.info("Sesja załadowana pomyślnie")
            return True
            
        except Exception as e:
            logger.warning(f"Nie można załadować sesji: {e}")
            # Usuń nieprawidłowy plik sesji
            try:
                self.session_file.unlink()
            except:
                pass
            return False
    
    @retry_with_backoff(
        max_retries=3,
        base_delay=5.0,
        max_delay=60.0,
        exceptions=(LoginRequired, PleaseWaitFewMinutes, ConnectionError)
    )
    def login(self) -> Optional[Client]:
        """Loguje się do Instagrama z session persistence"""
        instagram_rate_limiter.wait_if_needed()
        
        # Spróbuj załadować istniejącą sesję
        if self._load_session():
            return self.client
        
        # Jeśli nie ma sesji lub jest nieprawidłowa, zaloguj się ponownie
        try:
            self.client = Client()
            self.client.login(self.username, self.password)
            logger.info("Pomyślnie zalogowano do Instagrama")
            
            # Zapisz sesję
            self._save_session()
            
            return self.client
            
        except (LoginRequired, PleaseWaitFewMinutes, RateLimitError) as e:
            logger.warning(f"Instagram wymaga oczekiwania lub ma problemy z logowaniem: {e}")
            raise
        except Exception as e:
            logger.error(f"Błąd podczas logowania do Instagrama: {e}")
            raise
    
    def get_client(self) -> Optional[Client]:
        """Zwraca aktualnego klienta lub None"""
        return self.client
    
    def logout(self) -> None:
        """Wylogowuje i usuwa sesję"""
        if self.client:
            try:
                self.client.logout()
            except:
                pass
        
        # Usuń plik sesji
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Sesja usunięta")
        except Exception as e:
            logger.warning(f"Nie można usunąć pliku sesji: {e}")
        
        self.client = None


# Globalna instancja managera (będzie inicjalizowana w services.py)
_instagram_manager: Optional[InstagramManager] = None


def get_instagram_manager(username: str, password: str) -> InstagramManager:
    """Zwraca globalną instancję Instagram managera"""
    global _instagram_manager
    if _instagram_manager is None:
        _instagram_manager = InstagramManager(username, password)
    return _instagram_manager


@retry_with_backoff(
    max_retries=3,
    base_delay=5.0,
    max_delay=60.0,
    exceptions=(LoginRequired, PleaseWaitFewMinutes, ConnectionError)
)
def zaloguj_instagrama(username: str, password: str) -> Optional[Client]:
    """Loguje się do Instagrama z retry mechanism (backward compatibility)"""
    manager = get_instagram_manager(username, password)
    return manager.login()


@retry_with_backoff(
    max_retries=2,
    base_delay=10.0,
    max_delay=120.0,
    exceptions=(PleaseWaitFewMinutes, RateLimitError, ConnectionError)
)
def opublikuj_post(cl: Client, sciezka_zdjecia: str, opis: str) -> Any:
    """Publikuje post na Instagramie z retry mechanism"""
    try:
        instagram_rate_limiter.wait_if_needed()
        # Sprawdź czy to URL czy lokalna ścieżka
        if sciezka_zdjecia.startswith(('http://', 'https://')):
            # To jest URL - pobierz obrazek
            logger.info(f"Wykryto URL obrazka: {sciezka_zdjecia}")
            
            # Konwertuj URL Google Drive na bezpośredni link
            direct_url = gdrive_to_direct(sciezka_zdjecia)
            if direct_url != sciezka_zdjecia:
                logger.info(f"Przekonwertowano URL Google Drive: {direct_url}")
            
            # Pobierz obrazek
            temp_path = pobierz_i_zapisz_zdjecie(direct_url, "post")
            if not temp_path:
                raise Exception(f"Nie udało się pobrać obrazka z URL: {sciezka_zdjecia}")
            
            try:
                # Publikuj post z pobranym obrazkiem
                media = cl.photo_upload(temp_path, opis)
                logger.info(f"Pomyślnie opublikowano post: {media.pk}")
                return media
            finally:
                # Usuń tymczasowy plik
                try:
                    os.remove(temp_path)
                    logger.info(f"Usunięto tymczasowy plik: {temp_path}")
                except Exception as e:
                    logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")
        else:
            # To jest lokalna ścieżka
            if not os.path.exists(sciezka_zdjecia):
                raise FileNotFoundError(f"Nie znaleziono pliku: {sciezka_zdjecia}")

            # Przetwórz lokalny plik, aby miał odpowiednie proporcje
            temp_path = przetworz_lokalny_obraz(sciezka_zdjecia)
            
            try:
                media = cl.photo_upload(temp_path, opis)
                logger.info(f"Pomyślnie opublikowano post: {media.pk}")
                return media
            finally:
                # Usuń tymczasowy plik jeśli został utworzony
                if temp_path != sciezka_zdjecia:
                    try:
                        os.remove(temp_path)
                        logger.info(f"Usunięto tymczasowy plik: {temp_path}")
                    except Exception as e:
                        logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")
            
    except Exception as e:
        logger.error(f"Błąd podczas publikowania posta: {e}")
        raise