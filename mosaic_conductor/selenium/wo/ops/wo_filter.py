from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from dagster import op, Field, String
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


@op(
    config_schema={
        "start_date_treatment": Field(String, is_required=False, default_value=""),
        "start_date": Field(String, is_required=False, default_value="")
    },
    required_resource_keys={"selenium_driver"}
)
def filter_input_op(context, site_url: str):
    driver = context.resources.selenium_driver
    wait = WebDriverWait(driver, 30)

    # Вычисляем дефолтные значения, если не заданы в конфиге
    start_date_treatment = context.op_config.get("start_date_treatment") or datetime(datetime.now().year, 1,
                                                                                     1).strftime("%d-%m-%y")
    start_date = context.op_config.get("start_date") or (datetime.now() - timedelta(days=1)).strftime("%d-%m-%y")

    context.log.info(f"Устанавливаем фильтр для даты начала лечения: {start_date_treatment}")
    context.log.info(f"Устанавливаем фильтр для даты изменений талонов: {start_date}")

    # Пример установки фильтра для даты начала лечения
    start_date_input_treatment = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="menu"]/div/div[1]/div/div[1]/div/div[2]/div[1]/div[1]/div/div/div/input')
        )
    )

    # Устанавливаем значение с проверкой через цикл
    def set_input_value(element, expected_value, field_name, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            element.clear()
            element.send_keys(expected_value)
            time.sleep(1)  # небольшая задержка для применения
            current_value = element.get_attribute("value")
            context.log.info(f"{field_name} attempt {attempts + 1}: {current_value}")
            if current_value == expected_value:
                return True
            attempts += 1
        return False

    if not set_input_value(start_date_input_treatment, start_date_treatment, "Дата начала лечения"):
        raise Exception("Не удалось установить фильтр для даты начала лечения.")

    # Открываем фильтр (пример, ваши XPATH могут отличаться)
    open_filter_step1 = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[1]/div[2]')
        )
    )
    open_filter_step1.click()
    open_filter_step2 = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH,
             '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[1]/div[2]')
        )
    )
    open_filter_step2.click()

    # Устанавливаем фильтр для даты изменений талонов
    start_date_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH,
             '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[3]/div[5]/div[2]/div[1]/div/div/div/input')
        )
    )
    if not set_input_value(start_date_input, start_date, "Дата изменений талонов"):
        raise Exception("Не удалось установить фильтр для даты изменений талонов.")

    context.log.info("Фильтры установлены корректно, нажимаем Enter для выполнения поиска.")

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

    find_button = driver.find_element(By.XPATH,
                                      '//*[@id="menu"]/div/div[1]/div/div[4]/div/div[4]/div/button')
    find_button.click()
    ojidanie()
    # Ожидание загрузки
    loading_indicator_locator = (By.XPATH,
                                 '//h2[contains(@class, "jss170") and contains(@class, "jss176") and text()="Пожалуйста, подождите..."]')
    wait.until(EC.invisibility_of_element_located(loading_indicator_locator))
    time.sleep(5)
    context.log.info("Выбираем все результаты")

    # Выбираем все результаты
    select_all_checkbox = driver.find_element(By.XPATH,
                                              '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span')
    select_all_checkbox.click()
    # Скачивание файла
    context.log.info("Начинаем скачивание файла")
    download_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[3]/div/div/div[4]/a/button')
    download_button.click()
    time.sleep(5)
    return "Данные выгруженны в csv."


@op(
    required_resource_keys={"selenium_driver"}
)
def filter_input_doctor_op(context, site_url: str):
    time.sleep(5)
    driver = context.resources.selenium_driver
    page_doctor = f"{site_url.rstrip('/')}/registry/doctors"
    driver.get(page_doctor)
    context.log.info(f'Открыта страница: {page_doctor}')
    wait = WebDriverWait(driver, 10)
    # Дожидаемся появления кнопки поиска
    search_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[3]/div/div[2]/div/button'))
    )
    search_button.click()

    try:
        select_all_checkbox = driver.find_element(By.XPATH,
                                                  '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]/thead/tr[1]/th[1]/span/span[1]/input')
        select_all_checkbox.click()
    except:
        time.sleep(5)
        select_all_checkbox = driver.find_element(By.XPATH,
                                                  '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]/thead/tr[1]/th[1]/span/span[1]/input')
        select_all_checkbox.click()
    download_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div[2]/div[2]/a/button'))
    )
    download_button.click()
    return "Данные выгруженны в csv."


@op(
    config_schema={
        "start_date_treatment": Field(String, is_required=False, default_value=""),
        "start_date": Field(String, is_required=False, default_value="")
    },
    required_resource_keys={"selenium_driver"}
)
def filter_input_detail_op(context, site_url: str):
    time.sleep(5)
    driver = context.resources.selenium_driver
    wait = WebDriverWait(driver, 30)
    page_doctor = f"{site_url.rstrip('/')}/registry/detailedMedicalExamination"
    driver.get(page_doctor)
    context.log.info(f'Открыта страница: {page_doctor}')
    # Вычисляем дефолтные значения, если не заданы в конфиге
    start_date_treatment = context.op_config.get("start_date_treatment") or datetime(datetime.now().year, 1,
                                                                                     1).strftime("%d-%m-%y")
    start_date = context.op_config.get("start_date") or (datetime.now() - timedelta(days=1)).strftime("%d-%m-%y")

    context.log.info(f"Устанавливаем фильтр для даты начала лечения: {start_date_treatment}")
    context.log.info(f"Устанавливаем фильтр для даты изменений талонов: {start_date}")

    # Пример установки фильтра для даты начала лечения
    start_date_input_treatment = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="menu"]/div/div[2]/div/div[2]/div[1]/div/div/div/input')
        )
    )

    # Устанавливаем значение с проверкой через цикл
    def set_input_value(element, expected_value, field_name, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            element.clear()
            element.send_keys(expected_value)
            time.sleep(1)  # небольшая задержка для применения
            current_value = element.get_attribute("value")
            context.log.info(f"{field_name} attempt {attempts + 1}: {current_value}")
            if current_value == expected_value:
                return True
            attempts += 1
        return False

    if not set_input_value(start_date_input_treatment, start_date_treatment, "Дата начала лечения"):
        raise Exception("Не удалось установить фильтр для даты начала лечения.")

    # Открываем фильтр (пример, ваши XPATH могут отличаться)
    open_filter_step1 = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="menu"]/div/div[6]/div/div/div[1]/div[2]')
        )
    )
    open_filter_step1.click()
    open_filter_step2 = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH,
             '//*[@id="menu"]/div/div[6]/div/div/div[2]/div/div/div/div/div[2]/div/div[1]/div[2]')
        )
    )
    open_filter_step2.click()

    # Устанавливаем фильтр для даты изменений талонов
    start_date_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH,
             '//*[@id="menu"]/div/div[6]/div/div/div[2]/div/div/div/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/input')
        )
    )
    if not set_input_value(start_date_input, start_date, "Дата изменений талонов"):
        raise Exception("Не удалось установить фильтр для даты изменений талонов.")

    context.log.info("Фильтры установлены корректно, нажимаем Enter для выполнения поиска.")

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

    find_button = driver.find_element(By.XPATH,
                                      '//*[@id="menu"]/div/div[5]/div/div/div[2]/button')
    find_button.click()
    ojidanie()
    # Ожидание загрузки
    loading_indicator_locator = (By.XPATH,
                                 '//h2[contains(@class, "jss170") and contains(@class, "jss176") and text()="Пожалуйста, подождите..."]')
    wait.until(EC.invisibility_of_element_located(loading_indicator_locator))
    time.sleep(5)
    
    # Дополнительное ожидание для загрузки таблицы с большим количеством записей
    context.log.info("Ожидаем полной загрузки таблицы...")
    try:
        # Ждем появления таблицы
        table_locator = (By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]')
        wait.until(EC.presence_of_element_located(table_locator))
        
        # Ждем появления чекбокса в заголовке таблицы
        checkbox_locator = (By.XPATH, '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]/thead/tr[1]/th[1]/span/span[1]/input')
        wait.until(EC.presence_of_element_located(checkbox_locator))
        
        # Дополнительная пауза для стабилизации
        time.sleep(3)
        context.log.info("Таблица загружена, переходим к выбору всех результатов")
    except Exception as e:
        context.log.warning(f"Не удалось дождаться полной загрузки таблицы: {e}")
    
    context.log.info("Выбираем все результаты")

    # Выбираем все результаты - используем рабочий XPath
    try:
        xpath = '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]/thead/tr[1]/th[1]/span/span[1]/input'
        select_all_checkbox = driver.find_element(By.XPATH, xpath)
        select_all_checkbox.click()
        context.log.info("Чекбокс найден и нажат")
    except Exception as e:
        context.log.error(f"Не удалось найти чекбокс: {e}")
        raise Exception("Элемент для выбора всех результатов не найден")
    # Скачивание файла
    context.log.info("Начинаем скачивание файла")
    
    # Поиск кнопки скачивания CSV
    download_button = None
    download_selectors = [
        '//*[@id="menu"]/div/div[4]/div/div[2]/div[2]/a/button',
        '//button[contains(text(), "csv")]',
        '//a[contains(text(), "csv")]',
        '//button[contains(text(), "CSV")]',
        '//a[contains(text(), "CSV")]',
        '//button[contains(text(), "Скачать")]',
        '//a[contains(text(), "Скачать")]'
    ]
    
    for selector in download_selectors:
        try:
            download_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            context.log.info(f"Найдена кнопка скачивания с селектором: {selector}")
            break
        except Exception as e:
            context.log.warning(f"Не удалось найти кнопку с селектором {selector}: {e}")
            continue
    
    if download_button is None:
        context.log.error("Не удалось найти кнопку скачивания")
        raise Exception("Кнопка скачивания не найдена")
    
    download_button.click()
    time.sleep(5)
    return "Данные выгруженны в csv."

@op(
    config_schema={
        "start_date_treatment": Field(String, is_required=False, default_value=""),
        "start_date": Field(String, is_required=False, default_value="")
    },
    required_resource_keys={"selenium_driver"}
)
def filter_input_error_op(context, site_url: str):
    time.sleep(5)
    driver = context.resources.selenium_driver
    wait = WebDriverWait(driver, 30)
    page_doctor = f"{site_url.rstrip('/')}/registry/error_log"
    driver.get(page_doctor)
    context.log.info(f'Открыта страница: {page_doctor}')
    # Вычисляем дефолтные значения, если не заданы в конфиге
    start_date_treatment = context.op_config.get("start_date_treatment") or datetime(datetime.now().year, 1,
                                                                                     1).strftime("%d-%m-%y")
    start_date = context.op_config.get("start_date_treatment") or datetime(datetime.now().year, 1,
                                                                                     1).strftime("%d-%m-%y")

    context.log.info(f"Устанавливаем фильтр для даты начала лечения: {start_date_treatment}")
    context.log.info(f"Устанавливаем фильтр для даты выставления счета: {start_date}")

    # Пример установки фильтра для даты начала лечения
    start_date_input_treatment = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="menu"]/div/div[2]/div/div[2]/div[1]/div/div/div/input')
        )
    )

    # Устанавливаем значение с проверкой через цикл
    def set_input_value(element, expected_value, field_name, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            element.clear()
            element.send_keys(expected_value)
            time.sleep(1)  # небольшая задержка для применения
            current_value = element.get_attribute("value")
            context.log.info(f"{field_name} attempt {attempts + 1}: {current_value}")
            if current_value == expected_value:
                return True
            attempts += 1
        return False

    if not set_input_value(start_date_input_treatment, start_date_treatment, "Дата начала лечения"):
        raise Exception("Не удалось установить фильтр для даты начала лечения.")


    # Устанавливаем фильтр для даты изменений талонов
    start_date_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH,
             '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[1]/div/div[2]/div[1]/div/div/div/input')
        )
    )
    if not set_input_value(start_date_input, start_date, "Дата изменений талонов"):
        raise Exception("Не удалось установить фильтр для периода выставления счета.")

    context.log.info("Фильтры установлены корректно, нажимаем Enter для выполнения поиска.")

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

    find_button = driver.find_element(By.XPATH,
                                      '//*[@id="menu"]/div/div[4]/div/div[3]/div/button')
    find_button.click()
    ojidanie()
    # Ожидание загрузки
    loading_indicator_locator = (By.XPATH,
                                 '//h2[contains(@class, "jss170") and contains(@class, "jss176") and text()="Пожалуйста, подождите..."]')
    wait.until(EC.invisibility_of_element_located(loading_indicator_locator))
    time.sleep(5)
    context.log.info("Выбираем все результаты")

    # Выбираем все результаты с обработкой ошибок
    try:
        # Пробуем найти чекбокс с ожиданием
        select_all_checkbox = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span/span[1]/input')
            )
        )
        select_all_checkbox.click()
        context.log.info("Чекбокс 'выбрать все' успешно найден и нажат")
    except Exception as e:
        context.log.warning(f"Не удалось найти основной чекбокс: {e}")
        # Пробуем альтернативные селекторы
        alternative_selectors = [
            '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span/span[1]/input',
            '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]/thead/tr[1]/th[1]/span/input',
            '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span/span[1]/input',
            '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]/thead/tr[1]/th[1]/input',
            '//table//thead//tr//th[1]//input[@type="checkbox"]',
            '//input[@type="checkbox" and contains(@class, "select-all")]',
            '//span[contains(@class, "checkbox")]//input'
        ]
        
        checkbox_found = False
        for selector in alternative_selectors:
            try:
                context.log.info(f"Пробуем альтернативный селектор: {selector}")
                select_all_checkbox = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                select_all_checkbox.click()
                context.log.info(f"Чекбокс найден с селектором: {selector}")
                checkbox_found = True
                break
            except Exception as alt_e:
                context.log.warning(f"Альтернативный селектор не сработал: {alt_e}")
                continue
        
        if not checkbox_found:
            context.log.error("Не удалось найти чекбокс 'выбрать все' ни одним из способов")
            # Проверяем, есть ли вообще таблица на странице
            try:
                table = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[1]/table[1]')
                context.log.info("Таблица найдена, но чекбокс отсутствует")
                # Продолжаем выполнение без выбора всех элементов
            except Exception as table_e:
                context.log.error(f"Таблица не найдена: {table_e}")
                raise Exception("Не удалось найти таблицу с данными для выбора")
    
    # Скачивание файла
    context.log.info("Начинаем скачивание файла")
    download_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[6]/div/div/div[4]/a/button')
    download_button.click()
    time.sleep(5)
    return "Данные выгруженны в csv."