"""Serwisy biznesowe dla Instagram Auto Publisher"""

import os
import tempfile
from typing import List, Optional
from datetime import datetime

from src.config import (
    GOOGLE_SHEET_ID, INSTA_USERNAME, INSTA_PASSWORD, 
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, logger, is_telegram_enabled, log_with_context
)
from src.models import Post, ColumnMapper
from src.integrations.google_sheets import wczytaj_arkusz, znajdz_zdjecie_dla_wiersza
from src.integrations.instagram import zaloguj_instagrama, opublikuj_post
from src.integrations.telegram_bot import wyslij_telegram
from src.utils.image_utils import pobierz_domyslne_zdjecie
from src.utils.security import security_manager, ValidationResult
from src.services.monitoring import metrics_collector


class DataService:
    """Serwis odpowiedzialny za pobieranie i przetwarzanie danych z arkusza"""
    
    def __init__(self, sheet_id: str) -> None:
        self.sheet_id = sheet_id
    
    def get_posts_from_sheet(self) -> List[Post]:
        """Pobiera posty z arkusza Google Sheets z walidacją bezpieczeństwa"""
        try:
            log_with_context('info', 'Pobieranie danych z arkusza', sheet_id=self.sheet_id)
            
            # Sprawdź rate limit dla Google Sheets
            if not security_manager.check_google_sheets_rate_limit():
                log_with_context('warning', 'Google Sheets rate limit exceeded, skipping data fetch')
                metrics_collector.record_api_call('google_sheets', blocked=True)
                return []
            
            # Rejestruj wywołanie API
            metrics_collector.record_api_call('google_sheets')
            
            dane = wczytaj_arkusz(self.sheet_id)
            posts = []
            invalid_posts_count = 0
            
            for i, row in enumerate(dane):
                # Waliduj dane wiersza przed mapowaniem
                validation_result = security_manager.validate_and_sanitize_post(row)
                
                if not validation_result.is_valid:
                    invalid_posts_count += 1
                    log_with_context('warning', 'Invalid post data detected', 
                                   row_index=i, errors=validation_result.errors)
                    continue
                
                # Użyj sanitized data jeśli dostępne
                row_data = validation_result.sanitized_data if validation_result.sanitized_data else row
                
                post = ColumnMapper.map_row_to_post(row_data, i)
                if post:
                    posts.append(post)
            
            log_with_context('info', 'Zmapowano posty z arkusza', 
                           posts_count=len(posts), sheet_id=self.sheet_id,
                           invalid_posts_count=invalid_posts_count)
            return posts
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania postów z arkusza: {e}")
            security_manager.report_suspicious_activity('data_fetch_error', {'error': str(e)})
            raise
    
    def get_posts_for_today(self) -> List[Post]:
        """Zwraca posty zaplanowane na dzisiaj, które nie zostały jeszcze opublikowane"""
        posts = self.get_posts_from_sheet()
        today_posts = [
            post for post in posts 
            if not post.czy_opublikowano and post.czy_do_publikacji_dzisiaj
        ]
        
        log_with_context('info', 'Znaleziono posty do publikacji na dzisiaj', 
                        today_posts_count=len(today_posts), total_posts=len(posts))
        return today_posts


class ImageService:
    """Serwis odpowiedzialny za zarządzanie obrazami"""
    
    def __init__(self, sheet_id: str) -> None:
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
            return pobierz_domyslne_zdjecie()
             
        except Exception as e:
            logger.error(f"Błąd podczas przygotowywania zdjęcia: {e}")
            # W przypadku błędu, spróbuj użyć domyślnego zdjęcia
            return pobierz_domyslne_zdjecie()


class NotificationService:
    """Serwis odpowiedzialny za wysyłanie powiadomień"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_enabled = is_telegram_enabled()
    
    def send_success_notification(self, post: Post, media, image_path: str) -> None:
        """Wysyła powiadomienie o pomyślnej publikacji"""
        if not self.telegram_enabled:
            logger.info("Telegram nie jest skonfigurowany - pomijam powiadomienie")
            return
            
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
        if not self.telegram_enabled:
            logger.info("Telegram nie jest skonfigurowany - pomijam powiadomienie o błędzie")
            return
            
        try:
            message = f"❌ Błąd podczas publikacji wiersza {post.row_index + 2}: {error}"
            wyslij_telegram(self.bot_token, self.chat_id, message)
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomienia o błędzie: {e}")
    
    def send_critical_error_notification(self, error: str) -> None:
        """Wysyła powiadomienie o błędzie krytycznym"""
        if not self.telegram_enabled:
            logger.error("Telegram nie jest skonfigurowany - nie można wysłać powiadomienia o krytycznym błędzie")
            return
            
        try:
            message = f"❌ <b>Błąd krytyczny:</b>\n{error}"
            wyslij_telegram(self.bot_token, self.chat_id, message)
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania powiadomienia o błędzie krytycznym: {e}")


class PublisherService:
    """Główny serwis odpowiedzialny za publikację postów"""
    
    def __init__(self) -> None:
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
        """Publikuje pojedynczy post z zabezpieczeniami"""
        try:
            # Sprawdź rate limit dla Instagram
            if not security_manager.check_instagram_rate_limit():
                log_with_context('warning', 'Instagram rate limit exceeded, skipping post publication',
                               post_row=post.row_index + 2)
                metrics_collector.record_api_call('instagram', blocked=True)
                return False
            
            # Rejestruj wywołanie API
            metrics_collector.record_api_call('instagram')
            
            # Dodatkowa walidacja posta przed publikacją
            validation_result = security_manager.validate_and_sanitize_post({
                'tresc_postu': post.tresc_postu,
                'tagi': post.tagi,
                'sciezka_zdjecia': post.sciezka_zdjecia
            })
            
            if not validation_result.is_valid:
                log_with_context('error', 'Post validation failed before publication',
                               post_row=post.row_index + 2, errors=validation_result.errors)
                security_manager.report_suspicious_activity('invalid_post_publication', 
                                                          {'row': post.row_index, 'errors': validation_result.errors})
                # Rejestruj nieudaną publikację
                post_info = {
                    'content_preview': post.tresc_postu[:50] + '...' if len(post.tresc_postu) > 50 else post.tresc_postu,
                    'image_path': post.sciezka_zdjecia,
                    'tags': post.tagi[:50] + '...' if len(post.tagi) > 50 else post.tagi
                }
                metrics_collector.record_post_failed(post_info, 'Validation failed')
                return False
            
            # Rozwiąż ścieżkę do obrazu
            image_path = self.image_service.resolve_image_path(post)
            if not image_path:
                # Rejestruj nieudaną publikację
                post_info = {
                    'content_preview': post.tresc_postu[:50] + '...' if len(post.tresc_postu) > 50 else post.tresc_postu,
                    'image_path': post.sciezka_zdjecia,
                    'tags': post.tagi[:50] + '...' if len(post.tagi) > 50 else post.tagi
                }
                metrics_collector.record_post_failed(post_info, 'Brak ścieżki do obrazu')
                raise Exception("Brak ścieżki do obrazu")
            
            # Publikuj post
            log_with_context('info', 'Publishing post', 
                           post_row=post.row_index + 2,
                           image_path=image_path,
                           content_length=len(post.pelny_opis))
            
            media = opublikuj_post(self.instagram_client, image_path, post.pelny_opis)
            
            # Wyślij powiadomienie o sukcesie
            self.notification_service.send_success_notification(post, media, image_path)
            
            # Rejestruj udaną publikację
            post_info = {
                'content_preview': post.tresc_postu[:50] + '...' if len(post.tresc_postu) > 50 else post.tresc_postu,
                'image_path': image_path,
                'tags': post.tagi[:50] + '...' if len(post.tagi) > 50 else post.tagi,
                'media_id': media.id if hasattr(media, 'id') else None,
                'media_code': media.code if hasattr(media, 'code') else None
            }
            metrics_collector.record_post_published(post_info)
            
            # Usuń tymczasowy plik jeśli został utworzony
            if image_path.startswith(tempfile.gettempdir()):
                try:
                    os.remove(image_path)
                    log_with_context('info', 'Temporary file removed', file_path=image_path)
                except Exception as e:
                    log_with_context('warning', 'Failed to remove temporary file', 
                                   file_path=image_path, error=str(e))
            
            log_with_context('info', 'Post published successfully', post_row=post.row_index + 2)
            return True
            
        except Exception as e:
            log_with_context('error', 'Post publication failed', 
                           post_row=post.row_index + 2, error=str(e))
            self.notification_service.send_error_notification(post, str(e))
            security_manager.report_suspicious_activity('post_publication_error', 
                                                      {'row': post.row_index, 'error': str(e)})
            # Rejestruj nieudaną publikację
            post_info = {
                'content_preview': post.tresc_postu[:50] + '...' if len(post.tresc_postu) > 50 else post.tresc_postu,
                'image_path': post.sciezka_zdjecia,
                'tags': post.tagi[:50] + '...' if len(post.tagi) > 50 else post.tagi
            }
            metrics_collector.record_post_failed(post_info, str(e))
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
    
    def _publish_single_post(self, post: Post) -> bool:
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