import os
import subprocess
import re
from dagster import resource
from selenium import webdriver

from mosaic_conductor.selenium.wo.config import CHROME_DRIVER


def get_chrome_version():
    """Получает версию установленного Chrome в системе"""
    try:
        # Для Ubuntu/Debian
        if os.path.exists('/usr/bin/google-chrome'):
            result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
            version = re.search(r'Google Chrome (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if version:
                return version.group(1)
        
        # Для Windows
        elif os.path.exists('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'):
            result = subprocess.run(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                capture_output=True, text=True
            )
            version = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if version:
                return version.group(1)
    except Exception as e:
        print(f"Ошибка при определении версии Chrome: {e}")
    return None


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
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService

        options = ChromeOptions()
        options.headless = True
        
        # Базовые опции для стабильности
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Отключаем использование пользовательской директории
        options.add_argument("--incognito")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-cache")
        options.add_argument("--disable-offline-load-stale-cache")
        options.add_argument("--disk-cache-size=0")
        
        # Настройки прокси
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')

        # Для Chrome задаем временную папку загрузки через preferences
        prefs = {
            "download.default_directory": temp_download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        options.add_experimental_option("prefs", prefs)

        # Определяем версию Chrome
        chrome_version = get_chrome_version()
        if chrome_version:
            context.log.info(f"Обнаружена версия Chrome: {chrome_version}")
            # Извлекаем мажорную версию (например, из 120.0.6099.109 получаем 120)
            major_version = chrome_version.split('.')[0]
            context.log.info(f"Используем драйвер для версии Chrome {major_version}")
            service = ChromeService(
                ChromeDriverManager(driver_version=major_version).install()
            )
        else:
            context.log.warning("Не удалось определить версию Chrome, используется последняя версия драйвера")
            service = ChromeService(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)
    else:
        raise ValueError("Поддерживаются только 'firefox' и 'chrome'")

    context.log.info(f"Браузер {browser} успешно запущен.")

    driver.target_url = target_url

    try:
        yield driver
    finally:
        context.log.info("Закрытие браузера.")
        driver.quit()
