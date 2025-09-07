import os
import tempfile
from instagrapi import Client
from config import logger
from google_sheets import gdrive_to_direct
from image_utils import pobierz_i_zapisz_zdjecie, przetworz_lokalny_obraz


def zaloguj_instagrama(username, password):
    """Loguje się do Instagrama"""
    try:
        cl = Client()
        cl.login(username, password)
        logger.info("Pomyślnie zalogowano do Instagrama")
        return cl
    except Exception as e:
        logger.error(f"Błąd podczas logowania do Instagrama: {e}")
        raise


def opublikuj_post(cl, sciezka_zdjecia, opis):
    """Publikuje post na Instagramie"""
    try:
        # Sprawdź czy to URL czy lokalna ścieżka
        if sciezka_zdjecia.startswith(('http://', 'https://')):
            # To jest URL - pobierz obrazek
            logger.info(f"Wykryto URL obrazka: {sciezka_zdjecia}")
            
            # Konwertuj URL Google Drive na bezpośredni link
            direct_url = gdrive_to_direct(sciezka_zdjecia)
            if direct_url != sciezka_zdjecia:
                logger.info(f"Przekonwertowano URL Google Drive: {direct_url}")
            
            # Pobierz obrazek
            temp_path = pobierz_i_zapisz_zdjecie(direct_url, "post")
            if not temp_path:
                raise Exception(f"Nie udało się pobrać obrazka z URL: {sciezka_zdjecia}")
            
            try:
                # Publikuj post z pobranym obrazkiem
                media = cl.photo_upload(temp_path, opis)
                logger.info(f"Pomyślnie opublikowano post: {media.pk}")
                return media
            finally:
                # Usuń tymczasowy plik
                try:
                    os.remove(temp_path)
                    logger.info(f"Usunięto tymczasowy plik: {temp_path}")
                except Exception as e:
                    logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")
        else:
            # To jest lokalna ścieżka
            if not os.path.exists(sciezka_zdjecia):
                raise FileNotFoundError(f"Nie znaleziono pliku: {sciezka_zdjecia}")

            # Przetwórz lokalny plik, aby miał odpowiednie proporcje
            temp_path = przetworz_lokalny_obraz(sciezka_zdjecia)
            
            try:
                media = cl.photo_upload(temp_path, opis)
                logger.info(f"Pomyślnie opublikowano post: {media.pk}")
                return media
            finally:
                # Usuń tymczasowy plik jeśli został utworzony
                if temp_path != sciezka_zdjecia:
                    try:
                        os.remove(temp_path)
                        logger.info(f"Usunięto tymczasowy plik: {temp_path}")
                    except Exception as e:
                        logger.warning(f"Nie można usunąć tymczasowego pliku: {e}")
            
    except Exception as e:
        logger.error(f"Błąd podczas publikowania posta: {e}")
        raise