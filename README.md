# Instagram Auto Publisher 📸

Automatyczny system publikacji postów na Instagramie na podstawie harmonogramu z Google Sheets.

## 🚀 Funkcje

- ⏰ Automatyczna publikacja postów według harmonogramu
- 📊 Integracja z Google Sheets jako źródło danych
- 🖼️ Automatyczne przetwarzanie obrazów (proporcje Instagram)
- 📱 Powiadomienia Telegram o statusie publikacji
- 🔄 Obsługa różnych formatów dat
- 🌐 Pobieranie obrazów z URL (w tym Google Drive)

## 📋 Wymagania

- Python 3.8+
- Konto Instagram
- Google Sheets API Key
- Bot Telegram (opcjonalnie)

## 🛠️ Instalacja

1. **Sklonuj repozytorium:**
   ```bash
   git clone <repository-url>
   cd pythonProject57
   ```

2. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Utwórz plik `.env` z konfiguracją:**
   ```env
   INSTA_USERNAME=twoja_nazwa_uzytkownika
   INSTA_PASSWORD=twoje_haslo
   GOOGLE_SHEET_ID=id_arkusza_google
   GOOGLE_API_KEY=twoj_klucz_api_google
   TELEGRAM_BOT_TOKEN=token_bota_telegram
   TELEGRAM_CHAT_ID=id_czatu_telegram
   
   # Opcjonalne - konfiguracja logowania
   LOG_LEVEL=INFO
   LOG_FORMAT=TEXT
   ```

## 📊 Konfiguracja Google Sheets

Arkusz powinien zawierać kolumny:
- `data_publikacji` - data publikacji (DD.MM.YYYY lub inne obsługiwane formaty)
- `tresc_postu` - treść posta
- `tagi` - hashtagi (opcjonalnie)
- `sciezka_zdjecia` - URL lub ścieżka do zdjęcia
- `czy_opublikowano` - status publikacji (TRUE/FALSE)

## 📝 Konfiguracja logowania

System obsługuje konfigurowalny poziom logowania i structured logging w formacie JSON:

### Poziomy logowania
- `DEBUG` - szczegółowe informacje diagnostyczne
- `INFO` - ogólne informacje o działaniu (domyślny)
- `WARNING` - ostrzeżenia
- `ERROR` - błędy
- `CRITICAL` - krytyczne błędy

### Formaty logowania
- `TEXT` - standardowy format tekstowy (domyślny)
- `JSON` - structured logging w formacie JSON

### Przykłady konfiguracji
```bash
# Standardowe logowanie
LOG_LEVEL=INFO
LOG_FORMAT=TEXT

# Structured logging dla systemów monitorowania
LOG_LEVEL=DEBUG
LOG_FORMAT=JSON
```

### Testowanie logowania
```bash
python test_logging.py
```

## 🔒 Bezpieczeństwo

Aplikacja zawiera zaawansowane mechanizmy bezpieczeństwa chroniące przed nadużyciami i błędami.

### Walidacja danych wejściowych

- **Nazwy użytkowników Instagram**: Sprawdzanie długości (1-30 znaków) i dozwolonych znaków
- **Treść postów**: Limit 2200 znaków, wykrywanie zabronionych słów
- **Hashtagi**: Maksymalnie 30 hashtagów, walidacja formatu
- **URL obrazów**: Sprawdzanie protokołu HTTPS i rozszerzeń plików

### Rate Limiting

- **Instagram API**: 20 wywołań/min, 500/godz, burst limit 5
- **Google Sheets API**: 60 wywołań/min, 3000/godz, burst limit 10
- **Automatyczny cooldown**: Po przekroczeniu limitów (5-10 minut)
- **Inteligentne oczekiwanie**: Automatyczne opóźnienia przy zbliżaniu się do limitów

### Monitoring bezpieczeństwa

- **Wykrywanie podejrzanych aktywności**: Automatyczne logowanie nietypowych zachowań
- **Statystyki wywołań API**: Śledzenie użycia i blokad
- **Strukturalne logowanie**: Wszystkie zdarzenia bezpieczeństwa w formacie JSON

### Testowanie bezpieczeństwa

Aby przetestować funkcje bezpieczeństwa:

```bash
python test_security.py
```

## 📊 Monitoring i Health Check

Aplikacja zawiera zaawansowany system monitorowania:

### Health Check Server
- **Port**: 8080 (konfigurowalny przez `HEALTH_CHECK_PORT`)
- **Automatyczne uruchamianie**: serwer startuje w tle razem z aplikacją
- **Endpointy HTTP**: dostępne dla zewnętrznych systemów monitorowania

### Dostępne Endpointy

#### `/health` - Status Zdrowia
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-01-17T23:26:34.123456",
  "uptime_seconds": 3600.5,
  "version": "1.0.0"
}
```

#### `/metrics` - Metryki Aplikacji
```json
{
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_used_mb": 512.3,
    "memory_available_mb": 1024.7,
    "disk_usage_percent": 67.4,
    "disk_free_gb": 25.8
  },
  "application": {
    "posts_published_total": 150,
    "posts_failed_total": 3,
    "posts_published_last_24h": 12,
    "posts_failed_last_24h": 0,
    "last_successful_post": "2025-01-17T22:30:15.123456",
    "last_failed_post": null,
    "scheduler_status": "running",
    "api_calls_instagram": 200,
    "api_calls_google_sheets": 50,
    "api_calls_blocked": 5
  },
  "timestamp": "2025-01-17T23:26:34.123456"
}
```

#### `/metrics/prometheus` - Metryki Prometheus
Format kompatybilny z Prometheus dla integracji z systemami monitorowania:
```
# HELP instagram_scheduler_posts_published_total Total number of published posts
# TYPE instagram_scheduler_posts_published_total counter
instagram_scheduler_posts_published_total 150

# HELP instagram_scheduler_cpu_percent CPU usage percentage
# TYPE instagram_scheduler_cpu_percent gauge
instagram_scheduler_cpu_percent 15.2
```

#### `/status` - Pełny Status
Kombinuje informacje z `/health` i `/metrics` w jednym endpoincie.

### Automatyczne Zbieranie Metryk
- **Publikacje postów**: automatyczne rejestrowanie udanych i nieudanych publikacji
- **Wywołania API**: śledzenie wszystkich wywołań Instagram i Google Sheets API
- **Status schedulera**: monitorowanie stanu aplikacji (running, stopped, error)
- **Metryki systemowe**: CPU, pamięć, dysk w czasie rzeczywistym

### Kryteria Zdrowia
Aplikacja automatycznie określa swój status na podstawie:
- **CPU > 90%**: degraded/unhealthy
- **Pamięć > 90%**: degraded/unhealthy
- **Dysk > 95%**: degraded/unhealthy
- **Scheduler nie działa**: degraded/unhealthy
- **Wskaźnik błędów > 50%**: degraded/unhealthy

### Integracja z Systemami Monitorowania
- **Prometheus**: endpoint `/metrics/prometheus`
- **Grafana**: wizualizacja metryk
- **Alerting**: na podstawie statusu health check
- **Load balancers**: health check dla wysokiej dostępności

### Testowanie Monitorowania
```bash
python test_monitoring.py
```

### Przykłady Użycia
```bash
# Sprawdź status zdrowia
curl http://localhost:8080/health

# Pobierz metryki
curl http://localhost:8080/metrics

# Metryki dla Prometheus
curl http://localhost:8080/metrics/prometheus
```

## 🎯 Użycie

### Uruchomienie harmonogramu
```bash
python main.py
```

### Test publikacji
```bash
python main.py test
```

### Test parsowania dat
```bash
python main.py dates
```

### Test ładowania danych
```bash
python main.py data
```

### Jednorazowa publikacja
```bash
python main.py once
```

### Status schedulera
```bash
python main.py status
```

### Pomoc
```bash
python main.py help
```

## 📁 Struktura projektu

```
├── .gitignore           # Pliki ignorowane przez Git
├── README.md            # Dokumentacja projektu
├── main.py              # Główny plik uruchomieniowy
├── config.py            # Konfiguracja i zmienne środowiskowe
├── scheduler.py         # Scheduler oparty na klasach
├── models.py            # Modele danych (Post, ColumnMapper)
├── services.py          # Logika biznesowa (serwisy)
├── instagram.py         # Integracja z Instagram API
├── google_sheets.py     # Integracja z Google Sheets API
├── telegram_bot.py      # Powiadomienia Telegram
├── image_utils.py       # Przetwarzanie obrazów
└── requirements.txt     # Zależności projektu
```

## 🏗️ Architektura

Projekt został zrefaktoryzowany z monolitycznej struktury na architekturę opartą na klasach:

- **models.py** - Modele danych (`Post`, `ColumnMapper`)
- **services.py** - Serwisy biznesowe (`DataService`, `ImageService`, `NotificationService`, `PublisherService`)
- **scheduler.py** - Scheduler (`Scheduler`, `TestScheduler`)
- **main.py** - Punkt wejścia z rozszerzonymi opcjami
- **config.py** - Zarządzanie konfiguracją środowiska
- **instagram.py** - Obsługa publikacji na Instagram
- **google_sheets.py** - Integracja z Google Sheets
- **telegram_bot.py** - Powiadomienia przez Telegram
- **image_utils.py** - Przetwarzanie i optymalizacja obrazów

### Korzyści refaktoryzacji:
- ✅ Single Responsibility Principle
- ✅ Łatwiejsze testowanie jednostkowe
- ✅ Lepsza skalowalność
- ✅ Prostsze debugowanie
- ✅ Czytelniejszy kod
- ✅ Usunięte duplikacje kodu

## ⚙️ Konfiguracja API

### Google Sheets API
1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt lub wybierz istniejący
3. Włącz Google Sheets API
4. Utwórz klucz API i dodaj go do `.env`

### Telegram Bot (opcjonalnie)
1. Napisz do [@BotFather](https://t.me/botfather) na Telegramie
2. Utwórz nowego bota poleceniem `/newbot`
3. Skopiuj token i dodaj do `.env`
4. Znajdź swoje Chat ID i dodaj do `.env`

## 🕐 Harmonogram

Domyślnie system sprawdza posty do publikacji codziennie o **16:00**. 
Można to zmienić w pliku `scheduler.py` w metodzie `run()` klasy `Scheduler`:
```python
target_time = dt_time(16, 0)  # Zmień na wybraną godzinę
```

## 🖼️ Obsługiwane formaty obrazów

- JPG, JPEG, PNG, WEBP
- Automatyczne dostosowanie proporcji do wymagań Instagram
- Obsługa URL (w tym Google Drive)
- Lokalne pliki z folderu `images/`

## 📝 Obsługiwane formaty dat

- `DD.MM.YYYY` (np. 08.08.2025)
- `DD/MM/YYYY` (np. 08/08/2025)
- `YYYY-MM-DD` (np. 2025-08-08)
- `DD-MM-YYYY` (np. 08-08-2025)
- Liczby (serial date number z Excel/Google Sheets)

## 🚨 Uwagi bezpieczeństwa

- **Nigdy nie commituj pliku `.env`** do repozytorium
- Używaj silnych haseł dla konta Instagram
- Regularnie zmieniaj klucze API
- Monitoruj aktywność konta Instagram

## 🐛 Rozwiązywanie problemów

### Błędy logowania Instagram
- Sprawdź poprawność danych logowania
- Instagram może wymagać weryfikacji dwuetapowej
- Unikaj zbyt częstego logowania (może prowadzić do blokady)

### Błędy Google Sheets API
- Sprawdź czy arkusz jest publiczny lub udostępniony
- Zweryfikuj poprawność Google Sheet ID w pliku `.env`
- Upewnij się, że API Key ma odpowiednie uprawnienia
- Sprawdź czy kolumny w arkuszu mają poprawne nazwy

### Problemy z obrazami
- Sprawdź czy URL jest dostępny publicznie
- Upewnij się, że format obrazu jest obsługiwany
- Sprawdź czy folder `images/` istnieje dla lokalnych plików

## 📄 Licencja

Ten projekt jest udostępniony na licencji MIT.

## 🤝 Wsparcie

W przypadku problemów:
1. Sprawdź logi w konsoli
2. Przetestuj komponenty osobno (`python main.py test`)
3. Sprawdź konfigurację w pliku `.env`

---

**⚠️ Disclaimer:** Używaj tego narzędzia zgodnie z regulaminem Instagram. Autor nie ponosi odpowiedzialności za ewentualne blokady konta.