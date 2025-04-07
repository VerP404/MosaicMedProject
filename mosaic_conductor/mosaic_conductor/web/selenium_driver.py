import os
from dagster import resource
from selenium import webdriver


@resource(config_schema={
    "browser": str,
    "destination_folder": str,
    "target_url": str
})
def selenium_driver_resource(context):
    browser = context.resource_config.get("browser")
    destination_folder = context.resource_config.get("destination_folder")
    target_url = context.resource_config.get("target_url")

    context.log.info(f"Выбран браузер: {browser}")
    context.log.info(f"Папка для загрузки: {destination_folder}")
    context.log.info(f"Целевой URL: {target_url}")

    # Создание папки, если не существует
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        context.log.info(f"Папка {destination_folder} создана, так как не существовала.")

    # Запуск драйвера в зависимости от выбранного браузера
    if browser == "firefox":
        from webdriver_manager.firefox import GeckoDriverManager
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.firefox.service import Service as FirefoxService

        options = FirefoxOptions()
        options.headless = True
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
    elif browser == "chrome":
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService

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
        # Настройка папки загрузки для Chrome через preferences
        prefs = {
            "download.default_directory": destination_folder,
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
        driver.get(target_url)
        context.log.info(f"Страница {target_url} успешно открыта.")
    except Exception as e:
        context.log.info(f"Ошибка при открытии страницы {target_url}: {e}")
        driver.quit()
        raise e

    try:
        yield driver
    finally:
        context.log.info("Закрытие браузера.")
        driver.quit()
