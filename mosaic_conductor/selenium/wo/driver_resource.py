from dagster import resource, Field, String
import os

from .config import DEFAULT_BROWSER


@resource(
    config_schema={
        "browser": Field(String, is_required=False, default_value=DEFAULT_BROWSER),
        "destination_folder": Field(String, is_required=False, default_value="/default/destination/path")
    }
)
def selenium_driver_resource(context):
    browser = context.resource_config.get("browser", DEFAULT_BROWSER)
    destination_folder = context.resource_config.get("destination_folder")

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    if browser.lower() == "firefox":
        from webdriver_manager.firefox import GeckoDriverManager
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
        from selenium import webdriver

        options = Options()
        options.headless = True
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
    elif browser.lower() == "chrome":
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium import webdriver

        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        prefs = {
            "download.default_directory": destination_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        raise ValueError("Поддерживаются только 'firefox' и 'chrome'")

    driver.implicitly_wait(10)
    context.log.info(f"Инициализирован Selenium драйвер для {browser}")

    try:
        yield driver
    finally:
        driver.quit()
        context.log.info("Selenium драйвер закрыт")
