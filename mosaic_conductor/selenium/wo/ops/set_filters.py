from dagster import op, Field, String
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup


@op(
    config_schema={
        "start_date": Field(String, description="Дата изменения талонов"),
        "end_date": Field(String, description="Конечная дата изменения талонов"),
        "start_date_treatment": Field(String, description="Дата начала лечения")
    },
    required_resource_keys={"selenium_driver"}
)
def set_filters_op(context):
    driver = context.resources.selenium_driver

    context.log.info("Установка даты лечения")
    try:
        treatment_input = driver.find_element(By.XPATH,
                                              '//*[@id="menu"]/div/div[1]/div/div[1]/div/div[2]/div[1]/div[1]/div/div/div/input')
        treatment_input.clear()
        treatment_input.send_keys(context.op_config["start_date_treatment"])
    except Exception as e:
        context.log.error(f"Ошибка ввода даты лечения: {e}")
        raise e

    context.log.info("Открытие фильтра")
    try:
        open_filter1 = driver.find_element(By.XPATH,
                                           '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[1]/div[2]')
        open_filter1.click()
        open_filter2 = driver.find_element(By.XPATH,
                                           '/html/body/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[1]/div[2]')
        open_filter2.click()
    except Exception as e:
        context.log.error(f"Ошибка открытия фильтра: {e}")
        raise e

    context.log.info("Установка даты изменения талонов")
    try:
        start_date_input = driver.find_element(By.XPATH,
                                               '//*[@id="menu"]/div/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div[7]/div/div[2]/div[1]/div/div/div/input')
        start_date_input.clear()
        start_date_input.send_keys(context.op_config["start_date"])
    except Exception as e:
        context.log.error(f"Ошибка ввода даты изменения талонов: {e}")
        raise e

    time.sleep(1)

    context.log.info("Нажатие кнопки 'Найти'")
    try:
        find_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[1]/div/div[4]/div/div[4]/div/button')
        find_button.click()
    except Exception as e:
        context.log.error(f"Ошибка при нажатии кнопки 'Найти': {e}")
        raise e

    # Пример ожидания обработки (заглушка)
    def wait_for_processing():
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

    wait_for_processing()
    time.sleep(5)
    return True
