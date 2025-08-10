import os
import tempfile
from config import GOOGLE_SHEET_ID, INSTA_USERNAME, INSTA_PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from google_sheets import wczytaj_arkusz, test_parsowania_dat, znajdz_zdjecie_dla_wiersza
from instagram import zaloguj_instagrama, opublikuj_post
from telegram_bot import wyslij_telegram
from image_utils import pobierz_domyslne_zdjecie


def test_publikacji():
    """Testuje publikację jednego posta"""
    try:
        print("🧪 Test publikacji...")
        dane = wczytaj_arkusz(GOOGLE_SHEET_ID)
        cl = zaloguj_instagrama(INSTA_USERNAME, INSTA_PASSWORD)

        if not dane:
            print("❌ Brak danych w arkuszu")
            return

        # Weź pierwszy wiersz do testu
        row = dane[0]
        print(f"📄 Testowanie pierwszego wiersza: {row}")

        # Sprawdź różne możliwe nazwy kolumn
        possible_content_keys = ['tresc_postu', 'treść_postu', 'content', 'tekst', 'opis']
        possible_tags_keys = ['tagi', 'tags', 'hashtags', 'hash']
        possible_image_keys = ['sciezka_zdjecia', 'ścieżka_zdjęcia', 'image', 'zdjecie', 'photo', 'path']

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

        if not tresc_postu:
            print("❌ Brak treści posta")
            return

        # Jeśli brak ścieżki, spróbuj pobrać zdjęcie z arkusza
        if not sciezka_zdjecia:
            print("🔍 Próbuję pobrać zdjęcie z arkusza...")
            sciezka_zdjecia = znajdz_zdjecie_dla_wiersza(GOOGLE_SHEET_ID, 0)

        # Jeśli nadal brak zdjęcia, użyj zdjęcia z folderu images
        if not sciezka_zdjecia:
            print("🔍 Próbuję użyć zdjęcia z folderu images...")
            sciezka_zdjecia = pobierz_domyslne_zdjecie()

        if not sciezka_zdjecia:
            print("❌ Brak ścieżki zdjęcia")
            return

        opis = f"{tresc_postu}"
        if tagi:
            opis += f"\n\n{tagi}"

        print(f"📝 Treść: {tresc_postu}")
        print(f"🏷️ Tagi: {tagi}")
        print(f"🖼️ Zdjęcie: {sciezka_zdjecia}")
        print(f"📄 Pełny opis: {opis}")

        # Publikuj post
        print("📤 Publikowanie posta...")
        media = opublikuj_post(cl, sciezka_zdjecia, opis)

        print(f"✅ Post opublikowany pomyślnie! ID: {media.pk}")

        # Utwórz link do posta
        post_url = f"https://www.instagram.com/p/{media.code}/"

        # Wyślij powiadomienie
        wyslij_telegram(
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
            f"✅ <b>Test publikacji zakończony pomyślnie!</b>\n\n"
            f"📝 Treść: {tresc_postu[:100]}{'...' if len(tresc_postu) > 100 else ''}\n"
            f"🖼️ Zdjęcie: {os.path.basename(sciezka_zdjecia)}\n"
            f"🆔 ID posta: {media.pk}\n"
            f"🔗 Link: {post_url}"
        )

    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")
        wyslij_telegram(
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
            f"❌ <b>Błąd podczas testu publikacji:</b>\n{str(e)}"
        )