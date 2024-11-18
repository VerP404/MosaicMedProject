import logging
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.firefox import GeckoDriverManager
import time
import os
import glob
from django.conf import settings

# Установка уровня логирования для selenium и urllib3
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Логи уровня INFO и выше будут выводиться


def selenium_iszl_people(username, password):
    def input_enter_xpath(xpath, text):
        element = driver.find_element(By.XPATH, xpath)
        element.send_keys(text, Keys.ENTER)

    def click_xpath(xpath):
        element = driver.find_element(By.XPATH, xpath)
        element.click()

    logger.info("Начало выполнения скрипта Selenium")
    try:
        # Настройка опций для Firefox
        options = Options()
        options.headless = True
        options.set_preference('browser.download.folderList', 2)
        options.set_preference('browser.download.manager.showWhenStarting', False)
        options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')
        download_folder = os.path.join(settings.BASE_DIR, 'imported_files')
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        options.set_preference('browser.download.dir', download_folder)

        # Автоматическая установка geckodriver с помощью webdriver-manager
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.implicitly_wait(10)
        driver.get('http://10.36.29.2:8087/')
        logger.info("Открыт ИСЗЛ")

        # Авторизация
        login_input = driver.find_element(By.XPATH, '//*[@id="tbLogin"]')
        login_input.clear()
        login_input.send_keys(username)
        try:
            input_enter_xpath('//*[@id="tbPwd"]', password)
        except:
            input_enter_xpath('//*[@id="tbPwd"]', password)

        time.sleep(2)
        # Открываем меню и выбираем нужный пункт
        clickable = driver.find_element(By.XPATH, '//*[@id="mnuAtt"]/ul/li[1]')
        ActionChains(driver).click_and_hold(clickable).perform()
        menu_item = driver.find_element(By.XPATH, '//*[@id="mnuAtt:submenu:2"]/li[3]/a')
        menu_item.click()
        menu_item.click()
        time.sleep(2)

        # Переход во внутренний фрейм
        frame = driver.find_element(By.XPATH, '//*[@id="ifMain"]')
        driver.switch_to.frame(frame)

        # Открываем форму выгрузки данных
        click_xpath('//*[@id="lbtnExternalData"]')
        time.sleep(2)

        # Переходим во фрейм модального окна
        modal_frame = driver.find_element(By.XPATH, '//*[@id="ifDic"]')
        driver.switch_to.frame(modal_frame)

        logger.info("Экспорт данных")
        time.sleep(2)

        # Нажимаем Экспорт данных
        click_xpath('//*[@id="lbtnExport"]')
        time.sleep(60)

        logger.info("Скачиваем файл")
        # Нажимаем Получить файл
        click_xpath('//*[@id="lbtnFile"]')
        time.sleep(60)

        # Проверка завершения загрузки файла
        file_pattern = os.path.join(download_folder, 'Att_MO_*.csv')
        timeout = 120  # Время ожидания завершения загрузки в секундах
        end_time = time.time() + timeout

        while time.time() < end_time:
            files = glob.glob(file_pattern)
            # Проверяем, если файл загружен и нет временного файла (.part)
            if files and not any(f.endswith('.crdownload') for f in files):
                latest_file = max(files, key=os.path.getctime)
                new_file_path = os.path.join(download_folder, 'downloaded_Att_MO.csv')
                os.rename(latest_file, new_file_path)
                logger.info(f"Файл успешно загружен и перемещен в {new_file_path}")
                driver.quit()
                return True, new_file_path
            time.sleep(5)  # Проверяем каждые 5 секунд

        logger.error("Файл не был загружен в течение отведенного времени")
        driver.quit()
        return False, None

    except Exception as e:
        logger.error(f"Ошибка при выполнении скрипта Selenium: {e}")
        return False, None
