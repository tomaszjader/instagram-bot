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
   ```

## 📊 Konfiguracja Google Sheets

Arkusz powinien zawierać kolumny:
- `data_publikacji` - data publikacji (DD.MM.YYYY lub inne obsługiwane formaty)
- `tresc_postu` - treść posta
- `tagi` - hashtagi (opcjonalnie)
- `sciezka_zdjecia` - URL lub ścieżka do zdjęcia
- `czy_opublikowano` - status publikacji (TRUE/FALSE)

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

### Korzyści refaktoryzacji:
- ✅ Single Responsibility Principle
- ✅ Łatwiejsze testowanie jednostkowe
- ✅ Lepsza skalowalność
- ✅ Prostsze debugowanie
- ✅ Czytelniejszy kod

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
Można to zmienić w pliku `scheduler.py` w linii:
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
- Zweryfikuj poprawność Google Sheet ID
- Upewnij się, że API Key ma odpowiednie uprawnienia

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