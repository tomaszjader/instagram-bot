"""Narzędzia pomocnicze dla Instagram Auto Publisher"""

import time
import random
from typing import Callable, Any, Optional, Type, Union
from functools import wraps
from config import logger


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Dekorator implementujący retry mechanism z exponential backoff
    
    Args:
        max_retries: Maksymalna liczba prób
        base_delay: Podstawowe opóźnienie w sekundach
        max_delay: Maksymalne opóźnienie w sekundach
        backoff_factor: Współczynnik zwiększania opóźnienia
        jitter: Czy dodawać losowe opóźnienie
        exceptions: Tuple wyjątków, które powinny być retry'owane
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Funkcja {func.__name__} nie powiodła się po {max_retries + 1} próbach: {e}")
                        raise e
                    
                    # Oblicz opóźnienie z exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    # Dodaj jitter jeśli włączony
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Próba {attempt + 1}/{max_retries + 1} funkcji {func.__name__} nie powiodła się: {e}. "
                        f"Ponowna próba za {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            # To nie powinno się nigdy wykonać, ale dla bezpieczeństwa
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_api_call(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    **kwargs: Any
) -> Any:
    """
    Funkcja pomocnicza do retry API calls bez użycia dekoratora
    
    Args:
        func: Funkcja do wykonania
        *args: Argumenty pozycyjne dla funkcji
        max_retries: Maksymalna liczba prób
        base_delay: Podstawowe opóźnienie
        exceptions: Wyjątki do retry
        **kwargs: Argumenty nazwane dla funkcji
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"API call {func.__name__} nie powiódł się po {max_retries + 1} próbach: {e}")
                raise e
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"API call {func.__name__} próba {attempt + 1} nie powiodła się: {e}. Retry za {delay}s")
            time.sleep(delay)
    
    if last_exception:
        raise last_exception


class RateLimiter:
    """
    Prosty rate limiter dla API calls
    """
    
    def __init__(self, calls_per_minute: int = 60) -> None:
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call_time = 0.0
    
    def wait_if_needed(self) -> None:
        """
        Czeka jeśli potrzeba, aby nie przekroczyć rate limit
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            sleep_time = self.min_interval - time_since_last_call
            logger.debug(f"Rate limiting: czekam {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()


# Globalne instancje rate limiterów
instagram_rate_limiter = RateLimiter(calls_per_minute=30)  # Instagram ma ograniczenia
google_sheets_rate_limiter = RateLimiter(calls_per_minute=100)  # Google Sheets API