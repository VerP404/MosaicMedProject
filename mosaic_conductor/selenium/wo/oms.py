from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import glob
import shutil
from bs4 import BeautifulSoup
from django.conf import settings


def selenium_oms(context, username, password, start_date, end_date, start_date_treatment, browser='firefox'):
    """
    Функция запуска Selenium для скачивания файла.
    Параметр context (OpExecutionContext) используется для логирования в Dagster.
    Логика: для Chrome файл сразу сохраняется в целевую папку,
    а для Firefox — скачивается в стандартную папку, а потом переносится.
    """
    log = context.log
    try:
        # Определяем целевую папку для файла
        destination_folder = os.path.join(settings.BASE_DIR, 'mosaic_conductor', 'etl', 'data', 'weboms', 'talon')
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Инициализация браузера
        if browser == 'firefox':
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.firefox.service import Service

            options = Options()
            options.headless = True
            # Для Firefox не задаём папку загрузки, чтобы файл скачивался по умолчанию
            service = Service(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
        elif browser == 'chrome':
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

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
            options.add_argument('--proxy-server="direct://"')
            options.add_argument('--proxy-bypass-list=*')
            # Задаём папку загрузки для Chrome
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
        driver.get('http://10.36.0.142:9000/')
        log.info("Открыт сайт OMS")
        log.info(
            f"ПАРАМЕТРЫ: start_date={start_date}, end_date={end_date}, start_date_treatment={start_date_treatment}")

        # Авторизация
        try:
            login_input = driver.find_element(By.XPATH, '/html/body/div/form/input[1]')
            login_input.clear()
            login_input.send_keys(username)
            password_input = driver.find_element(By.XPATH, '/html/body/div/form/input[2]')
            password_input.clear()
            password_input.send_keys(password)
            password_input.send_keys(Keys.ENTER)
            log.info("Авторизация выполнена")
        except Exception as e:
            raise Exception(f"Ошибка авторизации: {type(e).__name__} {e}")

        time.sleep(30)
        wait = WebDriverWait(driver, 120)
        log.info("Открытие меню")

        # Ввод даты начала лечения
        try:
            start_date_input_treatment = driver.find_element(By.XPATH,
                                                             '//*[@id="menu"]/div/div[1]/div/div[1]/div/div[2]/div[1]/div[1]/div/div/div/input')
            start_date_input_treatment.clear()
            start_date_input_treatment.send_keys(start_date_treatment)
        except Exception as e:
            raise Exception(f"Ошибка ввода даты лечения: {type(e).__name__} {e}")

        log.info("Открытие фильтра")
        try:
            open_filter_step1 = driver.find_element(By.XPATH,
                                                    '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[1]/div[2]')
            open_filter_step1.click()
            open_filter_step2 = driver.find_element(By.XPATH,
                                                    '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[1]/div[2]')
            open_filter_step2.click()
        except Exception as e:
            raise Exception(f"Ошибка открытия фильтра: {type(e).__name__} {e}")

        log.info("Ввод даты изменения талонов")
        try:
            start_date_input = driver.find_element(By.XPATH,
                                                   '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[7]/div/div[2]/div[1]/div/div/div/input')
            start_date_input.clear()
            start_date_input.send_keys(start_date)
        except Exception as e:
            raise Exception(f"Ошибка ввода даты изменения талонов: {type(e).__name__} {e}")
        time.sleep(1)

        log.info("Нажатие кнопки 'Найти'")
        try:
            find_button = driver.find_element(By.XPATH,
                                              '//*[@id="menu"]/div/div[1]/div/div[4]/div/div[4]/div/button')
            find_button.click()
        except Exception as e:
            raise Exception(f"Ошибка при нажатии кнопки 'Найти': {type(e).__name__} {e}")

        # Функция ожидания исчезновения сообщения "Пожалуйста, подождите..."
        def ojidanie():
            elapsed = 0
            while elapsed < 30:
                try:
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    info_elem = soup.find('h2', {'class': 'jss170 jss176'})
                    if info_elem and info_elem.get_text() == 'Пожалуйста, подождите...':
                        time.sleep(2)
                        elapsed += 2
                    else:
                        break
                except Exception:
                    break

        ojidanie()
        time.sleep(5)
        try:
            loading_indicator_locator = (By.XPATH,
                                         '//h2[contains(@class, "jss170") and contains(@class, "jss176") and text()="Пожалуйста, подождите..."]')
            wait.until(EC.invisibility_of_element_located(loading_indicator_locator))
        except Exception as e:
            log.error(f"Ошибка ожидания загрузки: {type(e).__name__} {e}")
        time.sleep(5)

        log.info("Выбор всех результатов")
        try:
            select_all_checkbox = driver.find_element(By.XPATH,
                                                      '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span')
            select_all_checkbox.click()
        except Exception as e:
            raise Exception(f"Ошибка выбора результатов: {type(e).__name__} {e}")

        log.info("Нажатие кнопки скачивания файла")
        try:
            download_button = driver.find_element(By.XPATH,
                                                  '//*[@id="menu"]/div/div[3]/div/div/div[5]/a/button')
            download_button.click()
        except Exception as e:
            raise Exception(f"Ошибка нажатия кнопки скачивания: {type(e).__name__} {e}")
        time.sleep(5)

        # Определяем папку, где искать файл: для Chrome — destination_folder, для Firefox — стандартная папка загрузок
        if browser == 'chrome':
            file_folder = destination_folder
        else:
            file_folder = os.path.expanduser('~/Downloads')

        file_pattern = 'journal_*.csv'
        files = glob.glob(os.path.join(file_folder, file_pattern))
        if not files:
            raise Exception(f"Файл не найден в папке {file_folder}")

        latest_file = max(files, key=os.path.getctime)
        log.info(f"Найден файл: {latest_file}")

        # Если браузер Firefox — перемещаем файл в destination_folder
        if browser != 'chrome':
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            new_file_path = os.path.join(destination_folder, 'downloaded_file.csv')
            shutil.move(latest_file, new_file_path)
            log.info(f"Файл перемещен в: {new_file_path}")
        else:
            new_file_path = os.path.join(destination_folder, 'downloaded_file.csv')
            shutil.move(latest_file, new_file_path)
            log.info(f"Файл переименован в: {new_file_path}")

        driver.quit()
        return True, new_file_path

    except Exception as e:
        context.log.error(f"Ошибка при выполнении скрипта Selenium: {type(e).__name__} {e}")
        try:
            driver.quit()
        except Exception:
            pass
        return False, None
