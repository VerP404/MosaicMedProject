import time

from dagster import op
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mosaic_conductor.selenium.wo.config import OMS_USERNAME, OMS_PASSWORD


@op(required_resource_keys={"selenium_driver"})
def open_site_op(context) -> str:
    driver = context.resources.selenium_driver
    target_url = driver.target_url

    try:
        driver.get(target_url)
        context.log.info(f"Страница {target_url} успешно открыта.")
    except Exception as e:
        context.log.error(f"Ошибка при открытии страницы {target_url}: {e}")
        raise

    # Теперь можно работать с формой авторизации
    wait = WebDriverWait(driver, 30)
    login_input = wait.until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/form/input[1]'))
    )
    login_input.clear()
    login_input.send_keys(OMS_USERNAME)

    for attempt in range(3):
        try:
            password_input = wait.until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/input[2]'))
            )
            password_input.clear()
            password_input.send_keys(OMS_PASSWORD)
            break  # Если прошло успешно, выходим из цикла
        except StaleElementReferenceException:
            context.log.info(f"Попытка {attempt + 1}: элемент устарел, повторный поиск...")
            time.sleep(1)
    # Дополнительная проверка успешной авторизации.
    try:
        # Указываем XPath элемента, который появляется только после успешной авторизации.
        authenticated_element = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="navBar"]/header/div/div/div[2]/p'))
        )
        context.log.info("Авторизация успешна, элемент найден: " + authenticated_element.text)
    except Exception as e:
        context.log.info("Не удалось найти элемент, свидетельствующий об успешной авторизации: " + str(e))
        context.log.error("Не удалось найти элемент, свидетельствующий об успешной авторизации: " + str(e))
        raise
    return target_url
