import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.config import logger, GOOGLE_API_KEY, GOOGLE_SHEET_ID
from src.utils.security import InputValidator, ValidationResult
from src.utils import RateLimiter


class AsyncGoogleSheetsClient:
    """Asynchroniczny klient dla Google Sheets API"""
    
    def __init__(self, api_key: str, sheet_id: str):
        self.api_key = api_key
        self.sheet_id = sheet_id
        self.base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values"
        self.rate_limiter = RateLimiter(calls_per_minute=100)  # Google Sheets API limit
        self.validator = InputValidator()
        
    async def _make_request(self, session: aiohttp.ClientSession, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje asynchroniczne żądanie do Google Sheets API"""
        await asyncio.sleep(self.rate_limiter.get_wait_time())
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Pomyślnie pobrano dane z Google Sheets: {len(data.get('values', []))} wierszy")
                    return data
                elif response.status == 429:
                    logger.warning("Rate limit przekroczony dla Google Sheets API")
                    await asyncio.sleep(60)  # Czekaj minutę
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Błąd API Google Sheets: {response.status} - {error_text}")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
        except asyncio.TimeoutError:
            logger.error("Timeout podczas pobierania danych z Google Sheets")
            raise
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas żądania do Google Sheets: {e}")
            raise
    
    async def validate_and_sanitize_sheet_data(self, data: List[List[str]]) -> List[List[str]]:
        """Asynchronicznie waliduje i sanityzuje dane z arkusza"""
        sanitized_data = []
        
        for row_idx, row in enumerate(data):
            if not row or all(not cell.strip() for cell in row):
                continue  # Pomiń puste wiersze
                
            sanitized_row = []
            for cell in row:
                if isinstance(cell, str):
                    # Usuń niebezpieczne znaki
                    sanitized_cell = cell.replace('\x00', '').strip()
                    # Ogranicz długość
                    if len(sanitized_cell) > 1000:
                        sanitized_cell = sanitized_cell[:1000]
                        logger.warning(f"Skrócono zawartość komórki w wierszu {row_idx + 1}")
                    sanitized_row.append(sanitized_cell)
                else:
                    sanitized_row.append(str(cell) if cell is not None else '')
            
            sanitized_data.append(sanitized_row)
            
            # Yield control periodically for large datasets
            if row_idx % 100 == 0:
                await asyncio.sleep(0)
        
        logger.info(f"Zwalidowano i zsanityzowano {len(sanitized_data)} wierszy danych")
        return sanitized_data
    
    async def fetch_sheet_data(self, range_name: str = "A:Z") -> List[List[str]]:
        """Asynchronicznie pobiera dane z arkusza Google Sheets"""
        url = f"{self.base_url}/{range_name}"
        params = {
            'key': self.api_key,
            'valueRenderOption': 'UNFORMATTED_VALUE',
            'dateTimeRenderOption': 'FORMATTED_STRING'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                response_data = await self._make_request(session, url, params)
                raw_data = response_data.get('values', [])
                
                if not raw_data:
                    logger.warning("Arkusz Google Sheets jest pusty")
                    return []
                
                # Walidacja i sanityzacja danych
                sanitized_data = await self.validate_and_sanitize_sheet_data(raw_data)
                
                logger.info(f"Pomyślnie pobrano {len(sanitized_data)} wierszy z Google Sheets")
                return sanitized_data
                
            except aiohttp.ClientResponseError as e:
                if e.status == 403:
                    logger.error("Brak uprawnień do Google Sheets API - sprawdź klucz API")
                elif e.status == 404:
                    logger.error(f"Nie znaleziono arkusza o ID: {self.sheet_id}")
                else:
                    logger.error(f"Błąd HTTP podczas pobierania arkusza: {e.status}")
                raise
            except Exception as e:
                logger.error(f"Nieoczekiwany błąd podczas pobierania arkusza: {e}")
                raise


# Globalna instancja klienta
_async_client: Optional[AsyncGoogleSheetsClient] = None


def get_async_google_sheets_client() -> AsyncGoogleSheetsClient:
    """Zwraca globalną instancję asynchronicznego klienta Google Sheets"""
    global _async_client
    if _async_client is None:
        _async_client = AsyncGoogleSheetsClient(GOOGLE_API_KEY, GOOGLE_SHEET_ID)
    return _async_client


async def async_wczytaj_arkusz(range_name: str = "A:Z") -> List[List[str]]:
    """Asynchronicznie wczytuje arkusz Google Sheets"""
    client = get_async_google_sheets_client()
    return await client.fetch_sheet_data(range_name)