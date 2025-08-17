#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł bezpieczeństwa dla Instagram Auto Publisher
Zawiera walidację danych wejściowych, rate limiting i inne funkcje bezpieczeństwa
"""

import re
import time
import hashlib
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urlparse
from config import logger, log_with_context


@dataclass
class ValidationResult:
    """Wynik walidacji danych"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_data: Optional[Dict[str, Any]] = None


class InputValidator:
    """Klasa do walidacji danych wejściowych"""
    
    # Wzorce regex dla walidacji
    INSTAGRAM_USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._]{1,30}$')
    HASHTAG_PATTERN = re.compile(r'^#[a-zA-Z0-9_]+$')
    URL_PATTERN = re.compile(
        r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    )
    
    # Maksymalne długości
    MAX_POST_CONTENT_LENGTH = 2200  # Instagram limit
    MAX_HASHTAGS_COUNT = 30  # Instagram limit
    MAX_IMAGE_URL_LENGTH = 2048
    
    # Zabronione słowa/frazy (przykład)
    FORBIDDEN_WORDS = {
        'spam', 'fake', 'bot', 'automation', 'follow4follow', 'like4like'
    }
    
    @staticmethod
    def validate_instagram_username(username: str) -> ValidationResult:
        """Waliduje nazwę użytkownika Instagram"""
        errors = []
        warnings = []
        
        if not username or not isinstance(username, str):
            errors.append("Nazwa użytkownika nie może być pusta")
            return ValidationResult(False, errors, warnings)
        
        username = username.strip()
        
        if len(username) < 1 or len(username) > 30:
            errors.append("Nazwa użytkownika musi mieć 1-30 znaków")
        
        if not InputValidator.INSTAGRAM_USERNAME_PATTERN.match(username):
            errors.append("Nazwa użytkownika może zawierać tylko litery, cyfry, kropki i podkreślenia")
        
        if username.startswith('.') or username.endswith('.'):
            errors.append("Nazwa użytkownika nie może zaczynać się ani kończyć kropką")
        
        if '..' in username:
            errors.append("Nazwa użytkownika nie może zawierać dwóch kropek pod rząd")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={'username': username}
        )
    
    @staticmethod
    def validate_post_content(content: str) -> ValidationResult:
        """Waliduje treść posta"""
        errors = []
        warnings = []
        
        if not content or not isinstance(content, str):
            errors.append("Treść posta nie może być pusta")
            return ValidationResult(False, errors, warnings)
        
        content = content.strip()
        
        if len(content) > InputValidator.MAX_POST_CONTENT_LENGTH:
            errors.append(f"Treść posta jest za długa ({len(content)} > {InputValidator.MAX_POST_CONTENT_LENGTH})")
        
        if len(content) < 1:
            errors.append("Treść posta nie może być pusta")
        
        # Sprawdź zabronione słowa
        content_lower = content.lower()
        found_forbidden = [word for word in InputValidator.FORBIDDEN_WORDS if word in content_lower]
        if found_forbidden:
            warnings.append(f"Znaleziono potencjalnie problematyczne słowa: {', '.join(found_forbidden)}")
        
        # Sprawdź nadmierną liczbę emoji
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content))
        if emoji_count > 10:
            warnings.append(f"Duża liczba emoji ({emoji_count}) może wpłynąć na zasięg")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={'content': content}
        )
    
    @staticmethod
    def validate_hashtags(hashtags: str) -> ValidationResult:
        """Waliduje hashtagi"""
        errors = []
        warnings = []
        
        if not hashtags or not isinstance(hashtags, str):
            return ValidationResult(True, [], [], {'hashtags': ''})
        
        hashtags = hashtags.strip()
        if not hashtags:
            return ValidationResult(True, [], [], {'hashtags': ''})
        
        # Podziel hashtagi
        hashtag_list = [tag.strip() for tag in re.split(r'[\s,]+', hashtags) if tag.strip()]
        valid_hashtags = []
        
        for tag in hashtag_list:
            if not tag.startswith('#'):
                tag = '#' + tag
            
            if not InputValidator.HASHTAG_PATTERN.match(tag):
                errors.append(f"Nieprawidłowy hashtag: {tag}")
                continue
            
            if len(tag) > 100:  # Instagram limit
                errors.append(f"Hashtag za długi: {tag}")
                continue
            
            valid_hashtags.append(tag)
        
        if len(valid_hashtags) > InputValidator.MAX_HASHTAGS_COUNT:
            warnings.append(f"Za dużo hashtagów ({len(valid_hashtags)} > {InputValidator.MAX_HASHTAGS_COUNT})")
            valid_hashtags = valid_hashtags[:InputValidator.MAX_HASHTAGS_COUNT]
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={'hashtags': ' '.join(valid_hashtags)}
        )
    
    @staticmethod
    def validate_image_url(url: str) -> ValidationResult:
        """Waliduje URL obrazu"""
        errors = []
        warnings = []
        
        if not url or not isinstance(url, str):
            errors.append("URL obrazu nie może być pusty")
            return ValidationResult(False, errors, warnings)
        
        url = url.strip()
        
        if len(url) > InputValidator.MAX_IMAGE_URL_LENGTH:
            errors.append(f"URL obrazu za długi ({len(url)} > {InputValidator.MAX_IMAGE_URL_LENGTH})")
        
        # Sprawdź format URL
        if not InputValidator.URL_PATTERN.match(url):
            errors.append("Nieprawidłowy format URL")
        
        # Sprawdź czy URL wskazuje na obraz
        parsed = urlparse(url)
        if parsed.path:
            path_lower = parsed.path.lower()
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
            if not any(path_lower.endswith(ext) for ext in image_extensions):
                # Sprawdź czy to Google Drive lub inne znane serwisy
                if 'drive.google.com' not in parsed.netloc and 'imgur.com' not in parsed.netloc:
                    warnings.append("URL może nie wskazywać na obraz")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={'url': url}
        )
    
    @staticmethod
    def validate_post_data(post_data: Dict[str, Any]) -> ValidationResult:
        """Waliduje kompletne dane posta"""
        all_errors = []
        all_warnings = []
        sanitized_data = {}
        
        # Waliduj treść posta
        if 'tresc_postu' in post_data:
            content_result = InputValidator.validate_post_content(post_data['tresc_postu'])
            all_errors.extend(content_result.errors)
            all_warnings.extend(content_result.warnings)
            if content_result.sanitized_data:
                sanitized_data.update(content_result.sanitized_data)
        
        # Waliduj hashtagi
        if 'tagi' in post_data:
            hashtags_result = InputValidator.validate_hashtags(post_data['tagi'])
            all_errors.extend(hashtags_result.errors)
            all_warnings.extend(hashtags_result.warnings)
            if hashtags_result.sanitized_data:
                sanitized_data.update(hashtags_result.sanitized_data)
        
        # Waliduj URL obrazu
        if 'sciezka_zdjecia' in post_data:
            url_result = InputValidator.validate_image_url(post_data['sciezka_zdjecia'])
            all_errors.extend(url_result.errors)
            all_warnings.extend(url_result.warnings)
            if url_result.sanitized_data:
                sanitized_data.update(url_result.sanitized_data)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            sanitized_data=sanitized_data
        )


class AdvancedRateLimiter:
    """Zaawansowany rate limiter z różnymi strategiami"""
    
    def __init__(self, 
                 calls_per_minute: int = 60,
                 calls_per_hour: int = 1000,
                 burst_limit: int = 10,
                 cooldown_period: int = 300):
        """
        Args:
            calls_per_minute: Maksymalna liczba wywołań na minutę
            calls_per_hour: Maksymalna liczba wywołań na godzinę
            burst_limit: Maksymalna liczba szybkich wywołań pod rząd
            cooldown_period: Okres ochłodzenia po przekroczeniu limitów (sekundy)
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.burst_limit = burst_limit
        self.cooldown_period = cooldown_period
        
        # Historia wywołań
        self.call_history: List[float] = []
        self.burst_count = 0
        self.last_burst_reset = time.time()
        self.cooldown_until = 0.0
        
        # Statystyki
        self.total_calls = 0
        self.blocked_calls = 0
    
    def can_make_call(self) -> tuple[bool, str]:
        """Sprawdza czy można wykonać wywołanie"""
        current_time = time.time()
        
        # Sprawdź cooldown
        if current_time < self.cooldown_until:
            remaining = int(self.cooldown_until - current_time)
            return False, f"Cooldown aktywny przez {remaining}s"
        
        # Wyczyść starą historię
        self._cleanup_history(current_time)
        
        # Sprawdź limity
        minute_calls = len([t for t in self.call_history if current_time - t <= 60])
        hour_calls = len([t for t in self.call_history if current_time - t <= 3600])
        
        if minute_calls >= self.calls_per_minute:
            return False, f"Przekroczono limit {self.calls_per_minute} wywołań/min"
        
        if hour_calls >= self.calls_per_hour:
            return False, f"Przekroczono limit {self.calls_per_hour} wywołań/h"
        
        # Sprawdź burst limit
        if current_time - self.last_burst_reset > 60:  # Reset co minutę
            self.burst_count = 0
            self.last_burst_reset = current_time
        
        if self.burst_count >= self.burst_limit:
            return False, f"Przekroczono burst limit {self.burst_limit} wywołań"
        
        return True, "OK"
    
    def record_call(self) -> None:
        """Rejestruje wykonane wywołanie"""
        current_time = time.time()
        self.call_history.append(current_time)
        self.burst_count += 1
        self.total_calls += 1
        
        log_with_context('debug', 'API call recorded', 
                        total_calls=self.total_calls,
                        burst_count=self.burst_count,
                        minute_calls=len([t for t in self.call_history if current_time - t <= 60]))
    
    def record_blocked_call(self, reason: str) -> None:
        """Rejestruje zablokowane wywołanie"""
        self.blocked_calls += 1
        log_with_context('warning', 'API call blocked by rate limiter', 
                        reason=reason, blocked_calls=self.blocked_calls)
    
    def trigger_cooldown(self, reason: str = "Rate limit exceeded") -> None:
        """Aktywuje okres ochłodzenia"""
        self.cooldown_until = time.time() + self.cooldown_period
        log_with_context('warning', 'Rate limiter cooldown activated', 
                        reason=reason, cooldown_seconds=self.cooldown_period)
    
    def wait_if_needed(self) -> bool:
        """Czeka jeśli potrzeba, zwraca True jeśli można kontynuować"""
        can_call, reason = self.can_make_call()
        
        if not can_call:
            self.record_blocked_call(reason)
            
            # Jeśli to problem z minutowym limitem, poczekaj
            if "wywołań/min" in reason:
                wait_time = 60 - (time.time() % 60) + 1
                log_with_context('info', 'Waiting for rate limit reset', wait_seconds=wait_time)
                time.sleep(wait_time)
                return self.wait_if_needed()  # Sprawdź ponownie
            
            # Jeśli cooldown, nie czekaj
            return False
        
        self.record_call()
        return True
    
    def _cleanup_history(self, current_time: float) -> None:
        """Usuwa stare wpisy z historii"""
        # Zachowaj tylko wpisy z ostatniej godziny
        cutoff = current_time - 3600
        self.call_history = [t for t in self.call_history if t > cutoff]
    
    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki rate limitera"""
        current_time = time.time()
        self._cleanup_history(current_time)
        
        return {
            'total_calls': self.total_calls,
            'blocked_calls': self.blocked_calls,
            'calls_last_minute': len([t for t in self.call_history if current_time - t <= 60]),
            'calls_last_hour': len([t for t in self.call_history if current_time - t <= 3600]),
            'burst_count': self.burst_count,
            'cooldown_active': current_time < self.cooldown_until,
            'cooldown_remaining': max(0, int(self.cooldown_until - current_time))
        }


class SecurityManager:
    """Główny manager bezpieczeństwa"""
    
    def __init__(self):
        self.validator = InputValidator()
        self.instagram_limiter = AdvancedRateLimiter(
            calls_per_minute=20,  # Konserwatywny limit dla Instagram
            calls_per_hour=500,
            burst_limit=5,
            cooldown_period=600  # 10 minut cooldown
        )
        self.google_sheets_limiter = AdvancedRateLimiter(
            calls_per_minute=60,  # Google Sheets ma wyższe limity
            calls_per_hour=3000,
            burst_limit=10,
            cooldown_period=300  # 5 minut cooldown
        )
        
        # Tracking podejrzanych aktywności
        self.suspicious_activity_count = 0
        self.last_suspicious_activity = 0.0
    
    def validate_and_sanitize_post(self, post_data: Dict[str, Any]) -> ValidationResult:
        """Waliduje i sanityzuje dane posta"""
        result = self.validator.validate_post_data(post_data)
        
        if result.errors:
            log_with_context('warning', 'Post validation failed', 
                           errors=result.errors, post_data=post_data)
        
        if result.warnings:
            log_with_context('info', 'Post validation warnings', 
                           warnings=result.warnings)
        
        return result
    
    def check_instagram_rate_limit(self) -> bool:
        """Sprawdza i egzekwuje rate limit dla Instagram"""
        return self.instagram_limiter.wait_if_needed()
    
    def check_google_sheets_rate_limit(self) -> bool:
        """Sprawdza i egzekwuje rate limit dla Google Sheets"""
        return self.google_sheets_limiter.wait_if_needed()
    
    def report_suspicious_activity(self, activity_type: str, details: Dict[str, Any]) -> None:
        """Raportuje podejrzaną aktywność"""
        current_time = time.time()
        self.suspicious_activity_count += 1
        self.last_suspicious_activity = current_time
        
        log_with_context('warning', 'Suspicious activity detected', 
                        activity_type=activity_type, 
                        details=details,
                        count=self.suspicious_activity_count)
        
        # Jeśli za dużo podejrzanych aktywności, aktywuj cooldown
        if self.suspicious_activity_count > 5:
            self.instagram_limiter.trigger_cooldown("Too many suspicious activities")
            self.suspicious_activity_count = 0  # Reset
    
    def get_security_status(self) -> Dict[str, Any]:
        """Zwraca status bezpieczeństwa"""
        return {
            'instagram_limiter': self.instagram_limiter.get_stats(),
            'google_sheets_limiter': self.google_sheets_limiter.get_stats(),
            'suspicious_activity_count': self.suspicious_activity_count,
            'last_suspicious_activity': self.last_suspicious_activity
        }


# Globalna instancja security managera
security_manager = SecurityManager()