import os
import requests
import tempfile
import uuid
from PIL import Image
from config import logger


def pobierz_domyslne_zdjecie():
    """Zwraca ścieżkę do domyślnego zdjęcia z folderu images"""
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    
    # Lista możliwych nazw plików
    possible_names = ['photo.jpg', 'photo.jpeg', 'photo.png', 'image.jpg', 'image.jpeg', 'image.png', 'default.jpg']
    
    # Sprawdź czy któryś z plików istnieje
    for filename in possible_names:
        image_path = os.path.join(images_dir, filename)
        if os.path.exists(image_path):
            logger.info(f"Znaleziono zdjęcie: {image_path}")
            return image_path
    
    # Jeśli nie znaleziono konkretnych nazw, weź pierwszy dostępny plik obrazu
    if os.path.exists(images_dir):
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        for filename in os.listdir(images_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(images_dir, filename)
                logger.info(f"Znaleziono zdjęcie: {image_path}")
                return image_path
    
    logger.warning("Nie znaleziono żadnego zdjęcia w folderze images")
    return None


def dostosuj_proporcje_instagram(img):
    """Dostosowuje proporcje obrazu do wymagań Instagrama"""
    width, height = img.size
    aspect_ratio = width / height
    
    # Instagram akceptuje proporcje:
    # - Kwadrat: 1:1 (1.0)
    # - Portret: 4:5 (0.8)
    # - Krajobraz: 1.91:1 (1.91)
    
    # Określ docelowe proporcje na podstawie obecnych
    if aspect_ratio > 1.5:
        # Szeroki obraz - dostosuj do krajobrazu (1.91:1)
        target_ratio = 1.91
        target_width = int(height * target_ratio)
        target_height = height
    elif aspect_ratio < 0.9:
        # Wysoki obraz - dostosuj do portretu (4:5)
        target_ratio = 0.8
        target_width = width
        target_height = int(width / target_ratio)
    else:
        # Zbliżony do kwadratu - zrób kwadrat (1:1)
        target_ratio = 1.0
        size = min(width, height)
        target_width = size
        target_height = size
    
    # Jeśli obraz jest mniejszy niż docelowy, po prostu wykadruj
    if width >= target_width and height >= target_height:
        # Wykadruj z centrum
        left = (width - target_width) // 2
        top = (height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        img = img.crop((left, top, right, bottom))
    else:
        # Jeśli obraz jest za mały, zmień rozmiar zachowując proporcje, a potem wykadruj
        # Oblicz skalę potrzebną do pokrycia docelowego rozmiaru
        scale_x = target_width / width
        scale_y = target_height / height
        scale = max(scale_x, scale_y)
        
        # Przeskaluj obraz
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Wykadruj do docelowego rozmiaru
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        img = img.crop((left, top, right, bottom))
    
    logger.info(f"Dostosowano proporcje obrazu do {img.size[0]}x{img.size[1]} (ratio: {img.size[0]/img.size[1]:.2f})")
    return img


def pobierz_i_zapisz_zdjecie(image_url, row_index):
    """Pobiera zdjęcie z URL i zapisuje jako tymczasowy plik"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(image_url, headers=headers, stream=True)
        response.raise_for_status()

        # Utwórz tymczasowy plik
        temp_dir = tempfile.gettempdir()
        filename = f"instagram_image_{row_index}_{uuid.uuid4().hex[:8]}.jpg"
        temp_path = os.path.join(temp_dir, filename)

        # Zapisz obrazek
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Sprawdź czy to prawidłowy obrazek i ewentualnie przekonwertuj
        try:
            with Image.open(temp_path) as img:
                # Konwertuj do RGB jeśli potrzeba (usuwa kanał alpha)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Sprawdź proporcje i dostosuj do wymagań Instagrama
                width, height = img.size
                aspect_ratio = width / height
                
                # Jeśli obraz nie ma odpowiednich proporcji, dostosuj je
                if not (abs(aspect_ratio - 1.0) < 0.05 or  # Kwadrat
                        abs(aspect_ratio - 0.8) < 0.05 or  # Portret
                        abs(aspect_ratio - 1.91) < 0.1):   # Krajobraz
                    logger.info(f"Dostosowywanie proporcji pobranego obrazu (obecne: {aspect_ratio:.2f})")
                    img = dostosuj_proporcje_instagram(img)

                # Zapisz jako JPEG
                img.save(temp_path, 'JPEG', quality=95)
        except Exception as e:
            logger.warning(f"Nie można przetworzyć obrazka: {e}")

        logger.info(f"Pobrano zdjęcie: {temp_path}")
        return temp_path

    except Exception as e:
        logger.error(f"Błąd podczas pobierania zdjęcia z {image_url}: {e}")
        return None


def przetworz_lokalny_obraz(sciezka_zdjecia):
    """Przetwarza lokalny obraz, aby miał odpowiednie proporcje dla Instagrama"""
    try:
        with Image.open(sciezka_zdjecia) as img:
            # Konwertuj do RGB jeśli potrzeba
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Sprawdź proporcje
            width, height = img.size
            aspect_ratio = width / height
            
            # Jeśli obraz już ma odpowiednie proporcje, zwróć oryginalną ścieżkę
            if (abs(aspect_ratio - 1.0) < 0.05 or  # Kwadrat
                abs(aspect_ratio - 0.8) < 0.05 or  # Portret
                abs(aspect_ratio - 1.91) < 0.1):   # Krajobraz
                logger.info("Obraz ma już odpowiednie proporcje dla Instagrama")
                return sciezka_zdjecia
            
            # Dostosuj proporcje
            img = dostosuj_proporcje_instagram(img)
            
            # Zapisz do tymczasowego pliku
            temp_dir = tempfile.gettempdir()
            filename = f"instagram_processed_{uuid.uuid4().hex[:8]}.jpg"
            temp_path = os.path.join(temp_dir, filename)
            
            img.save(temp_path, 'JPEG', quality=95)
            logger.info(f"Przetworzono lokalny obraz: {temp_path}")
            return temp_path
            
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania lokalnego obrazu: {e}")
        return sciezka_zdjecia  # Zwróć oryginalną ścieżkę w przypadku błędu