#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring i health check dla aplikacji Instagram Scheduler
Zawiera endpoint health check i zbieranie metryk
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request
from config import log_with_context


@dataclass
class HealthStatus:
    """Status zdrowia aplikacji"""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: str
    uptime_seconds: float
    version: str = "1.0.0"
    

@dataclass
class SystemMetrics:
    """Metryki systemowe"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    

@dataclass
class ApplicationMetrics:
    """Metryki aplikacji"""
    posts_published_total: int
    posts_failed_total: int
    posts_published_last_24h: int
    posts_failed_last_24h: int
    last_successful_post: Optional[str]
    last_failed_post: Optional[str]
    scheduler_status: str
    api_calls_instagram: int
    api_calls_google_sheets: int
    api_calls_blocked: int
    

class MetricsCollector:
    """Kolektor metryk aplikacji"""
    
    def __init__(self):
        self.start_time = time.time()
        self.posts_published = 0
        self.posts_failed = 0
        self.api_calls_instagram = 0
        self.api_calls_google_sheets = 0
        self.api_calls_blocked = 0
        
        # Historia zdarzeń (ostatnie 24h)
        self.events_history: List[Dict[str, Any]] = []
        self.last_successful_post: Optional[str] = None
        self.last_failed_post: Optional[str] = None
        self.scheduler_status = "stopped"
        
        # Lock dla thread safety
        self._lock = threading.Lock()
    
    def record_post_published(self, post_info: Dict[str, Any]) -> None:
        """Rejestruje opublikowany post"""
        with self._lock:
            self.posts_published += 1
            self.last_successful_post = datetime.now().isoformat()
            
            event = {
                'type': 'post_published',
                'timestamp': self.last_successful_post,
                'data': post_info
            }
            self._add_event(event)
            
            log_with_context('info', 'Post publication recorded', 
                           total_published=self.posts_published,
                           post_info=post_info)
    
    def record_post_failed(self, post_info: Dict[str, Any], error: str) -> None:
        """Rejestruje nieudaną publikację posta"""
        with self._lock:
            self.posts_failed += 1
            self.last_failed_post = datetime.now().isoformat()
            
            event = {
                'type': 'post_failed',
                'timestamp': self.last_failed_post,
                'data': post_info,
                'error': error
            }
            self._add_event(event)
            
            log_with_context('warning', 'Post publication failure recorded', 
                           total_failed=self.posts_failed,
                           post_info=post_info,
                           error=error)
    
    def record_api_call(self, service: str, blocked: bool = False) -> None:
        """Rejestruje wywołanie API"""
        with self._lock:
            if service == 'instagram':
                self.api_calls_instagram += 1
            elif service == 'google_sheets':
                self.api_calls_google_sheets += 1
            
            if blocked:
                self.api_calls_blocked += 1
                
                event = {
                    'type': 'api_call_blocked',
                    'timestamp': datetime.now().isoformat(),
                    'service': service
                }
                self._add_event(event)
    
    def update_scheduler_status(self, status: str) -> None:
        """Aktualizuje status schedulera"""
        with self._lock:
            old_status = self.scheduler_status
            self.scheduler_status = status
            
            if old_status != status:
                event = {
                    'type': 'scheduler_status_change',
                    'timestamp': datetime.now().isoformat(),
                    'old_status': old_status,
                    'new_status': status
                }
                self._add_event(event)
                
                log_with_context('info', 'Scheduler status changed', 
                               old_status=old_status, new_status=status)
    
    def _add_event(self, event: Dict[str, Any]) -> None:
        """Dodaje zdarzenie do historii"""
        self.events_history.append(event)
        
        # Usuń stare zdarzenia (starsze niż 24h)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.events_history = [
            e for e in self.events_history 
            if datetime.fromisoformat(e['timestamp']) > cutoff_time
        ]
    
    def get_system_metrics(self) -> SystemMetrics:
        """Pobiera metryki systemowe"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Pamięć
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Dysk
            disk = psutil.disk_usage('.')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=round(memory_used_mb, 2),
                memory_available_mb=round(memory_available_mb, 2),
                disk_usage_percent=round(disk_usage_percent, 2),
                disk_free_gb=round(disk_free_gb, 2)
            )
        except Exception as e:
            log_with_context('error', 'Failed to collect system metrics', error=str(e))
            # Zwróć domyślne wartości w przypadku błędu
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0
            )
    
    def get_application_metrics(self) -> ApplicationMetrics:
        """Pobiera metryki aplikacji"""
        with self._lock:
            # Policz zdarzenia z ostatnich 24h
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            posts_published_24h = len([
                e for e in self.events_history 
                if e['type'] == 'post_published' and 
                   datetime.fromisoformat(e['timestamp']) > cutoff_time
            ])
            
            posts_failed_24h = len([
                e for e in self.events_history 
                if e['type'] == 'post_failed' and 
                   datetime.fromisoformat(e['timestamp']) > cutoff_time
            ])
            
            return ApplicationMetrics(
                posts_published_total=self.posts_published,
                posts_failed_total=self.posts_failed,
                posts_published_last_24h=posts_published_24h,
                posts_failed_last_24h=posts_failed_24h,
                last_successful_post=self.last_successful_post,
                last_failed_post=self.last_failed_post,
                scheduler_status=self.scheduler_status,
                api_calls_instagram=self.api_calls_instagram,
                api_calls_google_sheets=self.api_calls_google_sheets,
                api_calls_blocked=self.api_calls_blocked
            )
    
    def get_health_status(self) -> HealthStatus:
        """Określa status zdrowia aplikacji"""
        uptime = time.time() - self.start_time
        
        # Sprawdź różne wskaźniki zdrowia
        health_issues = []
        
        # Sprawdź metryki systemowe
        try:
            system_metrics = self.get_system_metrics()
            
            if system_metrics.cpu_percent > 90:
                health_issues.append("High CPU usage")
            
            if system_metrics.memory_percent > 90:
                health_issues.append("High memory usage")
            
            if system_metrics.disk_usage_percent > 95:
                health_issues.append("Low disk space")
        except Exception:
            health_issues.append("Cannot collect system metrics")
        
        # Sprawdź metryki aplikacji
        app_metrics = self.get_application_metrics()
        
        # Sprawdź czy scheduler działa
        if app_metrics.scheduler_status not in ['running', 'idle']:
            health_issues.append("Scheduler not running")
        
        # Sprawdź czy są zbyt częste błędy
        if (app_metrics.posts_failed_last_24h > 0 and 
            app_metrics.posts_published_last_24h > 0):
            failure_rate = app_metrics.posts_failed_last_24h / (
                app_metrics.posts_published_last_24h + app_metrics.posts_failed_last_24h
            )
            if failure_rate > 0.5:  # Więcej niż 50% błędów
                health_issues.append("High failure rate")
        
        # Określ status
        if not health_issues:
            status = "healthy"
        elif len(health_issues) <= 2:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=round(uptime, 2)
        )


class HealthCheckServer:
    """Serwer HTTP dla health check i metryk"""
    
    def __init__(self, metrics_collector: MetricsCollector, port: int = 8080):
        self.metrics_collector = metrics_collector
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Konfiguruje endpointy"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Endpoint health check"""
            try:
                health_status = self.metrics_collector.get_health_status()
                
                # Ustaw odpowiedni kod HTTP
                if health_status.status == 'healthy':
                    status_code = 200
                elif health_status.status == 'degraded':
                    status_code = 200  # Nadal dostępne
                else:  # unhealthy
                    status_code = 503  # Service Unavailable
                
                return jsonify(asdict(health_status)), status_code
                
            except Exception as e:
                log_with_context('error', 'Health check failed', error=str(e))
                return jsonify({
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }), 503
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Endpoint metryk"""
            try:
                system_metrics = self.metrics_collector.get_system_metrics()
                app_metrics = self.metrics_collector.get_application_metrics()
                
                return jsonify({
                    'system': asdict(system_metrics),
                    'application': asdict(app_metrics),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                log_with_context('error', 'Metrics collection failed', error=str(e))
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/metrics/prometheus', methods=['GET'])
        def prometheus_metrics():
            """Endpoint metryk w formacie Prometheus"""
            try:
                system_metrics = self.metrics_collector.get_system_metrics()
                app_metrics = self.metrics_collector.get_application_metrics()
                
                # Format Prometheus
                metrics_text = f"""# HELP instagram_scheduler_posts_published_total Total number of published posts
# TYPE instagram_scheduler_posts_published_total counter
instagram_scheduler_posts_published_total {app_metrics.posts_published_total}

# HELP instagram_scheduler_posts_failed_total Total number of failed posts
# TYPE instagram_scheduler_posts_failed_total counter
instagram_scheduler_posts_failed_total {app_metrics.posts_failed_total}

# HELP instagram_scheduler_cpu_percent CPU usage percentage
# TYPE instagram_scheduler_cpu_percent gauge
instagram_scheduler_cpu_percent {system_metrics.cpu_percent}

# HELP instagram_scheduler_memory_percent Memory usage percentage
# TYPE instagram_scheduler_memory_percent gauge
instagram_scheduler_memory_percent {system_metrics.memory_percent}

# HELP instagram_scheduler_api_calls_instagram Instagram API calls
# TYPE instagram_scheduler_api_calls_instagram counter
instagram_scheduler_api_calls_instagram {app_metrics.api_calls_instagram}

# HELP instagram_scheduler_api_calls_google_sheets Google Sheets API calls
# TYPE instagram_scheduler_api_calls_google_sheets counter
instagram_scheduler_api_calls_google_sheets {app_metrics.api_calls_google_sheets}

# HELP instagram_scheduler_api_calls_blocked Blocked API calls
# TYPE instagram_scheduler_api_calls_blocked counter
instagram_scheduler_api_calls_blocked {app_metrics.api_calls_blocked}
"""
                
                return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
                
            except Exception as e:
                log_with_context('error', 'Prometheus metrics failed', error=str(e))
                return f"# Error: {str(e)}\n", 500, {'Content-Type': 'text/plain'}
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Endpoint statusu aplikacji"""
            try:
                health_status = self.metrics_collector.get_health_status()
                system_metrics = self.metrics_collector.get_system_metrics()
                app_metrics = self.metrics_collector.get_application_metrics()
                
                return jsonify({
                    'health': asdict(health_status),
                    'system': asdict(system_metrics),
                    'application': asdict(app_metrics)
                })
                
            except Exception as e:
                log_with_context('error', 'Status endpoint failed', error=str(e))
                return jsonify({'error': str(e)}), 500
    
    def start(self) -> None:
        """Uruchamia serwer health check"""
        try:
            log_with_context('info', 'Starting health check server', port=self.port)
            self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
        except Exception as e:
            log_with_context('error', 'Failed to start health check server', 
                           port=self.port, error=str(e))
            raise
    
    def start_in_background(self) -> threading.Thread:
        """Uruchamia serwer w tle"""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        log_with_context('info', 'Health check server started in background', port=self.port)
        return thread


# Globalna instancja kolektora metryk
metrics_collector = MetricsCollector()