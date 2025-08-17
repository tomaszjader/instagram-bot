import unittest
from datetime import datetime
from unittest.mock import patch, Mock
from google_sheets import parsuj_date_value, gdrive_to_direct


class TestDateParsing(unittest.TestCase):
    """Testy dla funkcji parsowania dat"""
    
    def test_parsuj_date_value_none(self):
        """Test parsowania wartości None"""
        result = parsuj_date_value(None)
        self.assertIsNone(result)
    
    def test_parsuj_date_value_empty_string(self):
        """Test parsowania pustego stringa"""
        result = parsuj_date_value('')
        self.assertIsNone(result)
    
    def test_parsuj_date_value_serial_number(self):
        """Test parsowania numeru seryjnego Excel (45292 = 2024-01-01)"""
        result = parsuj_date_value(45292)
        expected = datetime(2024, 1, 1)
        if hasattr(result, 'date'):
            self.assertEqual(result.date(), expected.date())
        else:
            self.assertEqual(result, expected.date())
    
    def test_parsuj_date_value_iso_format(self):
        """Test parsowania daty w formacie ISO (YYYY-MM-DD)"""
        result = parsuj_date_value('2024-01-15')
        expected = datetime(2024, 1, 15)
        if hasattr(result, 'date'):
            self.assertEqual(result.date(), expected.date())
        else:
            self.assertEqual(result, expected.date())
    
    def test_parsuj_date_value_polish_format(self):
        """Test parsowania daty w formacie polskim (DD.MM.YYYY)"""
        result = parsuj_date_value('15.01.2024')
        expected = datetime(2024, 1, 15)
        if hasattr(result, 'date'):
            self.assertEqual(result.date(), expected.date())
        else:
            self.assertEqual(result, expected.date())
    
    def test_parsuj_date_value_us_format(self):
        """Test parsowania daty w formacie amerykańskim (MM/DD/YYYY)"""
        result = parsuj_date_value('01/15/2024')
        expected = datetime(2024, 1, 15)
        if hasattr(result, 'date'):
            self.assertEqual(result.date(), expected.date())
        else:
            self.assertEqual(result, expected.date())
    
    def test_parsuj_date_value_with_time(self):
        """Test parsowania daty z czasem"""
        result = parsuj_date_value('2024-01-15 14:30:00')
        expected = datetime(2024, 1, 15, 14, 30, 0)
        # parsuj_date_value może zwracać tylko datę bez czasu
        if hasattr(result, 'date'):
            self.assertEqual(result.date(), expected.date())
        else:
            self.assertEqual(result, expected.date())
    
    def test_parsuj_date_value_invalid_format(self):
        """Test parsowania nieprawidłowego formatu daty"""
        result = parsuj_date_value('invalid-date')
        self.assertIsNone(result)
    
    def test_parsuj_date_value_float_serial(self):
        """Test parsowania liczby zmiennoprzecinkowej jako numer seryjny"""
        result = parsuj_date_value(45292.5)  # 2024-01-01 12:00:00
        expected = datetime(2024, 1, 1, 12, 0, 0)
        if hasattr(result, 'date'):
            self.assertEqual(result.date(), expected.date())
            if hasattr(result, 'hour'):
                self.assertEqual(result.hour, expected.hour)
        else:
            self.assertEqual(result, expected.date())


class TestGoogleDriveUtils(unittest.TestCase):
    """Testy dla funkcji pomocniczych Google Drive"""
    
    def test_gdrive_to_direct_valid_url(self):
        """Test konwersji prawidłowego URL Google Drive"""
        gdrive_url = 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view'
        expected = 'https://drive.google.com/uc?export=download&id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        result = gdrive_to_direct(gdrive_url)
        self.assertEqual(result, expected)
    
    def test_gdrive_to_direct_invalid_url(self):
        """Test konwersji nieprawidłowego URL Google Drive"""
        invalid_url = 'https://example.com/invalid-url'
        result = gdrive_to_direct(invalid_url)
        self.assertEqual(result, invalid_url)  # Powinien zwrócić oryginalny URL
    
    def test_gdrive_to_direct_already_direct(self):
        """Test konwersji już bezpośredniego URL"""
        direct_url = 'https://drive.google.com/uc?export=download&id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        result = gdrive_to_direct(direct_url)
        # Jeśli URL nie zawiera /d/, powinien zostać zwrócony bez zmian
        self.assertEqual(result, direct_url)


if __name__ == '__main__':
    unittest.main()