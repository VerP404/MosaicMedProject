from dagster import op
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mosaic_conductor.selenium.wo.config import OMS_USERNAME, OMS_PASSWORD


@op(required_resource_keys={"selenium_driver"})
def open_site_op(context) -> str:
    driver = context.resources.selenium_driver
    target_url = context.resources.selenium_driver.config["target_url"]

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

    password_input = wait.until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/form/input[2]'))
    )
    password_input.clear()
    password_input.send_keys(OMS_PASSWORD)
    password_input.send_keys(Keys.ENTER)
    context.log.info("Авторизация выполнена")
    return target_url
