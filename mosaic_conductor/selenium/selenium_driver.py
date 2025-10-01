import os
import time
from dagster import resource
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
import tempfile
import subprocess
import platform
import socket
import requests
import glob

from mosaic_conductor.selenium.config import CHROME_DRIVER


def get_chrome_version():
    try:
        system = platform.system().lower()
        if system == 'windows':
            cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            return output.strip().split()[-1]
        elif system == 'linux':
            # Пробуем разные пути к Chrome в Linux
            chrome_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/snap/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium'
            ]

            for path in chrome_paths:
                if os.path.exists(path):
                    try:
                        output = subprocess.check_output([path, '--version'], stderr=subprocess.STDOUT).decode('utf-8')
                        return output.strip().split()[-1]
                    except subprocess.CalledProcessError:
                        continue

            # Если не нашли Chrome, пробуем через which
            try:
                chrome_path = subprocess.check_output(['which', 'google-chrome']).decode('utf-8').strip()
                output = subprocess.check_output([chrome_path, '--version'], stderr=subprocess.STDOUT).decode('utf-8')
                return output.strip().split()[-1]
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            return "Chrome не найден в системе"
        else:
            return f"Неподдерживаемая операционная система: {system}"
    except Exception as e:
        return f"Не удалось определить версию Chrome: {str(e)}"


def is_port_in_use(port):
    """Проверяет, занят ли порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_available_port():
    """Находит свободный порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def check_internet_connection():
    """Проверяет доступность интернета."""
    try:
        response = requests.get('https://www.google.com', timeout=5)
        return response.status_code == 200
    except:
        return False


def find_local_chromedriver():
    """Ищет локальный chromedriver в системе."""
    possible_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        '/opt/chromedriver',
        './chromedriver',
        './utils/geckodriver.exe',  # fallback на geckodriver если есть
        './utils/chromedriver.exe',  # возможный путь к chromedriver
    ]
    
    # Ищем в текущей директории и подпапках
    current_dir = os.getcwd()
    search_patterns = [
        os.path.join(current_dir, '**/chromedriver*'),
        os.path.join(current_dir, '**/geckodriver*'),
        os.path.join(current_dir, 'utils/**/chromedriver*'),
        os.path.join(current_dir, 'utils/**/geckodriver*'),
    ]
    
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            if os.path.isfile(match) and os.access(match, os.X_OK):
                return match
    
    # Проверяем стандартные пути
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None


def get_chromedriver_offline():
    """Получает путь к chromedriver в офлайн режиме."""
    # Сначала проверяем переменную окружения
    if CHROME_DRIVER and os.path.exists(CHROME_DRIVER):
        return CHROME_DRIVER
    
    # Ищем локальный драйвер
    local_driver = find_local_chromedriver()
    if local_driver:
        return local_driver
    
    # Если ничего не найдено, возвращаем None
    return None


@resource(
    config_schema={
        "browser": str,
        "destination_folder": str,  # Конечная папка (OMS_TALON_FOLDER)
        "temp_download_folder": str,  # Временная папка для загрузок (например, "uploads/talon")
        "target_url": str
    }
)
def selenium_driver_resource(context):
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)
    browser = context.resource_config.get("browser")
    destination_folder = context.resource_config.get("destination_folder")
    temp_download_folder = context.resource_config.get("temp_download_folder")
    target_url = context.resource_config.get("target_url")

    context.log.info(f"Выбран браузер: {browser}")
    context.log.info(f"Конечная папка для сохранения: {destination_folder}")
    context.log.info(f"Временная папка для загрузок: {temp_download_folder}")
    context.log.info(f"Целевой URL: {target_url}")
    context.log.info(f"Операционная система: {platform.system()} {platform.release()}")
    context.log.info(f"Путь к текущей директории: {os.getcwd()}")

    # Создаем конечную папку, если не существует
    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
            context.log.info(f"Папка {destination_folder} создана.")
        except Exception as e:
            context.log.error(f"Ошибка при создании папки {destination_folder}: {e}")

    # Создаем временную папку, если не существует
    if not os.path.exists(temp_download_folder):
        try:
            os.makedirs(temp_download_folder)
            context.log.info(f"Папка {temp_download_folder} создана.")
        except Exception as e:
            context.log.error(f"Ошибка при создании папки {temp_download_folder}: {e}")

    # Запуск драйвера в зависимости от браузера
    driver = None

    try:
        if browser == "firefox":
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.firefox.service import Service as FirefoxService

            options = FirefoxOptions()
            options.headless = True
            # Создаем профиль Firefox и назначаем его в опции
            profile = webdriver.FirefoxProfile()
            profile.set_preference("browser.download.folderList", 2)
            profile.set_preference("browser.download.dir", temp_download_folder)
            profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
            options.profile = profile  # назначаем профиль опциям
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)

        elif browser == "chrome":
            chrome_version = get_chrome_version()
            context.log.info(f"Установленная версия Chrome: {chrome_version}")

            # Настройка Chrome с дополнительными параметрами для стабильности
            options = ChromeOptions()
            options.add_argument("--headless=new")  # Новая версия headless для Chrome
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-setuid-sandbox")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-software-rasterizer")

            # Дополнительные параметры для стабильности
            options.add_argument("--disable-features=NetworkService")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument('--proxy-server="direct://"')
            options.add_argument('--proxy-bypass-list=*')
            options.add_argument('--ignore-ssl-errors=yes')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')

            # Выделяем больше памяти для Chrome
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-application-cache')

            # Найдем свободный порт для remote debugging
            debug_port = find_available_port()
            options.add_argument(f"--remote-debugging-port={debug_port}")
            context.log.info(f"Используем порт для remote debugging: {debug_port}")

            user_data_dir = tempfile.mkdtemp()
            options.add_argument(f"--user-data-dir={user_data_dir}")

            # Для Chrome задаем временную папку загрузки через preferences
            prefs = {
                "download.default_directory": os.path.abspath(temp_download_folder),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "plugins.always_open_pdf_externally": True
            }
            options.add_experimental_option("prefs", prefs)

            # Отключаем раздражающие логи
            options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            try:
                driver_path = None
                
                # Сначала проверяем переменную окружения
                if CHROME_DRIVER and os.path.exists(CHROME_DRIVER):
                    context.log.info(f"Используем ChromeDriver из переменной окружения: {CHROME_DRIVER}")
                    driver_path = CHROME_DRIVER
                else:
                    # Проверяем доступность интернета
                    if check_internet_connection():
                        try:
                            context.log.info("Интернет доступен, пытаемся загрузить ChromeDriver через webdriver-manager")
                            driver_path = ChromeDriverManager().install()
                            context.log.info(f"Установлен ChromeDriver по пути: {driver_path}")
                        except Exception as e:
                            context.log.warning(f"Не удалось загрузить ChromeDriver через webdriver-manager: {e}")
                            context.log.info("Переходим к поиску локального драйвера")
                            driver_path = get_chromedriver_offline()
                    else:
                        context.log.warning("Интернет недоступен, ищем локальный ChromeDriver")
                        driver_path = get_chromedriver_offline()
                
                # Если драйвер не найден, пробуем найти локально
                if not driver_path:
                    context.log.info("Пытаемся найти локальный ChromeDriver")
                    driver_path = get_chromedriver_offline()
                
                if not driver_path:
                    raise Exception("Не удалось найти ChromeDriver. Установите драйвер вручную или проверьте подключение к интернету.")
                
                context.log.info(f"Используем ChromeDriver: {driver_path}")

                # Устанавливаем права на выполнение для ChromeDriver в Linux
                if platform.system().lower() == 'linux':
                    try:
                        os.chmod(driver_path, 0o755)
                        context.log.info("Установлены права на выполнение для ChromeDriver")
                    except Exception as e:
                        context.log.warning(f"Не удалось установить права на выполнение для ChromeDriver: {str(e)}")

                # Получаем версию ChromeDriver
                try:
                    driver_version = subprocess.check_output([driver_path, '--version']).decode('utf-8').strip()
                    context.log.info(f"Версия ChromeDriver: {driver_version}")
                except Exception as e:
                    context.log.warning(f"Не удалось определить версию ChromeDriver: {str(e)}")

                # Создаем сервис с явными параметрами
                service = ChromeService(
                    executable_path=driver_path,
                    log_path=os.path.join(os.getcwd(), "chromedriver.log"),
                    service_args=["--verbose"]
                )

                # Создаем веб-драйвер с несколькими попытками
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        context.log.info(f"Попытка {attempt + 1} создать Chrome WebDriver")
                        driver = webdriver.Chrome(service=service, options=options)
                        context.log.info("Chrome драйвер успешно инициализирован")
                        break
                    except Exception as e:
                        context.log.error(f"Ошибка при создании драйвера (попытка {attempt + 1}): {str(e)}")
                        if attempt < max_attempts - 1:
                            context.log.info("Ожидание перед следующей попыткой...")
                            time.sleep(5)
                        else:
                            raise

            except Exception as e:
                context.log.error(f"Критическая ошибка при инициализации Chrome драйвера: {str(e)}")
                raise

        if not driver:
            raise ValueError("Не удалось создать веб-драйвер")

        context.log.info(f"Браузер {browser} успешно запущен.")

        # Устанавливаем глобальные таймауты
        driver.implicitly_wait(30)  # Увеличиваем неявное ожидание
        driver.set_page_load_timeout(60)  # Устанавливаем таймаут загрузки страницы

        # Добавляем URL в объект драйвера
        driver.target_url = target_url

        # Проверяем работоспособность драйвера
        try:
            driver.get("about:blank")
            context.log.info("Драйвер успешно загрузил пустую страницу")
        except Exception as e:
            context.log.error(f"Драйвер не смог загрузить пустую страницу: {e}")
            raise

        yield driver

    except Exception as e:
        context.log.error(f"Произошла ошибка в ресурсе selenium_driver_resource: {e}")
        raise

    finally:
        context.log.info("Закрытие браузера.")
        if driver:
            try:
                driver.quit()
                context.log.info("Браузер успешно закрыт")
            except Exception as e:
                context.log.error(f"Ошибка при закрытии браузера: {e}")
