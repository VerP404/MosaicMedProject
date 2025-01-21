import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
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
# Устанавливаем файл для записи логов
LOG_FILE = os.path.join(os.path.dirname(__file__), "selenium_debug.log")

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат вывода
    handlers=[
        logging.StreamHandler(),  # Вывод логов в консоль
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")  # Запись логов в файл
    ]
)

# Создаём логгер
logger = logging.getLogger(__name__)

def selenium_oms(username, password, start_date, end_date, start_date_treatment):
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
        # Настройка опций для Firefox
        options = Options()
        options.headless = True
        options.set_preference('gfx.webrender.all', False)
        options.set_preference('gfx.webrender.enabled', False)
        options.set_preference('layers.acceleration.disabled', True)
        options.set_preference('webgl.disabled', True)

        # Автоматическая установка geckodriver с помощью webdriver-manager
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.implicitly_wait(10)
        driver.get('http://10.36.0.142:9000/')
        logger.info("Открыт сайт OMS")
        logger.info(
            f"ПАРАМЕТРЫ:\n"
            f"период изменения - начало: {start_date}\n"
            f"период изменения - окончание: {end_date}\n"
            f"период окончания лечения начло: {start_date_treatment}")

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

        # Обработка скачанного файла
        download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        file_pattern = 'journal_*.csv'
        logger.info(f"Ищем файлы в {download_folder} с шаблоном {file_pattern}")
        files = glob.glob(os.path.join(download_folder, file_pattern))

        if files:
            latest_file = max(files, key=os.path.getctime)
            logger.info(f"Последний файл: {latest_file}")
            destination_folder = os.path.join(settings.BASE_DIR, 'imported_files')
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            new_file_path = os.path.join(destination_folder, 'downloaded_file.csv')
            shutil.move(latest_file, new_file_path)
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
