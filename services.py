"""Serwisy biznesowe dla Instagram Auto Publisher"""

import os
import tempfile
from typing import List, Optional
from datetime import datetime

from config import (
    GOOGLE_SHEET_ID, INSTA_USERNAME, INSTA_PASSWORD, 
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, logger
)
from models import Post, ColumnMapper
from google_sheets import wczytaj_arkusz, znajdz_zdjecie_dla_wiersza
from instagram import zaloguj_instagrama, opublikuj_post
from telegram_bot import wyslij_telegram
from image_utils import pobierz_domyslne_zdjecie


class DataService:
    """Serwis odpowiedzialny za pobieranie i przetwarzanie danych z arkusza"""
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
    
    def get_posts_from_sheet(self) -> List[Post]:
        """Pobiera posty z arkusza i mapuje je na obiekty Post"""
        try:
            logger.info("Pobieranie danych z arkusza...")
            dane = wczytaj_arkusz(self.sheet_id)
            posts = []
            
            for i, row in enumerate(dane):
                post = ColumnMapper.map_row_to_post(row, i)
                if post:
                    posts.append(post)
            
            logger.info(f"Zmapowano {len(posts)} postów z arkusza")
            return posts
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania postów z arkusza: {e}")
            raise
    
    def get_posts_for_today(self) -> List[Post]:
        """Zwraca posty zaplanowane na dzisiaj, które nie zostały jeszcze opublikowane"""
        posts = self.get_posts_from_sheet()
        today_posts = [
            post for post in posts 
            if not post.czy_opublikowano and post.czy_do_publikacji_dzisiaj
        ]
        
        logger.info(f"Znaleziono {len(today_posts)} postów do publikacji na dzisiaj")
        return today_posts


class ImageService:
    """Serwis odpowiedzialny za zarządzanie obrazami"""
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
    
    def resolve_image_path(self, post: Post) -> Optional[str]:
        """Rozwiązuje ścieżkę do obrazu dla posta"""
        sciezka_zdjecia = post.sciezka_zdjecia
        
        # Jeśli brak ścieżki, spróbuj pobrać zdjęcie z arkusza
        if not sciezka_zdjecia:
            logger.info(f"Próbuję pobrać zdjęcie z arkusza dla wiersza {post.row_index + 2}")
            sciezka_zdjecia = znajdz_zdjecie_dla_wiersza(self.sheet_id, post.row_index)
        
        # Jeśli nadal brak zdjęcia, użyj zdjęcia z folderu images
        if not sciezka_zdjecia:
            logger.info(f"Próbuję użyć zdjęcia z folderu images dla wiersza {post.row_index + 2}")
            sciezka_zdjecia = pobierz_domyslne_zdjecie()
        
        if not sciezka_zdjecia:
            logger.warning(f"Brak ścieżki zdjęcia dla wiersza {post.row_index + 2}")
            return None
        
        return sciezka_zdjecia
    
    def prepare_image_for_post(self, post) -> Optional[str]:
        """Przygotowuje zdjęcie dla posta - pobiera z URL lub używa domyślnego"""
        try:
            # Jeśli post ma ścieżkę zdjęcia
            if hasattr(post, 'sciezka_zdjecia') and post.sciezka_zdjecia:
                if post.sciezka_zdjecia.startswith(('http://', 'https://')):
                    # URL - pobierz zdjęcie
                    from image_utils import pobierz_i_zapisz_zdjecie
                    return pobierz_i_zapisz_zdjecie(post.sciezka_zdjecia)
                else:
                    # Lokalna ścieżka - przetwórz obraz
                    from image_utils import przetworz_lokalny_obraz
                    return przetworz_lokalny_obraz(post.sciezka_zdjecia)
            
            # Brak ścieżki - użyj domyślnego zdjęcia
             logger.info("Brak ścieżki zdjęcia - używam domyślnego")
             return self.get_default_image()
             
         except Exception as e:
             logger.error(f"Błąd podczas przygotowywania zdjęcia: {e}")
             # W przypadku błędu, spróbuj użyć domyślnego zdjęcia
             return self.get_default_image()


class NotificationService:
    """Serwis odpowiedzialny za wysyłanie powiadomień"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send_success_notification(self, post: Post, media, image_path: str) -> None:
        """Wysyła powiadomienie o pomyślnej publikacji"""
        try:
            post_url = f"https://www.instagram.com/p/{media.code}/"
            
            message = (
                f"✅ <b>Post opublikowany!</b>\n\n"
                f"📝 Treść: {post.tresc_postu[:100]}{'...' if len(post.tresc_postu) > 100 else ''}\n"
                f"📅 Data: {post.data_publikacji}\n"
                f"🖼️ Zdjęcie: {os.path.basename(image_path)}\n"
                f"🔗 Link: {post_url}"
            )
            
            wyslij_telegram(self.bot_token, self.chat_id, message)
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomienia o sukcesie: {e}")
    
    def send_error_notification(self, post: Post, error: str) -> None:
        """Wysyła powiadomienie o błędzie publikacji"""
        try:
            message = f"❌ Błąd podczas publikacji wiersza {post.row_index + 2}: {error}"
            wyslij_telegram(self.bot_token, self.chat_id, message)
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomienia o błędzie: {e}")
    
    def send_critical_error_notification(self, error: str) -> None:
        """Wysyła powiadomienie o błędzie krytycznym"""
        try:
            message = f"❌ <b>Błąd krytyczny:</b>\n{error}"
            wyslij_telegram(self.bot_token, self.chat_id, message)
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomienia o błędzie krytycznym: {e}")


class PublisherService:
    """Główny serwis odpowiedzialny za publikację postów"""
    
    def __init__(self):
        self.data_service = DataService(GOOGLE_SHEET_ID)
        self.image_service = ImageService(GOOGLE_SHEET_ID)
        self.notification_service = NotificationService(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.instagram_client = None
    
    def login_to_instagram(self) -> None:
        """Loguje się do Instagrama"""
        if not self.instagram_client:
            logger.info("Logowanie do Instagrama...")
            self.instagram_client = zaloguj_instagrama(INSTA_USERNAME, INSTA_PASSWORD)
    
    def publish_post(self, post: Post) -> bool:
        """Publikuje pojedynczy post"""
        try:
            # Rozwiąż ścieżkę do obrazu
            image_path = self.image_service.resolve_image_path(post)
            if not image_path:
                raise Exception("Brak ścieżki do obrazu")
            
            # Publikuj post
            logger.info(f"Publikowanie posta z wiersza {post.row_index + 2}")
            logger.info(f"Zdjęcie: {image_path}")
            logger.info(f"Opis: {post.pelny_opis[:100]}...")
            
            media = opublikuj_post(self.instagram_client, image_path, post.pelny_opis)
            
            # Wyślij powiadomienie o sukcesie
            self.notification_service.send_success_notification(post, media, image_path)
            
            # Usuń tymczasowy plik jeśli został utworzony
            if image_path.startswith(tempfile.gettempdir()):
                try:
                    os.remove(image_path)
                    logger.info(f"Usunięto tymczasowy plik: {image_path}")
                except Exception as e:
                    logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")
            
            logger.info(f"Pomyślnie opublikowano post z wiersza {post.row_index + 2}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas publikacji posta z wiersza {post.row_index + 2}: {e}")
            self.notification_service.send_error_notification(post, str(e))
            return False
    
    def publish_today_posts(self) -> None:
        """Publikuje wszystkie posty zaplanowane na dzisiaj"""
        try:
            posts = self.data_service.get_posts_from_sheet()
            today_posts = [post for post in posts if post.czy_do_publikacji_dzisiaj()]
            
            if not today_posts:
                logger.info("📭 Brak postów do publikacji na dzisiaj")
                return
            
            logger.info(f"📝 Znaleziono {len(today_posts)} postów do publikacji")
            
            for post in today_posts:
                self._publish_single_post(post)
                
        except Exception as e:
            logger.error(f"Błąd podczas publikacji postów: {e}")
            self.notification_service.send_error_notification(
                "Błąd publikacji", str(e)
            )
    
    def _publish_single_post(self, post) -> bool:
        """Publikuje pojedynczy post"""
        try:
            # Zaloguj się do Instagrama jeśli nie jesteś zalogowany
            if not self.login_to_instagram():
                return False
            
            logger.info(f"📝 Publikowanie posta: {post.tresc[:50]}...")
            
            # Pobierz i przygotuj zdjęcie
            image_path = self.image_service.prepare_image_for_post(post)
            if not image_path:
                logger.error("❌ Nie udało się przygotować zdjęcia")
                return False
            
            # Publikuj na Instagramie
            from instagram import opublikuj_post
            post_id, post_url = opublikuj_post(
                self.cl, 
                post.tresc, 
                post.tagi, 
                image_path
            )
            
            if post_id:
                # Wyślij powiadomienie o sukcesie
                self.notification_service.send_success_notification(
                    post.tresc, 
                    image_path, 
                    post_id, 
                    post_url
                )
                logger.info(f"✅ Post opublikowany pomyślnie! ID: {post_id}")
                return True
            else:
                logger.error("❌ Nie udało się opublikować posta")
                return False
                
        except Exception as e:
            logger.error(f"Błąd podczas publikacji posta: {e}")
            self.notification_service.send_error_notification(
                "Błąd publikacji posta", str(e)
            )
            return False
    
    def test_publish_first_post(self) -> bool:
        """Testuje publikację pierwszego dostępnego posta"""
        try:
            posts = self.data_service.get_posts_from_sheet()
            
            if not posts:
                logger.warning("📭 Brak postów w arkuszu")
                return False
            
            # Znajdź pierwszy post, który nie został opublikowany
            unpublished_posts = [post for post in posts if not post.czy_opublikowano]
            
            if not unpublished_posts:
                logger.warning("📭 Wszystkie posty zostały już opublikowane")
                return False
            
            first_post = unpublished_posts[0]
            logger.info(f"🧪 Testowanie publikacji posta: {first_post.tresc[:50]}...")
            
            self._publish_single_post(first_post)
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas testowej publikacji: {e}")
            self.notification_service.send_error_notification(
                "Błąd testowej publikacji", str(e)
            )
            return False