import requests
import re
from datetime import datetime, timedelta
from config import GOOGLE_API_KEY, GOOGLE_SHEET_ID, logger


def gdrive_to_direct(url):
    """Konwertuje URL Google Drive na bezpośredni link do pobierania"""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def parsuj_date_value(date_value):
    """Parsuje wartość daty z Google Sheets (może być string lub liczba)"""
    if not date_value:
        return None

    # Jeśli to liczba (serial date number z Google Sheets/Excel)
    if isinstance(date_value, (int, float)):
        try:
            # Google Sheets używa serial date number (liczba dni od 30.12.1899)
            excel_epoch = datetime(1899, 12, 30)
            data_publikacji = excel_epoch + timedelta(days=int(date_value))
            return data_publikacji.date()
        except Exception as e:
            logger.warning(f"Nie można sparsować serial date number {date_value}: {e}")
            return None

    # Jeśli to string, spróbuj różnych formatów
    data_str = str(date_value).strip()
    if not data_str:
        return None

    possible_formats = [
        "%d.%m.%Y",  # 08.08.2025
        "%d/%m/%Y",  # 08/08/2025
        "%Y-%m-%d",  # 2025-08-08
        "%Y-%m-%d %H:%M:%S",  # 2025-08-08 10:00:00
        "%d-%m-%Y",  # 08-08-2025
        "%m/%d/%Y",  # 08/08/2025 (US format)
        "%Y.%m.%d",  # 2025.08.08
    ]

    for date_format in possible_formats:
        try:
            if ' ' in data_str and '%H:%M:%S' in date_format:
                return datetime.strptime(data_str, date_format).date()
            elif ' ' not in data_str and '%H:%M:%S' not in date_format:
                return datetime.strptime(data_str, date_format).date()
        except ValueError:
            continue

    return None


def pobierz_zdjecia_z_arkusza(sheet_id):
    """Pobiera wszystkie zdjęcia z arkusza Google Sheets"""
    try:
        # Pobierz metadane arkusza zawierające informacje o obrazkach
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        params = {
            'key': GOOGLE_API_KEY,
            'includeGridData': 'true'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        images_by_position = {}

        # Przeszukaj arkusz w poszukiwaniu obrazków
        if 'sheets' in data and len(data['sheets']) > 0:
            sheet_data = data['sheets'][0]
            if 'data' in sheet_data and len(sheet_data['data']) > 0:
                grid_data = sheet_data['data'][0]
                if 'rowData' in grid_data:
                    for row_idx, row in enumerate(grid_data['rowData']):
                        if 'values' in row:
                            for col_idx, cell in enumerate(row['values']):
                                # Sprawdź czy komórka zawiera obrazek
                                if 'formattedValue' in cell and cell['formattedValue'].startswith('=IMAGE'):
                                    # Wyciągnij URL z formuły =IMAGE("url")
                                    formula = cell['formattedValue']
                                    start = formula.find('"') + 1
                                    end = formula.rfind('"')
                                    if start > 0 and end > start:
                                        image_url = formula[start:end]
                                        images_by_position[f"{row_idx},{col_idx}"] = image_url
                                        logger.info(f"Znaleziono obrazek na pozycji ({row_idx},{col_idx}): {image_url}")

        return images_by_position

    except Exception as e:
        logger.error(f"Błąd podczas pobierania obrazków z arkusza: {e}")
        return {}


def znajdz_zdjecie_dla_wiersza(sheet_id, row_index):
    """Znajduje zdjęcie dla konkretnego wiersza"""
    try:
        # Pobierz wszystkie obrazki z arkusza
        images = pobierz_zdjecia_z_arkusza(sheet_id)

        # Szukaj obrazka w wierszu (row_index+1 bo liczymy od 0, ale arkusz od 1)
        for position, url in images.items():
            pos_row, pos_col = map(int, position.split(','))
            if pos_row == row_index + 1:  # +1 bo pierwszy wiersz to nagłówki
                from image_utils import pobierz_i_zapisz_zdjecie
                return pobierz_i_zapisz_zdjecie(url, row_index)

        # Jeśli nie znaleziono obrazka w konkretnym wierszu, sprawdź kolumnę "sciezka_zdjecia" (indeks 3)
        target_position = f"{row_index + 1},3"  # Wiersz, kolumna D (sciezka_zdjecia)
        if target_position in images:
            from image_utils import pobierz_i_zapisz_zdjecie
            return pobierz_i_zapisz_zdjecie(images[target_position], row_index)

        return None

    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania zdjęcia dla wiersza {row_index}: {e}")
        return None


def wczytaj_arkusz(sheet_id):
    """Wczytuje dane z arkusza Google Sheets używając Google API Key"""
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A:Z"
        params = {
            'key': GOOGLE_API_KEY,
            'valueRenderOption': 'FORMATTED_VALUE'  # Zmieniono na FORMATTED_VALUE dla lepszego parsowania dat
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        values = data.get('values', [])

        if not values:
            logger.warning("Arkusz jest pusty")
            return []

        # Pierwszy wiersz to nagłówki
        headers = values[0]
        dane = []

        logger.info(f"Nagłówki arkusza: {headers}")

        # Przetwórz pozostałe wiersze
        for row_idx, row in enumerate(values[1:], start=1):
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = row[i]
                else:
                    row_dict[header] = ''
            dane.append(row_dict)
            logger.info(f"Wiersz {row_idx + 1}: {row_dict}")

        logger.info(f"Wczytano {len(dane)} wierszy z arkusza używając API Key")
        return dane

    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd HTTP podczas wczytywania arkusza: {e}")
        raise
    except Exception as e:
        logger.error(f"Błąd podczas wczytywania arkusza: {e}")
        raise


def test_parsowania_dat():
    """Testuje parsowanie dat z arkusza"""
    try:
        dane = wczytaj_arkusz(GOOGLE_SHEET_ID)
        print(f"\n📊 Znaleziono {len(dane)} wierszy w arkuszu")

        if dane:
            print("\n📋 Dostępne kolumny w arkuszu:")
            for header in dane[0].keys():
                print(f"  - '{header}'")

            print("\n📄 Dane pierwszego wiersza:")
            for key, value in dane[0].items():
                print(f"  {key}: '{value}' (typ: {type(value).__name__})")

        print("\n🔍 Sprawdzanie formatów dat:")

        for i, row in enumerate(dane):
            date_value = row.get('data_publikacji', '')
            print(f"\nWiersz {i + 2}: '{date_value}' (typ: {type(date_value).__name__})")

            if not date_value:
                print("  ❌ Brak daty")
                continue

            # Użyj nowej funkcji parsowania
            data_publikacji = parsuj_date_value(date_value)

            if data_publikacji:
                print(f"  ✅ Sparsowano: {data_publikacji}")

                # Sprawdź czy to dzisiaj
                dzisiejsza_data = datetime.now().date()
                if data_publikacji == dzisiejsza_data:
                    print(f"  🎯 TO DZISIAJ! ({dzisiejsza_data})")
                else:
                    dni_do_publikacji = (data_publikacji - dzisiejsza_data).days
                    if dni_do_publikacji > 0:
                        print(f"  📅 Za {dni_do_publikacji} dni")
                    else:
                        print(f"  📅 {abs(dni_do_publikacji)} dni temu")
            else:
                print(f"  ❌ Nie można sparsować")

        print(f"\n📅 Dzisiejsza data: {datetime.now().date()}")

    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")