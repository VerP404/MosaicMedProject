import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob
import shutil
from bs4 import BeautifulSoup
from django.conf import settings

# Установка уровня логирования для selenium и urllib3
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Логи уровня INFO и выше будут выводиться

def selenium_oms_chrome(username, password, start_date, end_date, start_date_treatment):
    def parse_html():
        source_data = driver.page_source
        soup = BeautifulSoup(source_data, 'html.parser')
        return soup

    def ojidanie():
        flag = True
        while flag:
            try:
                soup = parse_html()
                info = soup.find('h2', {'class': 'jss170 jss176'}).get_text()
                if info == 'Пожалуйста, подождите...':
                    flag = True
                    time.sleep(2)
                else:
                    flag = False
            except AttributeError:
                flag = False

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
        driver.get('http://10.36.0.142:9000/')
        logger.info("Открыт сайт OMS")
        logger.info(
            f"ПАРАМЕТРЫ:\n"
            f"период изменения - начало: {start_date}\n"
            f"период изменения - окончание: {end_date}\n"
            f"период окончания лечения начало: {start_date_treatment}")

        # Авторизация
        login_input = driver.find_element(By.XPATH, '/html/body/div/form/input[1]')
        login_input.clear()
        login_input.send_keys(username)
        password_input = driver.find_element(By.XPATH, '/html/body/div/form/input[2]')
        password_input.clear()
        password_input.send_keys(password)
        password_input.send_keys(Keys.ENTER)
        logger.info("Авторизация выполнена")
        time.sleep(30)
        wait = WebDriverWait(driver, 120)
        logger.info("Открытие меню")

        # Ввод даты начала лечения
        start_date_input_treatment = driver.find_element(By.XPATH,
                                                         '//*[@id="menu"]/div/div[1]/div/div[1]/div/div[2]/div[1]/div[1]/div/div/div/input')
        start_date_input_treatment.clear()
        start_date_input_treatment.send_keys(start_date_treatment)

        logger.info("Открытие фильтра")
        # Открытие фильтра
        open_filter_step1 = driver.find_element(By.XPATH,
                                                '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[1]/div[2]')
        open_filter_step1.click()
        open_filter_step2 = driver.find_element(By.XPATH,
                                                '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[1]/div[2]')
        open_filter_step2.click()
        logger.info("Даты изменения талонов")
        # Даты изменения талонов
        start_date_input = driver.find_element(By.XPATH,
                                               '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[7]/div/div[2]/div[1]/div/div/div/input')
        start_date_input.clear()
        start_date_input.send_keys(start_date)

        end_date_input = driver.find_element(By.XPATH,
                                             '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[7]/div/div[2]/div[2]/div/div/div/input')
        end_date_input.clear()
        end_date_input.send_keys(end_date)

        logger.info("Загрузка талонов")
        # Нажимаем "Найти"
        find_button = driver.find_element(By.XPATH,
                                          '//*[@id="menu"]/div/div[1]/div/div[4]/div/div[4]/div/button')
        find_button.click()
        ojidanie()
        time.sleep(5)
        # Ожидание загрузки
        loading_indicator_locator = (By.XPATH,
                                     '//h2[contains(@class, "jss170") and contains(@class, "jss176") and text()="Пожалуйста, подождите..."]')
        wait.until(EC.invisibility_of_element_located(loading_indicator_locator))
        time.sleep(5)
        logger.info("Выбираем все результаты")

        # Выбираем все результаты
        select_all_checkbox = driver.find_element(By.XPATH,
                                                  '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span')
        select_all_checkbox.click()
        # Скачивание файла
        logger.info("Начинаем скачивание файла")
        download_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[3]/div/div/div[5]/a/button')
        download_button.click()
        time.sleep(5)  # Ожидание завершения загрузки

        # Проверяем, что файл загрузился
        file_pattern = os.path.join(download_folder, 'journal_*.csv')
        files = glob.glob(file_pattern)

        if files:
            latest_file = max(files, key=os.path.getctime)
            new_file_path = os.path.join(download_folder, 'downloaded_file.csv')
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