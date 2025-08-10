import os
import time
import threading
import tempfile
from datetime import datetime, time as dt_time
from config import GOOGLE_SHEET_ID, INSTA_USERNAME, INSTA_PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, logger
from google_sheets import wczytaj_arkusz, parsuj_date_value, znajdz_zdjecie_dla_wiersza
from instagram import zaloguj_instagrama, opublikuj_post
from telegram_bot import wyslij_telegram
from image_utils import pobierz_domyslne_zdjecie


def harmonogram():
    """Główna funkcja harmonogramu"""

    def zadanie():
        try:
            logger.info("Rozpoczynanie zadania publikacji...")
            dane = wczytaj_arkusz(GOOGLE_SHEET_ID)
            cl = zaloguj_instagrama(INSTA_USERNAME, INSTA_PASSWORD)
            zmieniono = False
            dzisiejsza_data = datetime.now().date()

            for i, row in enumerate(dane):
                # Sprawdź czy post nie został już opublikowany
                if str(row.get('czy_opublikowano', '')).lower() in ['true', 'tak', '1']:
                    continue

                try:
                    # Parsuj datę publikacji używając nowej funkcji
                    date_value = row.get('data_publikacji', '')
                    if not date_value:
                        logger.warning(f"Brak daty publikacji dla wiersza {i + 2}")
                        continue

                    data_publikacji = parsuj_date_value(date_value)

                    if not data_publikacji:
                        logger.warning(f"Nie można sparsować daty: '{date_value}' w wierszu {i + 2}")
                        logger.info(f"Obsługiwane formaty: DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY lub liczba")
                        continue

                    # Sprawdź czy to dzisiaj
                    if data_publikacji == dzisiejsza_data:
                        # Sprawdź różne możliwe nazwy kolumn
                        possible_content_keys = ['tresc_postu', 'treść_postu', 'content', 'tekst', 'opis']
                        possible_tags_keys = ['tagi', 'tags', 'hashtags', 'hash']
                        possible_image_keys = ['sciezka_zdjecia', 'ścieżka_zdjęcia', 'image', 'zdjecie', 'photo',
                                               'path']

                        tresc_postu = ''
                        tagi = ''
                        sciezka_zdjecia = ''

                        # Znajdź treść posta
                        for key in possible_content_keys:
                            if key in row and row[key]:
                                tresc_postu = str(row[key]).strip()
                                break

                        # Znajdź tagi
                        for key in possible_tags_keys:
                            if key in row and row[key]:
                                tagi = str(row[key]).strip()
                                break

                        # Znajdź ścieżkę zdjęcia
                        for key in possible_image_keys:
                            if key in row and row[key]:
                                sciezka_zdjecia = str(row[key]).strip()
                                break

                        logger.info(f"DEBUG - Wiersz {i + 2}:")
                        logger.info(f"  data_publikacji: {data_publikacji}")
                        logger.info(f"  tresc_postu: '{tresc_postu}'")
                        logger.info(f"  tagi: '{tagi}'")
                        logger.info(f"  sciezka_zdjecia: '{sciezka_zdjecia}'")
                        logger.info(f"  Wszystkie klucze: {list(row.keys())}")
                        logger.info(f"  Wszystkie wartości: {list(row.values())}")

                        if not tresc_postu or tresc_postu == 'nan':
                            logger.warning(f"Brak treści posta dla wiersza {i + 2}")
                            continue

                        # Jeśli brak ścieżki, spróbuj pobrać zdjęcie z arkusza
                        if not sciezka_zdjecia or sciezka_zdjecia == 'nan':
                            logger.info(f"Próbuję pobrać zdjęcie z arkusza dla wiersza {i + 2}")
                            sciezka_zdjecia = znajdz_zdjecie_dla_wiersza(GOOGLE_SHEET_ID, i)

                        # Jeśli nadal brak zdjęcia, użyj zdjęcia z folderu images
                        if not sciezka_zdjecia:
                            logger.info(f"Próbuję użyć zdjęcia z folderu images dla wiersza {i + 2}")
                            sciezka_zdjecia = pobierz_domyslne_zdjecie()

                        if not sciezka_zdjecia:
                            logger.warning(f"Brak ścieżki zdjęcia dla wiersza {i + 2} - pomijam post")
                            continue

                        opis = f"{tresc_postu}"
                        if tagi and tagi != 'nan':
                            opis += f"\n\n{tagi}"

                        # Publikuj post
                        logger.info(f"Publikowanie posta z wiersza {i + 2}")
                        logger.info(f"Zdjęcie: {sciezka_zdjecia}")
                        logger.info(f"Opis: {opis[:100]}...")

                        media = opublikuj_post(cl, sciezka_zdjecia, opis)

                        # Utwórz link do posta
                        post_url = f"https://www.instagram.com/p/{media.code}/"

                        # Wyślij powiadomienie
                        wyslij_telegram(
                            TELEGRAM_BOT_TOKEN,
                            TELEGRAM_CHAT_ID,
                            f"✅ <b>Post opublikowany!</b>\n\n"
                            f"📝 Treść: {tresc_postu[:100]}{'...' if len(tresc_postu) > 100 else ''}\n"
                            f"📅 Data: {data_publikacji}\n"
                            f"🖼️ Zdjęcie: {os.path.basename(sciezka_zdjecia)}\n"
                            f"🔗 Link: {post_url}"
                        )

                        # Oznacz jako opublikowany (tylko w pamięci, bo używamy API Key)
                        dane[i]['czy_opublikowano'] = "TRUE"
                        logger.info(f"Oznaczono wiersz {i + 2} jako opublikowany (wymaga ręcznej aktualizacji w arkuszu)")
                        zmieniono = True

                        # Usuń tymczasowy plik jeśli został utworzony
                        if sciezka_zdjecia.startswith(tempfile.gettempdir()):
                            try:
                                os.remove(sciezka_zdjecia)
                                logger.info(f"Usunięto tymczasowy plik: {sciezka_zdjecia}")
                            except Exception as e:
                                logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")

                except Exception as e:
                    logger.error(f"Błąd podczas przetwarzania wiersza {i + 2}: {e}")
                    wyslij_telegram(
                        TELEGRAM_BOT_TOKEN,
                        TELEGRAM_CHAT_ID,
                        f"❌ Błąd podczas publikacji wiersza {i + 2}: {str(e)}"
                    )

            if not zmieniono:
                logger.info("Brak postów do publikacji na dziś")

        except Exception as e:
            logger.error(f"Błąd głównego zadania: {e}")
            wyslij_telegram(
                TELEGRAM_BOT_TOKEN,
                TELEGRAM_CHAT_ID,
                f"❌ <b>Błąd krytyczny:</b>\n{str(e)}"
            )

    # Uruchom zadanie w osobnym wątku
    thread = threading.Thread(target=zadanie)
    thread.daemon = True
    thread.start()

    # Ustaw harmonogram
    while True:
        current_time = datetime.now().time()
        target_time = dt_time(16, 0)  # 16:00

        if current_time.hour == target_time.hour and current_time.minute == target_time.minute:
            if not thread.is_alive():
                logger.info("Uruchamianie zaplanowanego zadania...")
                thread = threading.Thread(target=zadanie)
                thread.daemon = True
                thread.start()

        time.sleep(60)  # Sprawdzaj co minutę