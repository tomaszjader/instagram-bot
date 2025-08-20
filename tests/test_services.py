import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import os
import sys
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models import Post
from src.services import DataService, ImageService, NotificationService, PublisherService


class TestDataService(unittest.TestCase):
    """Testy dla klasy DataService"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        self.data_service = DataService('test_sheet_id')
    
    @patch('services.wczytaj_arkusz')
    def test_get_posts_success(self, mock_wczytaj_arkusz):
        """Test pomyślnego pobierania postów"""
        # Mock danych z arkusza
        mock_data = [
            {
                'data_publikacji': '2024-01-15',
                'tresc_postu': 'Test content',
                'tagi': '#test',
                'sciezka_zdjecia': 'test.jpg',
                'czy_opublikowano': 'FALSE'
            }
        ]
        mock_wczytaj_arkusz.return_value = mock_data
        
        posts = self.data_service.get_posts_from_sheet()
        
        self.assertEqual(len(posts), 1)
        self.assertIsInstance(posts[0], Post)
        mock_wczytaj_arkusz.assert_called_once_with('test_sheet_id')
    
    @patch('services.wczytaj_arkusz')
    def test_get_posts_empty_data(self, mock_wczytaj_arkusz):
        """Test pobierania postów z pustymi danymi"""
        mock_wczytaj_arkusz.return_value = []
        
        posts = self.data_service.get_posts_from_sheet()
        
        self.assertEqual(len(posts), 0)
        self.assertIsInstance(posts, list)


class TestImageService(unittest.TestCase):
    """Testy dla klasy ImageService"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        self.image_service = ImageService('test_sheet_id')
    
    def test_resolve_image_path(self):
        """Test rozwiązywania ścieżki do obrazu"""
        test_post = Post(
            row_index=0,
            data_publikacji=date.today(),
            tresc_postu='Test',
            tagi='#test',
            sciezka_zdjecia='test.jpg',
            czy_opublikowano=False,
            raw_data={}
        )
        image_path = self.image_service.resolve_image_path(test_post)
        self.assertEqual(image_path, 'test.jpg')
    
    @patch('image_utils.pobierz_i_zapisz_zdjecie')
    def test_prepare_image_for_post_url(self, mock_pobierz):
        """Test przygotowania obrazu z URL"""
        mock_pobierz.return_value = '/tmp/test_image.jpg'
        
        # Tworzenie mock posta z URL
        mock_post = Mock()
        mock_post.sciezka_zdjecia = 'https://example.com/image.jpg'
        
        result = self.image_service.prepare_image_for_post(mock_post)
        
        self.assertEqual(result, '/tmp/test_image.jpg')
        mock_pobierz.assert_called_once_with('https://example.com/image.jpg')
    
    @patch('image_utils.przetworz_lokalny_obraz')
    def test_prepare_image_for_post_local_file(self, mock_przetworz):
        """Test przygotowania lokalnego pliku obrazu"""
        mock_przetworz.return_value = 'processed_image.jpg'
        
        # Tworzenie mock posta z lokalną ścieżką
        mock_post = Mock()
        mock_post.sciezka_zdjecia = 'local_image.jpg'
        
        result = self.image_service.prepare_image_for_post(mock_post)
        
        self.assertEqual(result, 'processed_image.jpg')
        mock_przetworz.assert_called_once_with('local_image.jpg')
    
    def test_prepare_image_for_post_no_image(self):
        """Test przygotowania obrazu gdy brak ścieżki"""
        # Tworzenie mock posta bez ścieżki zdjęcia
        mock_post = Mock()
        mock_post.sciezka_zdjecia = None
        
        result = self.image_service.prepare_image_for_post(mock_post)
        
        self.assertTrue(result.endswith('images\\default.jpg') or result.endswith('images/default.jpg'))


class TestNotificationService(unittest.TestCase):
    """Testy dla klasy NotificationService"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        self.notification_service = NotificationService('test_token', 'test_chat_id')
        self.test_post = Post(
            row_index=1,
            data_publikacji=date(2024, 1, 15),
            tresc_postu='Test content',
            tagi='#test',
            sciezka_zdjecia='test.jpg',
            czy_opublikowano=False,
            raw_data={}
        )
    
    @patch('services.wyslij_telegram')
    def test_notification_service_disabled(self, mock_wyslij):
        """Test serwisu powiadomień gdy Telegram jest wyłączony"""
        # Ustawiamy telegram_enabled na False
        self.notification_service.telegram_enabled = False
        
        # Powiadomienia nie powinny być wysyłane
        mock_media = Mock()
        mock_media.code = 'ABC123'
        self.notification_service.send_success_notification(self.test_post, mock_media, 'test.jpg')
        mock_wyslij.assert_not_called()
    
    @patch('services.wyslij_telegram')
    def test_send_success_notification(self, mock_wyslij):
        """Test wysyłania powiadomienia o sukcesie"""
        # Ustawiamy wszystkie potrzebne atrybuty
        self.notification_service.telegram_enabled = True
        self.notification_service.bot_token = 'test_token'
        self.notification_service.chat_id = 'test_chat_id'
        mock_media = Mock()
        mock_media.code = 'ABC123'
        
        self.notification_service.send_success_notification(
            self.test_post, mock_media, 'test_image.jpg'
        )
        
        mock_wyslij.assert_called_once()
    
    @patch('services.wyslij_telegram')
    def test_send_error_notification(self, mock_wyslij):
        """Test wysyłania powiadomienia o błędzie"""
        # Ustawiamy wszystkie potrzebne atrybuty
        self.notification_service.telegram_enabled = True
        self.notification_service.bot_token = 'test_token'
        self.notification_service.chat_id = 'test_chat_id'
        
        self.notification_service.send_error_notification(
            self.test_post, 'Test error message'
        )
        
        mock_wyslij.assert_called_once()


class TestPublisherService(unittest.TestCase):
    """Testy dla klasy PublisherService"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        with patch('services.GOOGLE_SHEET_ID', 'test_sheet'):
            self.publisher_service = PublisherService()
        
        self.test_post = Post(
            row_index=1,
            data_publikacji=date.today(),
            tresc_postu='Test content',
            tagi='#test',
            sciezka_zdjecia='test.jpg',
            czy_opublikowano=False,
            raw_data={}
        )
    
    @patch('services.PublisherService._publish_single_post')
    @patch('services.DataService.get_posts_from_sheet')
    def test_publish_scheduled_posts_success(self, mock_get_posts, mock_publish):
        """Test pomyślnej publikacji zaplanowanych postów"""
        mock_post = Mock()
        mock_post.czy_do_publikacji_dzisiaj.return_value = True
        mock_get_posts.return_value = [mock_post]
        mock_publish.return_value = True
        
        self.publisher_service.publish_today_posts()  # Metoda nie zwraca wartości
        
        mock_get_posts.assert_called_once()
        mock_publish.assert_called_once_with(mock_post)
    
    @patch('services.DataService.get_posts_from_sheet')
    def test_publish_scheduled_posts_no_posts(self, mock_get_posts):
        """Test publikacji gdy brak postów na dzisiaj"""
        mock_get_posts.return_value = []
        
        self.publisher_service.publish_today_posts()  # Metoda nie zwraca wartości
        
        mock_get_posts.assert_called_once()


if __name__ == '__main__':
    unittest.main()