# apps/data_loader/management/commands/download_oms_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.data_loader.models.oms_data import OMSSettings
from apps.data_loader.utils import process_csv_file
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import os
import glob
import shutil
import datetime
import time

from config import settings


class Command(BaseCommand):
    help = 'Downloads OMS data using Selenium and imports it into the database.'

    def handle(self, *args, **options):
        # Получаем последние настройки из базы данных
        try:
            oms_settings = OMSSettings.objects.latest('id')
        except OMSSettings.DoesNotExist:
            self.stdout.write(self.style.ERROR('No OMS settings found in the database. Please add settings via admin.'))
            return

        username = oms_settings.username
        password = oms_settings.password
        treatment_start_date = oms_settings.created_start.strftime('%d-%m-%y')
        treatment_end_date = oms_settings.created_end.strftime('%d-%m-%y')
        print(f'начало {treatment_start_date} окончание {treatment_end_date}')
        # Запускаем Selenium
        driver = self.start_browser()

        try:
            self.authorization_user(driver, username, password)
            time.sleep(5)
            self.main_app(driver, treatment_start_date, treatment_end_date)
            driver.quit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            driver.quit()
            return

        # Обрабатываем скачанный файл
        self.process_downloaded_file()
        self.stdout.write(self.style.SUCCESS('Data downloaded and processed successfully.'))

    def start_browser(self):
        options = Options()
        options.add_argument("--headless")  # Если хотите запускать без открытия браузера
        # Настройка пути к geckodriver
        geckodriver_path = os.path.join(settings.BASE_DIR, 'drivers', 'geckodriver')
        print(geckodriver_path)
        service = Service(geckodriver_path)

        driver = webdriver.Firefox(service=service, options=options)
        driver.implicitly_wait(120)
        driver.get('http://10.36.0.142:9000/')  # Замените на ваш URL
        return driver

    def authorization_user(self, driver, username, password):
        # Ввод логина и пароля
        login_input = driver.find_element(By.XPATH, '/html/body/div/form/input[1]')
        login_input.clear()
        login_input.send_keys(username)
        password_input = driver.find_element(By.XPATH, '/html/body/div/form/input[2]')
        password_input.clear()
        password_input.send_keys(password)
        password_input.send_keys(Keys.ENTER)

    def main_app(self, driver, start_date, end_date):
        # Изменяем период лечения на заданные даты
        try:
            date_input = driver.find_element(By.XPATH,
                                             '//*[@id="menu"]/div/div[1]/div/div[1]/div/div[2]/div[1]/div[1]/div/div/div/input')
            date_input.clear()
            date_input.send_keys(start_date)
        except NoSuchElementException:
            time.sleep(120)

        # Нажимаем "Найти"
        find_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[1]/div/div[4]/div/div[4]/div/button')
        find_button.click()
        self.wait(driver)

        # Выбираем все результаты
        select_all_checkbox = driver.find_element(By.XPATH,
                                                  '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span/span[1]/input')
        select_all_checkbox.click()
        time.sleep(15)

        # Скачиваем файл
        download_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[3]/div/div/div[5]/a/button')
        download_button.click()
        time.sleep(15)

    def wait(self, driver):
        flag = True
        while flag:
            try:
                source_data = driver.page_source
                # Здесь добавьте код для проверки, что страница загрузилась
                # Например, проверка наличия определенного элемента
                flag = False  # Если страница загрузилась, устанавливаем flag = False
            except Exception:
                time.sleep(1)

    def process_downloaded_file(self):
        # Определяем папку загрузок
        download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        file_pattern = "journal_*.csv"

        # Ожидаем появления файла
        latest_file = self.wait_for_file(download_folder, file_pattern)
        if not latest_file:
            self.stdout.write(self.style.ERROR('Downloaded file not found.'))
            return

        # Перемещаем и переименовываем файл
        destination_folder = os.path.join(os.path.dirname(__file__), '..', 'imported_files')
        destination_folder = os.path.abspath(destination_folder)
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        now = timezone.now()
        date_time = now.strftime("%Y-%m-%d_%H-%M")
        new_file_name = f'OMS_data_{date_time}.csv'
        new_file_path = os.path.join(destination_folder, new_file_name)
        shutil.move(latest_file, new_file_path)

        # Обрабатываем файл
        process_csv_file(new_file_path)

    def wait_for_file(self, folder_path, file_pattern, timeout=120):
        start_time = time.time()
        while True:
            file_list = glob.glob(os.path.join(folder_path, file_pattern))
            if file_list:
                # Сортируем файлы по дате изменения
                file_list.sort(key=os.path.getmtime, reverse=True)
                # Выбираем самый свежий файл
                latest_file = file_list[0]
                # Проверяем, что файл был создан недавно
                if os.path.getmtime(latest_file) > start_time:
                    return latest_file
            if time.time() - start_time > timeout:
                return None
            time.sleep(1)
