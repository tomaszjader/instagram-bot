import time
import json
import hashlib
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from src.config import logger


class CacheEntry:
    """Reprezentuje pojedynczy wpis w cache"""
    
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Sprawdza czy wpis wygasł"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def access(self) -> Any:
        """Oznacza dostęp do wpisu i zwraca dane"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje wpis do słownika dla serializacji"""
        return {
            'data': self.data,
            'created_at': self.created_at,
            'ttl_seconds': self.ttl_seconds,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Tworzy wpis z słownika"""
        entry = cls(data['data'], data['ttl_seconds'])
        entry.created_at = data['created_at']
        entry.access_count = data['access_count']
        entry.last_accessed = data['last_accessed']
        return entry


class GoogleSheetsCache:
    """Cache dla danych z Google Sheets z persistence na dysku"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._load_from_disk()
    
    def _generate_key(self, sheet_id: str, range_name: str = "A:Z") -> str:
        """Generuje unikalny klucz dla cache"""
        key_string = f"{sheet_id}:{range_name}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file_path(self, key: str) -> Path:
        """Zwraca ścieżkę do pliku cache dla danego klucza"""
        return self.cache_dir / f"{key}.json"
    
    def _load_from_disk(self) -> None:
        """Ładuje cache z dysku do pamięci"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    key = cache_file.stem
                    entry = CacheEntry.from_dict(cache_data)
                    
                    # Sprawdź czy wpis nie wygasł
                    if not entry.is_expired():
                        self._memory_cache[key] = entry
                    else:
                        # Usuń wygasły plik
                        cache_file.unlink()
                        
                except Exception as e:
                    logger.warning(f"Nie można załadować cache z pliku {cache_file}: {e}")
                    # Usuń uszkodzony plik
                    try:
                        cache_file.unlink()
                    except Exception:
                        pass
                        
            logger.info(f"Załadowano {len(self._memory_cache)} wpisów cache z dysku")
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania cache z dysku: {e}")
    
    def _save_to_disk(self, key: str, entry: CacheEntry) -> None:
        """Zapisuje wpis cache na dysk"""
        try:
            cache_file = self._get_cache_file_path(key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Nie można zapisać cache na dysk: {e}")
    
    def get(self, sheet_id: str, range_name: str = "A:Z") -> Optional[List[List[str]]]:
        """Pobiera dane z cache"""
        key = self._generate_key(sheet_id, range_name)
        
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            
            if entry.is_expired():
                # Usuń wygasły wpis
                self._remove(key)
                return None
            
            logger.debug(f"Cache hit dla {sheet_id}:{range_name}")
            return entry.access()
        
        logger.debug(f"Cache miss dla {sheet_id}:{range_name}")
        return None
    
    def set(self, sheet_id: str, data: List[List[str]], range_name: str = "A:Z", ttl: Optional[int] = None) -> None:
        """Zapisuje dane do cache"""
        key = self._generate_key(sheet_id, range_name)
        ttl = ttl or self.default_ttl
        
        entry = CacheEntry(data, ttl)
        self._memory_cache[key] = entry
        
        # Zapisz na dysk asynchronicznie (w tle)
        try:
            self._save_to_disk(key, entry)
            logger.debug(f"Zapisano do cache: {sheet_id}:{range_name} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania cache: {e}")
    
    def _remove(self, key: str) -> None:
        """Usuwa wpis z cache (pamięć i dysk)"""
        # Usuń z pamięci
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        # Usuń z dysku
        try:
            cache_file = self._get_cache_file_path(key)
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Nie można usunąć pliku cache: {e}")
    
    def invalidate(self, sheet_id: str, range_name: str = "A:Z") -> None:
        """Unieważnia wpis w cache"""
        key = self._generate_key(sheet_id, range_name)
        self._remove(key)
        logger.info(f"Unieważniono cache dla {sheet_id}:{range_name}")
    
    def clear_expired(self) -> int:
        """Usuwa wszystkie wygasłe wpisy z cache"""
        expired_keys = []
        
        for key, entry in self._memory_cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove(key)
        
        logger.info(f"Usunięto {len(expired_keys)} wygasłych wpisów cache")
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki cache"""
        total_entries = len(self._memory_cache)
        expired_entries = sum(1 for entry in self._memory_cache.values() if entry.is_expired())
        total_accesses = sum(entry.access_count for entry in self._memory_cache.values())
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'total_accesses': total_accesses,
            'cache_dir': str(self.cache_dir),
            'default_ttl': self.default_ttl
        }
    
    def cleanup(self) -> None:
        """Czyści cache i usuwa wszystkie pliki"""
        # Wyczyść pamięć
        self._memory_cache.clear()
        
        # Usuń wszystkie pliki cache
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache został wyczyszczony")
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia cache: {e}")


# Globalna instancja cache
_google_sheets_cache: Optional[GoogleSheetsCache] = None


def get_google_sheets_cache() -> GoogleSheetsCache:
    """Zwraca globalną instancję cache dla Google Sheets"""
    global _google_sheets_cache
    if _google_sheets_cache is None:
        _google_sheets_cache = GoogleSheetsCache()
    return _google_sheets_cache