import os
from dagster import resource
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
import tempfile
import subprocess
import json
import platform

from mosaic_conductor.selenium.wo.config import CHROME_DRIVER

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

@resource(
    config_schema={
        "browser": str,
        "destination_folder": str,         # Конечная папка (OMS_TALON_FOLDER)
        "temp_download_folder": str,         # Временная папка для загрузок (например, "uploads/talon")
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

    # Создаем конечную папку, если не существует
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        context.log.info(f"Папка {destination_folder} создана.")

    # Создаем временную папку, если не существует
    if not os.path.exists(temp_download_folder):
        os.makedirs(temp_download_folder)
        context.log.info(f"Папка {temp_download_folder} создана.")

    # Запуск драйвера в зависимости от браузера
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
        
        options = ChromeOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')
        user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Для Chrome задаем временную папку загрузки через preferences
        prefs = {
            "download.default_directory": temp_download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        try:
            # Используем ChromeDriverManager для автоматического определения версии
            driver_path = ChromeDriverManager().install()
            context.log.info(f"Путь к ChromeDriver: {driver_path}")
            
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
            
            service = ChromeService(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            context.log.info("Chrome драйвер успешно инициализирован")
        except Exception as e:
            context.log.error(f"Ошибка при инициализации Chrome драйвера: {str(e)}")
            raise
    else:
        raise ValueError("Поддерживаются только 'firefox' и 'chrome'")

    context.log.info(f"Браузер {browser} успешно запущен.")

    driver.target_url = target_url

    try:
        yield driver
    finally:
        context.log.info("Закрытие браузера.")
        driver.quit()
