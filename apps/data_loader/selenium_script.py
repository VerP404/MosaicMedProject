# apps/data_loader/selenium_script.py
import logging

logger = logging.getLogger(__name__)


def run_selenium_script(username, password, start_date, end_date, start_date_treatment):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    import time
    import os
    import glob
    import shutil
    from django.conf import settings
    from .utils import process_csv_file

    logger.info("Начало выполнения скрипта Selenium")
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        driver.implicitly_wait(10)
        driver.get('http://10.36.0.142:9000/')
        logger.info("Открыт сайт OMS")

        # Авторизация
        login_input = driver.find_element(By.XPATH, '/html/body/div/form/input[1]')
        login_input.clear()
        login_input.send_keys(username)
        password_input = driver.find_element(By.XPATH, '/html/body/div/form/input[2]')
        password_input.clear()
        password_input.send_keys(password)
        password_input.send_keys(Keys.ENTER)
        logger.info("Авторизация выполнена")
        time.sleep(5)

        wait = WebDriverWait(driver, 120)  # Ждем до 60 секунд
        logger.info("Открытие меню")
        # Ввод даты начала лечения
        start_date_input_treatment = driver.find_element(By.XPATH,
                                                         '//*[@id="menu"]/div/div[1]/div/div[1]/div/div[2]/div[1]/div[1]/div/div/div/input')
        start_date_input_treatment.clear()
        start_date_input_treatment.send_keys(start_date_treatment)

        # Открытие расширенного фильтра
        open_filter_step1 = driver.find_element(By.XPATH,
                                                '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[1]/div[2]')
        open_filter_step1.click()
        # Открытие фильтра по талону
        open_filter_step2 = driver.find_element(By.XPATH,
                                                '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[1]/div[2]')
        open_filter_step2.click()

        # Даты изменения талонов: начало
        start_date_input = driver.find_element(By.XPATH,
                                               '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[7]/div/div[2]/div[1]/div/div/div/input')
        start_date_input.clear()
        start_date_input.send_keys(start_date)
        # Даты изменения талонов: окончание
        end_date_input = driver.find_element(By.XPATH,
                                             '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[7]/div/div[2]/div[2]/div/div/div/input')
        end_date_input.clear()
        end_date_input.send_keys(end_date)
        # Нажимаем "Найти"
        find_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[1]/div/div[4]/div/div[4]/div/button')
        find_button.click()

        # Ожидаем, пока элемент "Пожалуйста, подождите..." не исчезнет
        loading_indicator_locator = (By.XPATH,
                                     '//h2[contains(@class, "jss170") and contains(@class, "jss176") and text()="Пожалуйста, подождите..."]')
        wait.until(EC.invisibility_of_element_located(loading_indicator_locator))

        # Выбираем все результаты
        select_all_checkbox = driver.find_element(By.XPATH,
                                                  '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span')
        select_all_checkbox.click()

        time.sleep(5)

        # Скачиваем файл
        logger.info("Начинаем скачивание файла")

        download_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[3]/div/div/div[5]/a/button')
        download_button.click()

        # Обработка скачанного файла
        download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        file_pattern = 'journal_*.csv'
        files = glob.glob(os.path.join(download_folder, file_pattern))
        if files:
            latest_file = max(files, key=os.path.getctime)
            destination_folder = os.path.join(settings.BASE_DIR, 'imported_files')
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            new_file_path = os.path.join(destination_folder, 'downloaded_file.csv')
            shutil.move(latest_file, new_file_path)

            # Вызываем функцию обработки CSV-файла и получаем статистику
            added_count, updated_count, error_count = process_csv_file(new_file_path)

            driver.quit()
            logger.info("Завершение работы скрипта Selenium")
            return True, added_count, updated_count, error_count
        else:
            driver.quit()
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"Ошибка при выполнении скрипта Selenium: {e}")
        return False, 0, 0, 0
