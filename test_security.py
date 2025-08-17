#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testy dla modułu security.py
Testuje walidację danych wejściowych i rate limiting
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from security import InputValidator, AdvancedRateLimiter, SecurityManager, ValidationResult


class TestInputValidator(unittest.TestCase):
    """Testy dla klasy InputValidator"""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_validate_instagram_username_valid(self):
        """Test walidacji poprawnej nazwy użytkownika Instagram"""
        result = self.validator.validate_instagram_username("test_user123")
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_instagram_username_invalid(self):
        """Test walidacji niepoprawnej nazwy użytkownika Instagram"""
        # Za długa nazwa
        result = self.validator.validate_instagram_username("a" * 31)
        self.assertFalse(result.is_valid)
        self.assertIn("Nazwa użytkownika musi mieć 1-30 znaków", result.errors[0])
        
        # Nieprawidłowe znaki
        result = self.validator.validate_instagram_username("test@user")
        self.assertFalse(result.is_valid)
        self.assertIn("Nazwa użytkownika może zawierać tylko litery, cyfry, kropki i podkreślenia", result.errors[0])
    
    def test_validate_post_content_valid(self):
        """Test walidacji poprawnej treści posta"""
        content = "To jest testowy post #test"
        result = self.validator.validate_post_content(content)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_post_content_too_long(self):
        """Test walidacji zbyt długiej treści posta"""
        content = "a" * 2201  # Przekracza limit 2200 znaków
        result = self.validator.validate_post_content(content)
        self.assertFalse(result.is_valid)
        self.assertIn("Treść posta jest za długa", result.errors[0])
    
    def test_validate_hashtags_valid(self):
        """Test walidacji poprawnych hashtagów"""
        hashtags = "#test #instagram #python"
        result = self.validator.validate_hashtags(hashtags)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_hashtags_too_many(self):
        """Test walidacji zbyt wielu hashtagów"""
        hashtags = " ".join([f"#tag{i}" for i in range(31)])  # 31 hashtagów
        result = self.validator.validate_hashtags(hashtags)
        self.assertTrue(result.is_valid)  # Walidacja przechodzi, ale jest warning
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("Za dużo hashtagów", result.warnings[0])
    
    def test_validate_image_url_valid(self):
        """Test walidacji poprawnego URL obrazu"""
        url = "https://example.com/image.jpg"
        result = self.validator.validate_image_url(url)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_image_url_invalid(self):
        """Test walidacji niepoprawnego URL obrazu"""
        # Nieprawidłowy protokół
        result = self.validator.validate_image_url("ftp://example.com/image.jpg")
        self.assertFalse(result.is_valid)
        self.assertIn("Nieprawidłowy format URL", result.errors[0])
        
        # Nieprawidłowe rozszerzenie - zwraca warning, nie error
        result = self.validator.validate_image_url("https://example.com/file.txt")
        self.assertTrue(result.is_valid)  # URL jest poprawny, ale może nie wskazywać na obraz
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("URL może nie wskazywać na obraz", result.warnings[0])


class TestAdvancedRateLimiter(unittest.TestCase):
    """Testy dla klasy AdvancedRateLimiter"""
    
    def setUp(self):
        self.rate_limiter = AdvancedRateLimiter(
            calls_per_minute=5,
            calls_per_hour=20,
            burst_limit=3,
            cooldown_period=1
        )
    
    def test_rate_limit_within_limits(self):
        """Test rate limiting w ramach limitów"""
        # Pierwsze wywołania powinny przejść
        for i in range(3):
            can_call, reason = self.rate_limiter.can_make_call()
            self.assertTrue(can_call)
            if can_call:
                self.rate_limiter.record_call()
    
    def test_rate_limit_burst_exceeded(self):
        """Test przekroczenia burst limit"""
        # Przekrocz burst limit
        for i in range(3):
            can_call, reason = self.rate_limiter.can_make_call()
            self.assertTrue(can_call)
            self.rate_limiter.record_call()
        
        # Kolejne wywołanie powinno być zablokowane
        can_call, reason = self.rate_limiter.can_make_call()
        self.assertFalse(can_call)
    
    def test_rate_limit_cooldown(self):
        """Test cooldown po przekroczeniu limitu"""
        # Aktywuj cooldown
        self.rate_limiter.trigger_cooldown("Test cooldown")
        
        # Sprawdź czy cooldown jest aktywny
        can_call, reason = self.rate_limiter.can_make_call()
        self.assertFalse(can_call)
        self.assertIn("Cooldown aktywny", reason)
        
        # Poczekaj na cooldown
        time.sleep(1.1)
        
        # Powinno być dostępne ponownie
        can_call, reason = self.rate_limiter.can_make_call()
        self.assertTrue(can_call)
    
    def test_get_stats(self):
        """Test pobierania statystyk"""
        # Wykonaj kilka wywołań
        for i in range(2):
            can_call, reason = self.rate_limiter.can_make_call()
            if can_call:
                self.rate_limiter.record_call()
        
        stats = self.rate_limiter.get_stats()
        self.assertEqual(stats['calls_last_minute'], 2)
        self.assertEqual(stats['calls_last_hour'], 2)
        self.assertFalse(stats['cooldown_active'])


class TestSecurityManager(unittest.TestCase):
    """Testy dla klasy SecurityManager"""
    
    def setUp(self):
        self.security_manager = SecurityManager()
    
    def test_validate_and_sanitize_post_valid(self):
        """Test walidacji i sanityzacji poprawnego posta"""
        post_data = {
            'tresc_postu': 'Test post content',
            'tagi': '#test #instagram',
            'sciezka_zdjecia': 'https://example.com/image.jpg'
        }
        
        result = self.security_manager.validate_and_sanitize_post(post_data)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_and_sanitize_post_invalid(self):
        """Test walidacji niepoprawnego posta"""
        post_data = {
            'tresc_postu': 'a' * 2201,  # Za długa treść
            'tagi': ' '.join([f'#tag{i}' for i in range(31)]),  # Za dużo tagów
            'sciezka_zdjecia': 'invalid-url'
        }
        
        result = self.security_manager.validate_and_sanitize_post(post_data)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_check_instagram_rate_limit(self):
        """Test sprawdzania rate limit dla Instagram"""
        # Pierwsze wywołania powinny przejść
        for i in range(3):
            self.assertTrue(self.security_manager.check_instagram_rate_limit())
    
    def test_check_google_sheets_rate_limit(self):
        """Test sprawdzania rate limit dla Google Sheets"""
        # Pierwsze wywołania powinny przejść
        for i in range(5):
            self.assertTrue(self.security_manager.check_google_sheets_rate_limit())
    
    def test_report_suspicious_activity(self):
        """Test raportowania podejrzanej aktywności"""
        # Test nie powinien rzucać wyjątku
        try:
            self.security_manager.report_suspicious_activity(
                'test_activity', 
                {'test_key': 'test_value'}
            )
        except Exception as e:
            self.fail(f"report_suspicious_activity raised an exception: {e}")
    
    def test_get_security_status(self):
        """Test pobierania statusu bezpieczeństwa"""
        # Wykonaj kilka operacji
        self.security_manager.check_instagram_rate_limit()
        self.security_manager.check_google_sheets_rate_limit()
        
        status = self.security_manager.get_security_status()
        self.assertIn('instagram_limiter', status)
        self.assertIn('google_sheets_limiter', status)
        self.assertIn('suspicious_activity_count', status)


if __name__ == '__main__':
    print("Uruchamianie testów bezpieczeństwa...")
    unittest.main(verbosity=2)