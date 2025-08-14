"""Modele danych i klasy dla Instagram Auto Publisher"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict, Any
from config import logger
from google_sheets import parsuj_date_value


@dataclass
class Post:
    """Model reprezentujący post do publikacji"""
    row_index: int
    data_publikacji: Optional[date]
    tresc_postu: str
    tagi: str
    sciezka_zdjecia: str
    czy_opublikowano: bool
    raw_data: Dict[str, Any]
    
    @property
    def pelny_opis(self) -> str:
        """Zwraca pełny opis posta z tagami"""
        opis = self.tresc_postu
        if self.tagi and self.tagi.strip() and self.tagi != 'nan':
            opis += f"\n\n{self.tagi}"
        return opis
    
    @property
    def czy_do_publikacji_dzisiaj(self) -> bool:
        """Sprawdza czy post ma być opublikowany dzisiaj"""
        if not self.data_publikacji:
            return False
        return self.data_publikacji == datetime.now().date()
    
    def __str__(self) -> str:
        return f"Post(wiersz={self.row_index}, data={self.data_publikacji}, treść='{self.tresc_postu[:50]}...')"


class ColumnMapper:
    """Klasa odpowiedzialna za mapowanie kolumn arkusza na pola modelu"""
    
    # Możliwe nazwy kolumn dla różnych pól
    CONTENT_KEYS = ['tresc_postu', 'treść_postu', 'content', 'tekst', 'opis']
    TAGS_KEYS = ['tagi', 'tags', 'hashtags', 'hash']
    IMAGE_KEYS = ['sciezka_zdjecia', 'ścieżka_zdjęcia', 'image', 'zdjecie', 'photo', 'path']
    DATE_KEYS = ['data_publikacji', 'data', 'date', 'publikacja']
    PUBLISHED_KEYS = ['czy_opublikowano', 'opublikowano', 'published', 'status']
    
    @classmethod
    def find_value_by_keys(cls, row: Dict[str, Any], possible_keys: list) -> str:
        """Znajduje wartość w wierszu na podstawie możliwych nazw kluczy"""
        for key in possible_keys:
            if key in row and row[key] and str(row[key]).strip() and str(row[key]).strip() != 'nan':
                return str(row[key]).strip()
        return ''
    
    @classmethod
    def map_row_to_post(cls, row: Dict[str, Any], row_index: int) -> Optional[Post]:
        """Mapuje wiersz arkusza na obiekt Post"""
        try:
            # Znajdź wartości dla każdego pola
            tresc_postu = cls.find_value_by_keys(row, cls.CONTENT_KEYS)
            tagi = cls.find_value_by_keys(row, cls.TAGS_KEYS)
            sciezka_zdjecia = cls.find_value_by_keys(row, cls.IMAGE_KEYS)
            date_value = cls.find_value_by_keys(row, cls.DATE_KEYS)
            published_value = cls.find_value_by_keys(row, cls.PUBLISHED_KEYS)
            
            # Parsuj datę
            data_publikacji = None
            if date_value:
                data_publikacji = parsuj_date_value(date_value)
            
            # Sprawdź status publikacji
            czy_opublikowano = published_value.lower() in ['true', 'tak', '1', 'yes']
            
            # Walidacja - wymagana treść posta
            if not tresc_postu:
                logger.warning(f"Brak treści posta dla wiersza {row_index + 2}")
                return None
            
            return Post(
                row_index=row_index,
                data_publikacji=data_publikacji,
                tresc_postu=tresc_postu,
                tagi=tagi,
                sciezka_zdjecia=sciezka_zdjecia,
                czy_opublikowano=czy_opublikowano,
                raw_data=row
            )
            
        except Exception as e:
            logger.error(f"Błąd podczas mapowania wiersza {row_index + 2}: {e}")
            return None
    
    @classmethod
    def log_mapping_debug(cls, post: Post) -> None:
        """Loguje informacje debug o mapowaniu"""
        logger.info(f"DEBUG - Wiersz {post.row_index + 2}:")
        logger.info(f"  data_publikacji: {post.data_publikacji}")
        logger.info(f"  tresc_postu: '{post.tresc_postu}'")
        logger.info(f"  tagi: '{post.tagi}'")
        logger.info(f"  sciezka_zdjecia: '{post.sciezka_zdjecia}'")
        logger.info(f"  Wszystkie klucze: {list(post.raw_data.keys())}")
        logger.info(f"  Wszystkie wartości: {list(post.raw_data.values())}")