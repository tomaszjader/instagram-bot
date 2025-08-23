import asyncio
import aiofiles
import aiohttp
from typing import Optional, Any
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, PleaseWaitFewMinutes, RateLimitError,
    ClientError, ClientConnectionError, ClientThrottledError
)
from src.config import logger, INSTA_USERNAME, INSTA_PASSWORD
from src.integrations.google_sheets import gdrive_to_direct
from src.utils.image_utils import pobierz_i_zapisz_zdjecie, przetworz_lokalny_obraz
from src.utils import RateLimiter


class AsyncInstagramManager:
    """Asynchroniczny menedżer dla operacji Instagram"""
    
    def __init__(self, username: str, password: str, session_file: str = "instagram_session.json"):
        self.username = username
        self.password = password
        self.session_file = session_file
        self.client: Optional[Client] = None
        self.rate_limiter = RateLimiter(calls_per_minute=30)  # Instagram API limit
        self._login_lock = asyncio.Lock()
    
    async def _save_session_async(self) -> bool:
        """Asynchronicznie zapisuje sesję Instagram"""
        if not self.client:
            return False
            
        try:
            session_data = self.client.get_settings()
            async with aiofiles.open(self.session_file, 'w') as f:
                await f.write(str(session_data))
            logger.info(f"Sesja Instagram zapisana do {self.session_file}")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania sesji: {e}")
            return False
    
    async def _load_session_async(self) -> bool:
        """Asynchronicznie ładuje sesję Instagram"""
        try:
            if not Path(self.session_file).exists():
                logger.info("Plik sesji nie istnieje")
                return False
                
            async with aiofiles.open(self.session_file, 'r') as f:
                session_data = await f.read()
                
            if not self.client:
                self.client = Client()
                
            # Konwertuj string z powrotem na dict
            session_dict = eval(session_data)  # Uwaga: w produkcji użyj json.loads
            self.client.set_settings(session_dict)
            
            # Sprawdź czy sesja jest nadal ważna
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.account_info
            )
            
            logger.info("Pomyślnie załadowano sesję Instagram")
            return True
            
        except Exception as e:
            logger.warning(f"Nie można załadować sesji: {e}")
            return False
    
    async def login_async(self) -> Optional[Client]:
        """Asynchronicznie loguje do Instagram z retry mechanism"""
        async with self._login_lock:
            if self.client:
                try:
                    # Sprawdź czy klient jest nadal aktywny
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.client.account_info
                    )
                    return self.client
                except Exception:
                    logger.info("Istniejąca sesja wygasła, logowanie ponownie")
                    self.client = None
            
            # Spróbuj załadować zapisaną sesję
            if await self._load_session_async():
                return self.client
            
            # Jeśli nie ma sesji, zaloguj się od nowa
            max_retries = 3
            base_delay = 5.0
            
            for attempt in range(max_retries):
                try:
                    await asyncio.sleep(self.rate_limiter.get_wait_time())
                    
                    self.client = Client()
                    
                    # Wykonaj logowanie w executor (synchroniczne)
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.client.login, self.username, self.password
                    )
                    
                    logger.info(f"Pomyślnie zalogowano do Instagram jako {self.username}")
                    
                    # Zapisz sesję asynchronicznie
                    await self._save_session_async()
                    
                    return self.client
                    
                except (LoginRequired, PleaseWaitFewMinutes, ClientConnectionError) as e:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Błąd logowania (próba {attempt + 1}/{max_retries}): {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Ponowna próba za {delay} sekund")
                        await asyncio.sleep(delay)
                    else:
                        logger.error("Wszystkie próby logowania nieudane")
                        raise
                        
                except Exception as e:
                    logger.error(f"Nieoczekiwany błąd podczas logowania: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(base_delay)
            
            return None
    
    async def publish_post_async(self, image_path: str, caption: str) -> Any:
        """Asynchronicznie publikuje post na Instagram"""
        if not self.client:
            await self.login_async()
            
        if not self.client:
            logger.error("Brak klienta Instagram - nie można opublikować posta")
            return None
        
        try:
            await asyncio.sleep(self.rate_limiter.get_wait_time())
            
            # Sprawdź czy to URL czy lokalna ścieżka
            if image_path.startswith(('http://', 'https://')):
                # Konwertuj Google Drive URL jeśli potrzeba
                if 'drive.google.com' in image_path:
                    image_path = gdrive_to_direct(image_path)
                
                # Pobierz obraz asynchronicznie
                temp_path = await asyncio.get_event_loop().run_in_executor(
                    None, pobierz_i_zapisz_zdjecie, image_path
                )
                
                if not temp_path:
                    logger.error(f"Nie można pobrać obrazu z URL: {image_path}")
                    return None
                    
                image_path = temp_path
            
            # Sprawdź czy plik istnieje
            if not Path(image_path).exists():
                logger.error(f"Nie znaleziono pliku: {image_path}")
                return None
            
            # Przetwórz obraz
            processed_path = await asyncio.get_event_loop().run_in_executor(
                None, przetworz_lokalny_obraz, image_path
            )
            
            try:
                # Publikuj post w executor (synchroniczne)
                media = await asyncio.get_event_loop().run_in_executor(
                    None, self.client.photo_upload, processed_path, caption
                )
                
                logger.info(f"Pomyślnie opublikowano post: {media.pk}")
                return media
                
            finally:
                # Usuń tymczasowy plik jeśli został utworzony
                if processed_path != image_path:
                    try:
                        Path(processed_path).unlink()
                        logger.info(f"Usunięto tymczasowy plik: {processed_path}")
                    except Exception as e:
                        logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")
        
        except (PleaseWaitFewMinutes, RateLimitError, ClientThrottledError) as e:
            logger.warning(f"Instagram wymaga oczekiwania: {e}")
            raise
        except (ClientConnectionError, ConnectionError) as e:
            logger.error(f"Problemy z połączeniem podczas publikacji: {e}")
            raise
        except ClientError as e:
            logger.error(f"Błąd klienta Instagram podczas publikacji: {e}")
            return None
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas publikacji posta: {e}")
            return None


# Globalna instancja menedżera
_async_instagram_manager: Optional[AsyncInstagramManager] = None


def get_async_instagram_manager() -> AsyncInstagramManager:
    """Zwraca globalną instancję asynchronicznego menedżera Instagram"""
    global _async_instagram_manager
    if _async_instagram_manager is None:
        _async_instagram_manager = AsyncInstagramManager(INSTA_USERNAME, INSTA_PASSWORD)
    return _async_instagram_manager


async def async_login_instagram() -> Optional[Client]:
    """Asynchronicznie loguje do Instagram"""
    manager = get_async_instagram_manager()
    return await manager.login_async()


async def async_publish_post(image_path: str, caption: str) -> Any:
    """Asynchronicznie publikuje post na Instagram"""
    manager = get_async_instagram_manager()
    return await manager.publish_post_async(image_path, caption)