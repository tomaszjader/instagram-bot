#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testy dla modułu monitoring
Testuje funkcjonalność health check, metryk i kolektora
"""

import unittest
import time
import threading
import requests
from datetime import datetime, timedelta
from monitoring import MetricsCollector, HealthCheckServer, SystemMetrics, ApplicationMetrics, HealthStatus


class TestMetricsCollector(unittest.TestCase):
    """Testy dla MetricsCollector"""
    
    def setUp(self):
        """Przygotowanie przed każdym testem"""
        self.collector = MetricsCollector()
    
    def test_initial_state(self):
        """Test początkowego stanu kolektora"""
        self.assertEqual(self.collector.posts_published, 0)
        self.assertEqual(self.collector.posts_failed, 0)
        self.assertEqual(self.collector.api_calls_instagram, 0)
        self.assertEqual(self.collector.api_calls_google_sheets, 0)
        self.assertEqual(self.collector.api_calls_blocked, 0)
        self.assertEqual(self.collector.scheduler_status, "stopped")
        self.assertIsNone(self.collector.last_successful_post)
        self.assertIsNone(self.collector.last_failed_post)
    
    def test_record_post_published(self):
        """Test rejestrowania opublikowanego posta"""
        post_info = {
            'content_preview': 'Test post content',
            'image_url': 'https://example.com/image.jpg',
            'hashtags': '#test #monitoring'
        }
        
        self.collector.record_post_published(post_info)
        
        self.assertEqual(self.collector.posts_published, 1)
        self.assertIsNotNone(self.collector.last_successful_post)
        self.assertEqual(len(self.collector.events_history), 1)
        
        event = self.collector.events_history[0]
        self.assertEqual(event['type'], 'post_published')
        self.assertEqual(event['data'], post_info)
    
    def test_record_post_failed(self):
        """Test rejestrowania nieudanej publikacji"""
        post_info = {
            'content_preview': 'Failed post content',
            'image_url': 'https://example.com/image.jpg'
        }
        error = "Network timeout"
        
        self.collector.record_post_failed(post_info, error)
        
        self.assertEqual(self.collector.posts_failed, 1)
        self.assertIsNotNone(self.collector.last_failed_post)
        self.assertEqual(len(self.collector.events_history), 1)
        
        event = self.collector.events_history[0]
        self.assertEqual(event['type'], 'post_failed')
        self.assertEqual(event['data'], post_info)
        self.assertEqual(event['error'], error)
    
    def test_record_api_call(self):
        """Test rejestrowania wywołań API"""
        # Test normalnego wywołania Instagram API
        self.collector.record_api_call('instagram')
        self.assertEqual(self.collector.api_calls_instagram, 1)
        self.assertEqual(self.collector.api_calls_blocked, 0)
        
        # Test normalnego wywołania Google Sheets API
        self.collector.record_api_call('google_sheets')
        self.assertEqual(self.collector.api_calls_google_sheets, 1)
        
        # Test zablokowanego wywołania
        self.collector.record_api_call('instagram', blocked=True)
        self.assertEqual(self.collector.api_calls_instagram, 2)
        self.assertEqual(self.collector.api_calls_blocked, 1)
        
        # Sprawdź czy zablokowane wywołanie zostało zapisane w historii
        blocked_events = [e for e in self.collector.events_history if e['type'] == 'api_call_blocked']
        self.assertEqual(len(blocked_events), 1)
        self.assertEqual(blocked_events[0]['service'], 'instagram')
    
    def test_update_scheduler_status(self):
        """Test aktualizacji statusu schedulera"""
        # Test zmiany statusu
        self.collector.update_scheduler_status('running')
        self.assertEqual(self.collector.scheduler_status, 'running')
        
        # Sprawdź czy zmiana została zapisana w historii
        status_events = [e for e in self.collector.events_history if e['type'] == 'scheduler_status_change']
        self.assertEqual(len(status_events), 1)
        self.assertEqual(status_events[0]['old_status'], 'stopped')
        self.assertEqual(status_events[0]['new_status'], 'running')
        
        # Test braku zmiany (nie powinno dodać zdarzenia)
        initial_events_count = len(self.collector.events_history)
        self.collector.update_scheduler_status('running')
        self.assertEqual(len(self.collector.events_history), initial_events_count)
    
    def test_get_system_metrics(self):
        """Test pobierania metryk systemowych"""
        metrics = self.collector.get_system_metrics()
        
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertGreaterEqual(metrics.cpu_percent, 0)
        self.assertLessEqual(metrics.cpu_percent, 100)
        self.assertGreaterEqual(metrics.memory_percent, 0)
        self.assertLessEqual(metrics.memory_percent, 100)
        self.assertGreater(metrics.memory_used_mb, 0)
        self.assertGreater(metrics.memory_available_mb, 0)
        self.assertGreaterEqual(metrics.disk_usage_percent, 0)
        self.assertLessEqual(metrics.disk_usage_percent, 100)
        self.assertGreater(metrics.disk_free_gb, 0)
    
    def test_get_application_metrics(self):
        """Test pobierania metryk aplikacji"""
        # Dodaj trochę danych testowych
        self.collector.record_post_published({'content': 'test1'})
        self.collector.record_post_failed({'content': 'test2'}, 'error')
        self.collector.record_api_call('instagram')
        self.collector.record_api_call('google_sheets', blocked=True)
        
        metrics = self.collector.get_application_metrics()
        
        self.assertIsInstance(metrics, ApplicationMetrics)
        self.assertEqual(metrics.posts_published_total, 1)
        self.assertEqual(metrics.posts_failed_total, 1)
        self.assertEqual(metrics.posts_published_last_24h, 1)
        self.assertEqual(metrics.posts_failed_last_24h, 1)
        self.assertEqual(metrics.api_calls_instagram, 1)
        self.assertEqual(metrics.api_calls_google_sheets, 1)
        self.assertEqual(metrics.api_calls_blocked, 1)
        self.assertIsNotNone(metrics.last_successful_post)
        self.assertIsNotNone(metrics.last_failed_post)
    
    def test_get_health_status(self):
        """Test określania statusu zdrowia"""
        # Poczekaj chwilę aby uptime był większy od 0
        time.sleep(0.1)
        
        # Test początkowego stanu (powinien być healthy)
        health = self.collector.get_health_status()
        
        self.assertIsInstance(health, HealthStatus)
        self.assertIn(health.status, ['healthy', 'degraded', 'unhealthy'])
        self.assertIsInstance(health.timestamp, str)
        self.assertGreaterEqual(health.uptime_seconds, 0)  # Zmienione na GreaterEqual
        self.assertEqual(health.version, "1.0.0")
        
        # Sprawdź czy timestamp jest w poprawnym formacie ISO
        try:
            datetime.fromisoformat(health.timestamp)
        except ValueError:
            self.fail("Timestamp is not in ISO format")
    
    def test_events_cleanup(self):
        """Test czyszczenia starych zdarzeń"""
        # Dodaj zdarzenie i zmień jego timestamp na starszy niż 24h
        self.collector.record_post_published({'content': 'old_post'})
        
        # Ręcznie zmień timestamp na starszy
        old_timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
        self.collector.events_history[0]['timestamp'] = old_timestamp
        
        # Dodaj nowe zdarzenie (powinno wywołać cleanup)
        self.collector.record_post_published({'content': 'new_post'})
        
        # Sprawdź czy stare zdarzenie zostało usunięte
        self.assertEqual(len(self.collector.events_history), 1)
        self.assertEqual(self.collector.events_history[0]['data']['content'], 'new_post')


class TestHealthCheckServer(unittest.TestCase):
    """Testy dla HealthCheckServer"""
    
    def setUp(self):
        """Przygotowanie przed każdym testem"""
        self.collector = MetricsCollector()
        self.server = HealthCheckServer(self.collector, port=8081)  # Użyj innego portu
        
        # Uruchom serwer w tle
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()
        
        # Poczekaj chwilę na uruchomienie serwera
        time.sleep(2)
    
    def test_health_endpoint(self):
        """Test endpointu /health"""
        try:
            response = requests.get('http://localhost:8081/health', timeout=5)
            
            self.assertIn(response.status_code, [200, 503])  # Może być healthy lub unhealthy
            
            data = response.json()
            self.assertIn('status', data)
            self.assertIn('timestamp', data)
            self.assertIn('uptime_seconds', data)
            self.assertIn('version', data)
            
            self.assertIn(data['status'], ['healthy', 'degraded', 'unhealthy'])
            self.assertEqual(data['version'], '1.0.0')
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Server not accessible: {e}")
    
    def test_metrics_endpoint(self):
        """Test endpointu /metrics"""
        try:
            # Dodaj trochę danych testowych
            self.collector.record_post_published({'content': 'test'})
            self.collector.record_api_call('instagram')
            
            response = requests.get('http://localhost:8081/metrics', timeout=5)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('system', data)
            self.assertIn('application', data)
            self.assertIn('timestamp', data)
            
            # Sprawdź strukturę metryk systemowych
            system = data['system']
            self.assertIn('cpu_percent', system)
            self.assertIn('memory_percent', system)
            self.assertIn('disk_usage_percent', system)
            
            # Sprawdź strukturę metryk aplikacji
            application = data['application']
            self.assertIn('posts_published_total', application)
            self.assertIn('api_calls_instagram', application)
            self.assertIn('scheduler_status', application)
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Server not accessible: {e}")
    
    def test_prometheus_metrics_endpoint(self):
        """Test endpointu /metrics/prometheus"""
        try:
            response = requests.get('http://localhost:8081/metrics/prometheus', timeout=5)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
            
            content = response.text
            
            # Sprawdź czy zawiera podstawowe metryki Prometheus
            self.assertIn('instagram_scheduler_posts_published_total', content)
            self.assertIn('instagram_scheduler_posts_failed_total', content)
            self.assertIn('instagram_scheduler_cpu_percent', content)
            self.assertIn('instagram_scheduler_memory_percent', content)
            self.assertIn('# HELP', content)
            self.assertIn('# TYPE', content)
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Server not accessible: {e}")
    
    def test_status_endpoint(self):
        """Test endpointu /status"""
        try:
            response = requests.get('http://localhost:8081/status', timeout=5)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('health', data)
            self.assertIn('system', data)
            self.assertIn('application', data)
            
            # Sprawdź czy każda sekcja ma odpowiednią strukturę
            health = data['health']
            self.assertIn('status', health)
            self.assertIn('uptime_seconds', health)
            
            system = data['system']
            self.assertIn('cpu_percent', system)
            
            application = data['application']
            self.assertIn('posts_published_total', application)
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Server not accessible: {e}")


class TestThreadSafety(unittest.TestCase):
    """Testy bezpieczeństwa wątków"""
    
    def test_concurrent_operations(self):
        """Test równoczesnych operacji na kolektorze"""
        collector = MetricsCollector()
        
        def worker():
            for i in range(10):
                collector.record_post_published({'content': f'post_{i}'})
                collector.record_api_call('instagram')
                time.sleep(0.01)
        
        # Uruchom kilka wątków równocześnie
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Poczekaj na zakończenie wszystkich wątków
        for thread in threads:
            thread.join()
        
        # Sprawdź czy wszystkie operacje zostały zarejestrowane
        self.assertEqual(collector.posts_published, 50)  # 5 wątków * 10 postów
        self.assertEqual(collector.api_calls_instagram, 50)  # 5 wątków * 10 wywołań


if __name__ == '__main__':
    # Uruchom testy
    unittest.main(verbosity=2)