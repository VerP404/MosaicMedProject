import os
from dagster import resource
from selenium import webdriver

@resource(
    config_schema={
        "browser": str,
        "destination_folder": str,         # Конечная папка (OMS_TALON_FOLDER)
        "temp_download_folder": str,         # Временная папка для загрузок (например, "uploads/talon")
        "target_url": str
    }
)
def selenium_driver_resource(context):
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
        import tempfile

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
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        raise ValueError("Поддерживаются только 'firefox' и 'chrome'")

    context.log.info(f"Браузер {browser} успешно запущен.")

    try:
        yield driver
    finally:
        context.log.info("Закрытие браузера.")
        driver.quit()
