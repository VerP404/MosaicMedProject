from dagster import op, RetryPolicy, RetryRequested
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from mosaic_conductor.selenium.config import ISZL_USERNAME, ISZL_PASSWORD


@op(
    required_resource_keys={"selenium_driver"},
    retry_policy=RetryPolicy(max_retries=3, delay=120)
)
def open_site_iszl_op(context) -> str:
    driver = context.resources.selenium_driver
    target_url = driver.target_url

    # Попытка открыть целевую страницу
    try:
        driver.get(target_url)
        context.log.info(f"Страница {target_url} успешно открыта.")
    except Exception as e:
        context.log.error(f"Ошибка при открытии страницы {target_url}: {e}")
        # Переинициализация драйвера перед повторной попыткой
        try:
            driver.quit()
        except Exception as quit_exc:
            context.log.error(f"Ошибка при закрытии драйвера: {quit_exc}")
        raise e  # При неудаче retry_policy повторит op

    # Попытка найти и заполнить поле ввода логина с ожиданием 10 секунд
    try:
        wait = WebDriverWait(driver, 10)  # явное ожидание 10 секунд только для логина
        login_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tbLogin"]'))
        )
        login_input.clear()
        login_input.send_keys(ISZL_USERNAME)
    except Exception as e:
        context.log.error(f"Поле ввода логина не появилось в течение 10 секунд: {e}")
        try:
            driver.quit()
        except Exception as quit_exc:
            context.log.error(f"Ошибка при закрытии драйвера: {quit_exc}")
        raise e

    # Попытка найти и заполнить поле ввода пароля (ждем стандартно, 30 сек)
    try:
        wait = WebDriverWait(driver, 30)
        password_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tbPwd"]'))
        )
        password_input.clear()
        password_input.send_keys(ISZL_PASSWORD)
        password_input.send_keys(Keys.ENTER)
        context.log.info("Авторизация выполнена")
    except Exception as e:
        context.log.error(f"Ошибка при авторизации: {e}")
        try:
            driver.quit()
        except Exception as quit_exc:
            context.log.error(f"Ошибка при закрытии драйвера: {quit_exc}")
        raise e

    return target_url