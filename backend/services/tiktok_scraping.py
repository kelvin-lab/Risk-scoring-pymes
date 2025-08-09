import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import re
import logging
import os

# Configurar logging para mostrar solo advertencias y errores
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TikTokScraper:
    def __init__(self, use_selenium=True, headless=True):
        self.use_selenium = use_selenium
        self.session = None
        self.driver = None
        if use_selenium:
            self._setup_selenium(headless)
        else:
            self._setup_session()

    def _setup_selenium(self, headless=True):
        from selenium.webdriver.chrome.service import Service

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")

        # Opciones para evitar detección y mejorar estabilidad
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Opciones para suprimir logs de la consola
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument('--silent')

        # Preferencias para notificaciones
        chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values": {"notifications": 2}})
        
        # Configuración del servicio de ChromeDriver para que no muestre logs
        service = Service(service_args=['--log-level=OFF'])
        
        # Ocultar la ventana de la consola del driver en Windows
        if os.name == 'nt':
            service.creation_flags = 0x08000000 # CREATE_NO_WINDOW

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            logger.error(f"Error configurando Selenium: {e}. Intentando fallback.")
            try:
                # Fallback sin servicio personalizado
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e2:
                logger.error(f"Error en fallback de Selenium: {e2}")
                raise

    def _setup_session(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def _find_element_text(self, selectors, wait_time=3):
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                return element.text.strip()
            except (TimeoutException, NoSuchElementException):
                continue
        return None

    def get_tiktok_stats_selenium(self, username):
        if not self.driver:
            logger.error("Driver de Selenium no está configurado.")
            return None

        username = username.replace('@', '').strip()
        base_url = os.getenv("TIKTOK_BASE_URL", "https://www.tiktok.com")
        url = f"{base_url}/@{username}"
        logger.info(f"Accediendo a: {url}")

        try:
            self.driver.get(url)
            time.sleep(5)

            stats = {'username': username, 'url': url, 'found': False}

            followers_count = self._find_element_text([
                "//strong[@data-e2e='followers-count']",
                "//strong[contains(@title, 'Followers')]"
            ])
            if followers_count:
                stats['followers'] = self._parse_count(followers_count)

            following_count = self._find_element_text([
                "//strong[@data-e2e='following-count']",
                "//strong[contains(@title, 'Following')]"
            ])
            if following_count:
                stats['following'] = self._parse_count(following_count)

            likes_count = self._find_element_text([
                "//strong[@data-e2e='likes-count']",
                "//strong[contains(@title, 'Likes')]"
            ])
            if likes_count:
                stats['likes'] = self._parse_count(likes_count)
            
            stats['display_name'] = self._find_element_text(["//h1[@data-e2e='user-title']"])
            stats['bio'] = self._find_element_text(["//h2[@data-e2e='user-bio']"])

            if any(key in stats for key in ['followers', 'following', 'likes']):
                stats['found'] = True
            else:
                stats.update(self._extract_from_metadata())

            return stats

        except Exception as e:
            logger.error(f"Error general en Selenium para @{username}: {e}")
            return {'username': username, 'error': str(e), 'found': False}

    def _extract_from_metadata(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            stats = {}
            
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if self._extract_from_json(data, stats):
                        return stats
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = meta_desc['content']
                numbers = re.findall(r'([\d,]+(?:\.\d+)?[KMB]?)', content)
                if numbers:
                    stats['meta_numbers'] = numbers
            
            return stats
        except Exception as e:
            logger.error(f"Error extrayendo metadatos: {e}")
            return {}

    def _extract_from_json(self, data, stats):
        if isinstance(data, dict):
            user_stats = data.get('userStats', {})
            stats['followers'] = user_stats.get('followerCount')
            stats['following'] = user_stats.get('followingCount')
            stats['likes'] = user_stats.get('heartCount')
            return any([stats['followers'], stats['following'], stats['likes']])
        return False

    def _parse_count(self, count_str):
        if not count_str: return 0
        count_str = count_str.replace(',', '').upper()
        multipliers = {'K': 1e3, 'M': 1e6, 'B': 1e9}
        for suffix, multiplier in multipliers.items():
            if suffix in count_str:
                return int(float(count_str.replace(suffix, '')) * multiplier)
        try:
            return int(count_str)
        except ValueError:
            return count_str

    def get_tiktok_stats(self, username):
        if self.use_selenium and self.driver:
            return self.get_tiktok_stats_selenium(username)
        else:
            return {'username': username, 'error': 'Requests method is not reliable.', 'found': False}

    def close(self):
        if self.driver:
            self.driver.quit()

def print_stats(stats):
    """Imprime las estadísticas de forma organizada."""
    print("\n" + "="*50)
    print(f"Estadísticas de TikTok - @{stats.get('username', 'N/A')}")
    print("="*50)
    
    if stats.get('found'):
        print("Perfil encontrado")
        if 'display_name' in stats and stats['display_name']:
            print(f"  Nombre: {stats['display_name']}")
        if 'followers' in stats:
            print(f"  Seguidores: {stats['followers']:,}")
        if 'following' in stats:
            print(f"  Siguiendo: {stats['following']:,}")
        if 'likes' in stats:
            print(f"  Likes: {stats['likes']:,}")
        if 'bio' in stats and stats['bio']:
            print(f"  Bio: {stats['bio']}")
    else:
        print("No se pudieron obtener estadísticas completas.")
    
    if 'error' in stats:
        print(f"Error: {stats['error']}")
    
    print(f"URL: {stats.get('url', 'N/A')}")

def main():
    """Función principal de ejemplo."""
    USERNAME = 'alfanetecuador'
    
    scraper = TikTokScraper(use_selenium=True, headless=True)
    
    try:
        stats = scraper.get_tiktok_stats(USERNAME)
        if stats:
            print_stats(stats)
    except Exception as e:
        print(f"Ocurrió un error en la ejecución principal: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()