import logging
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob
from django.conf import settings

# Установка уровня логирования для selenium и urllib3
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Логи уровня INFO и выше будут выводиться


def selenium_iszl_people_chrome(username, password):
    def input_enter_xpath(xpath, text):
        perehod = driver.find_element(By.XPATH, xpath)
        perehod.send_keys(text, Keys.ENTER)

    def click_xpath(xpath):
        perehod = driver.find_element(By.XPATH, xpath)
        perehod.click()

    logger.info("Начало выполнения скрипта Selenium")
    try:
        # Настройка опций для Chrome
        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-features=VizDisplayCompositor")

        # Настройка папки загрузки
        download_folder = os.path.join(settings.BASE_DIR, 'imported_files')
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        prefs = {
            "download.default_directory": download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        # Автоматическая установка chromedriver с помощью webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        driver.get('http://10.36.29.2:8088/')
        logger.info("Открыт ИСЗЛ")

        # Авторизация
        login_input = driver.find_element(By.XPATH, '//*[@id="tbLogin"]')
        login_input.clear()
        login_input.send_keys(username)
        try:
            try:
                input_enter_xpath('//*[@id="tbPwd"]', password)
            except:
                input_enter_xpath('//*[@id="tbPwd"]', password)
        except:
            try:
                input_enter_xpath('//*[@id="tbPwd"]', password)
            except:
                input_enter_xpath('//*[@id="tbPwd"]', password)

        # Открываем меню и выбираем нужный пункт
        clickable = driver.find_element(By.XPATH, '//*[@id="mnuAtt"]/ul/li[1]')
        ActionChains(driver) \
            .click_and_hold(clickable) \
            .perform()
        perehod = driver.find_element(By.XPATH, '//*[@id="mnuAtt:submenu:2"]/li[3]/a')
        perehod.click()
        perehod.click()

        # Переход во внутренний фрейм
        perehod_v_frame = driver.find_element(By.XPATH, '//*[@id="ifMain"]')
        driver.switch_to.frame(perehod_v_frame)

        # Открываем форму выгрузки данных
        click_xpath('//*[@id="lbtnExternalData"]')

        # Переходим во фрейм модального окна
        perehod_v_frame = driver.find_element(By.XPATH, '//*[@id="ifDic"]')
        driver.switch_to.frame(perehod_v_frame)

        logger.info("Экспорт данных")

        # Нажимаем Экспорт данных
        click_xpath('//*[@id="lbtnExport"]')
        time.sleep(60)

        logger.info("Скачиваем файл")
        # Нажимаем Получить файл
        click_xpath('//*[@id="lbtnFile"]')
        time.sleep(60)

        # Проверяем, что файл загрузился
        file_pattern = os.path.join(download_folder, 'Att_MO_*.csv')
        files = glob.glob(file_pattern)

        if files:
            latest_file = max(files, key=os.path.getctime)
            new_file_path = os.path.join(download_folder, 'downloaded_Att_MO.csv')
            os.rename(latest_file, new_file_path)
            logger.info(f"Файл успешно загружен и перемещен в {new_file_path}")
            driver.quit()
            return True, new_file_path
        else:
            logger.error("Файл не был загружен")
            driver.quit()
            return False, None

    except Exception as e:
        logger.error(f"Ошибка при выполнении скрипта Selenium: {e}")
        return False, None
