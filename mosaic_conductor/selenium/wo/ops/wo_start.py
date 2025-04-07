from dagster import op
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from mosaic_conductor.selenium.wo.config import OMS_USERNAME, OMS_PASSWORD


@op(required_resource_keys={"selenium_driver"})
def open_site_op(context) -> str:
    driver = context.resources.selenium_driver
    current_url = driver.current_url
    context.log.info(f"Сайт открыт: {current_url}")

    username = OMS_USERNAME
    password = OMS_PASSWORD

    login_input = driver.find_element(By.XPATH, '/html/body/div/form/input[1]')
    login_input.clear()
    login_input.send_keys(username)
    password_input = driver.find_element(By.XPATH, '/html/body/div/form/input[2]')
    password_input.clear()
    password_input.send_keys(password)
    password_input.send_keys(Keys.ENTER)
    context.log.info(f"Авторизация выполнена")
    return current_url
