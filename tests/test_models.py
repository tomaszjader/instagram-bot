import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, date
from src.models import Post, ColumnMapper


class TestPost(unittest.TestCase):
    """Testy dla klasy Post"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        self.post_data = {
            'row_index': 1,
            'data_publikacji': date(2024, 1, 15),
            'tresc_postu': 'Test post content',
            'tagi': '#test #unittest',
            'sciezka_zdjecia': 'images/test.jpg',
            'czy_opublikowano': False,
            'raw_data': {'col1': 'value1', 'col2': 'value2'}
        }
        self.post = Post(**self.post_data)
    
    def test_post_creation(self):
        """Test tworzenia obiektu Post"""
        self.assertEqual(self.post.row_index, 1)
        self.assertEqual(self.post.data_publikacji, date(2024, 1, 15))
        self.assertEqual(self.post.tresc_postu, 'Test post content')
        self.assertEqual(self.post.tagi, '#test #unittest')
        self.assertEqual(self.post.sciezka_zdjecia, 'images/test.jpg')
        self.assertFalse(self.post.czy_opublikowano)
    
    def test_pelny_opis(self):
        """Test właściwości pelny_opis"""
        description = self.post.pelny_opis
        self.assertIn('Test post content', description)
        self.assertIn('#test #unittest', description)
    
    def test_czy_do_publikacji_dzisiaj_true(self):
        """Test sprawdzania czy post jest zaplanowany na dzisiaj - pozytywny"""
        today_post = Post(
            row_index=1,
            data_publikacji=date.today(),
            tresc_postu='Today post',
            tagi='#today',
            sciezka_zdjecia='test.jpg',
            czy_opublikowano=False,
            raw_data={}
        )
        self.assertTrue(today_post.czy_do_publikacji_dzisiaj)
    
    def test_czy_do_publikacji_dzisiaj_false(self):
        """Test sprawdzania czy post jest zaplanowany na dzisiaj - negatywny"""
        self.assertFalse(self.post.czy_do_publikacji_dzisiaj)
    
    def test_czy_do_publikacji_dzisiaj_no_date(self):
        """Test sprawdzania czy post jest zaplanowany na dzisiaj - brak daty"""
        no_date_post = Post(
            row_index=1,
            data_publikacji=None,
            tresc_postu='No date post',
            tagi='#nodate',
            sciezka_zdjecia='test.jpg',
            czy_opublikowano=False,
            raw_data={}
        )
        self.assertFalse(no_date_post.czy_do_publikacji_dzisiaj)


class TestColumnMapper(unittest.TestCase):
    """Testy dla klasy ColumnMapper"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        pass  # ColumnMapper używa tylko metod klasowych
    
    def test_find_value_by_keys_found(self):
        """Test znajdowania wartości po kluczach - znaleziono"""
        row_data = {
            'data_publikacji': '2024-01-15',
            'tresc_postu': 'Test content',
            'tagi': '#test'
        }
        possible_keys = ['data_publikacji', 'data', 'date']
        result = ColumnMapper.find_value_by_keys(row_data, possible_keys)
        self.assertEqual(result, '2024-01-15')
    
    def test_find_value_by_keys_not_found(self):
        """Test znajdowania wartości po kluczach - nie znaleziono"""
        row_data = {
            'tresc_postu': 'Test content',
            'tagi': '#test'
        }
        possible_keys = ['data_publikacji', 'data', 'date']
        result = ColumnMapper.find_value_by_keys(row_data, possible_keys)
        self.assertEqual(result, '')
    
    def test_map_row_to_post(self):
        """Test mapowania wiersza na obiekt Post"""
        row_data = {
            'data_publikacji': '2024-01-15',
            'tresc_postu': 'Test post content',
            'tagi': '#test #unittest',
            'sciezka_zdjecia': 'images/test.jpg',
            'czy_opublikowano': 'FALSE'
        }
        
        post = ColumnMapper.map_row_to_post(row_data, 1)
        
        self.assertIsNotNone(post)
        self.assertEqual(post.row_index, 1)
        self.assertEqual(post.tresc_postu, 'Test post content')
        self.assertEqual(post.tagi, '#test #unittest')
        self.assertEqual(post.sciezka_zdjecia, 'images/test.jpg')
        self.assertFalse(post.czy_opublikowano)
        self.assertEqual(post.raw_data, row_data)


if __name__ == '__main__':
    unittest.main()