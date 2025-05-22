from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from dagster import op, Field, String
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from mosaic_conductor.selenium.screen import save_screenshot


@op(
    config_schema={
        "start_date": Field(String, is_required=False, default_value=""),
        "end_date": Field(String, is_required=False, default_value="")
    },
    required_resource_keys={"selenium_driver"}
)
def iszl_filter_input_dispanser_op(context, site_url: str):
    """
    Операция для фильтрации и скачивания данных в разделе диспансерного наблюдения
    """
    driver = context.resources.selenium_driver
    wait = WebDriverWait(driver, 30)

    # Вычисляем дефолтные значения, если не заданы в конфиге
    # По умолчанию, дата начала - первый день текущего месяца
    start_date = context.op_config.get("start_date") or (datetime.now().replace(day=1)).strftime("%d.%m.%Y")
    # По умолчанию, дата окончания - текущая дата
    end_date = context.op_config.get("end_date") or datetime.now().strftime("%d.%m.%Y")

    context.log.info(f"Устанавливаем фильтр для даты начала: {start_date}")
    context.log.info(f"Устанавливаем фильтр для даты окончания: {end_date}")

    try:
        # Переход на страницу диспансерного наблюдения
        dispanser_url = f"{site_url.rstrip('/')}/Dispanser"
        driver.get(dispanser_url)
        context.log.info(f"Открыта страница диспансерного наблюдения: {dispanser_url}")
        time.sleep(5)  # Даем время для загрузки страницы
        
        # Сохраняем скриншот для анализа структуры страницы
        save_screenshot(driver, prefix="dispanser_page", context=context)
        
        # Функция для установки значения в поля ввода с проверкой
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

        # Открываем фильтры (пример, XPath нужно будет скорректировать для реальной страницы)
        # Тут используются примерные XPath, которые нужно будет заменить на реальные
        filter_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Фильтры')]"))
        )
        filter_button.click()
        context.log.info("Нажата кнопка Фильтры")

        # Устанавливаем дату начала
        start_date_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='dateFrom']"))
        )
        if not set_input_value(start_date_input, start_date, "Дата начала"):
            raise Exception("Не удалось установить фильтр для даты начала.")

        # Устанавливаем дату окончания
        end_date_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='dateTo']"))
        )
        if not set_input_value(end_date_input, end_date, "Дата окончания"):
            raise Exception("Не удалось установить фильтр для даты окончания.")

        # Нажатие на кнопку применения фильтров
        apply_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Применить')]"))
        )
        apply_button.click()
        context.log.info("Фильтры применены")

        # Ожидание загрузки результатов
        time.sleep(5)
        
        # Функция для проверки загрузки данных
        def check_loading():
            try:
                # Проверяем наличие индикатора загрузки и ожидаем его исчезновения
                loading_indicator = driver.find_element(By.XPATH, "//div[contains(@class, 'loading')]")
                context.log.info("Ожидание загрузки данных...")
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'loading')]")))
                return True
            except:
                # Если индикатор не найден, считаем что данные уже загружены
                return True

        # Ожидаем загрузку данных
        check_loading()

        # Нажатие на кнопку экспорта/скачивания
        download_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Экспорт') or contains(text(), 'Скачать')]"))
        )
        download_button.click()
        context.log.info("Запущена операция скачивания")
        
        # Ожидание скачивания файла
        time.sleep(10)
        
        return "Данные диспансерного наблюдения выгружены в CSV."
    
    except Exception as e:
        context.log.error(f"Ошибка при работе с диспансерным наблюдением: {e}")
        # Сохраняем скриншот ошибки
        save_screenshot(driver, prefix="dispanser_error", context=context)
        raise


@op(
    required_resource_keys={"selenium_driver"}
)
def iszl_filter_input_download_op(context, site_url: str):
    """
    Операция для скачивания CSV-файла из раздела выгрузки отчетов
    """
    driver = context.resources.selenium_driver
    wait = WebDriverWait(driver, 30)
    
    try:
        # Переход на страницу выгрузки отчетов
        reports_url = f"{site_url.rstrip('/')}/Reports"
        driver.get(reports_url)
        context.log.info(f"Открыта страница выгрузки отчетов: {reports_url}")
        time.sleep(5)  # Даем время для загрузки страницы
        
        # Сохраняем скриншот для анализа структуры страницы
        save_screenshot(driver, prefix="reports_page", context=context)
        
        # Выбор отчета для скачивания (пример, XPath нужно будет скорректировать)
        report_selector = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//select[@id='reportType']"))
        )
        report_selector.click()
        
        # Выбираем нужный тип отчета
        report_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//option[contains(text(), 'CSV-отчет')]"))
        )
        report_option.click()
        context.log.info("Выбран тип отчета: CSV")
        
        # Нажатие на кнопку формирования/скачивания отчета
        download_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Сформировать') or contains(text(), 'Скачать')]"))
        )
        download_button.click()
        context.log.info("Запущена операция скачивания отчета")
        
        # Ожидание скачивания файла
        time.sleep(10)
        
        return "Отчет в формате CSV успешно скачан."
    
    except Exception as e:
        context.log.error(f"Ошибка при скачивании отчета: {e}")
        # Сохраняем скриншот ошибки
        save_screenshot(driver, prefix="report_download_error", context=context)
        raise 