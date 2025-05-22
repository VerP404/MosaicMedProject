from dagster import op, RetryPolicy, RetryRequested
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from mosaic_conductor.selenium.screen import save_screenshot
from mosaic_conductor.selenium.wo.config import OMS_USERNAME, OMS_PASSWORD
import time


@op(
    required_resource_keys={"selenium_driver"},
    retry_policy=RetryPolicy(max_retries=3, delay=120)
)
def open_site_op(context) -> str:
    driver = None
    try:
        # Получение драйвера из ресурса
        driver = context.resources.selenium_driver
        target_url = driver.target_url

        # Увеличиваем таймаут для загрузки страницы
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)

        # Попытка открыть целевую страницу с повторными попытками
        max_retries = 3
        for retry in range(max_retries):
            try:
                context.log.info(f"Попытка {retry + 1} открыть страницу {target_url}")
                driver.get(target_url)
                # Даем время странице полностью загрузиться
                time.sleep(5)
                context.log.info(f"Страница {target_url} успешно открыта.")
                break
            except Exception as e:
                context.log.error(f"Ошибка при открытии страницы {target_url}: {e}")
                save_screenshot(driver, prefix="page_load_error", context=context)
                if retry < max_retries - 1:
                    context.log.info(f"Повторная попытка через 5 секунд...")
                    time.sleep(5)
                else:
                    raise RetryRequested(f"Не удалось открыть страницу после {max_retries} попыток")

        # Попытка найти и заполнить поле ввода логина с увеличенным ожиданием и проверками
        try:
            context.log.info("Ожидание появления формы авторизации...")
            # Увеличиваем таймаут до 30 секунд
            wait = WebDriverWait(driver, 30)
            # Сначала проверим, что форма логина вообще загрузилась
            form = wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div/form'))
            )
            context.log.info("Форма авторизации найдена")

            # Теперь ищем поле логина
            login_input = wait.until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/input[1]'))
            )
            # Даем элементу время стать полностью интерактивным
            time.sleep(2)
            context.log.info("Найдено поле для ввода логина")
            login_input.clear()
            login_input.send_keys(OMS_USERNAME)
            context.log.info(f"Логин '{OMS_USERNAME}' введен")
        except Exception as e:
            context.log.error(f"Поле ввода логина не появилось: {e}")
            # Сохраняем скриншот с помощью универсальной функции
            screenshot_path = save_screenshot(driver, prefix="login_error", context=context)
            raise RetryRequested(f"Не удалось найти форму авторизации. Скриншот: {screenshot_path}")

        # Попытка найти и заполнить поле ввода пароля
        try:
            context.log.info("Поиск поля для ввода пароля...")
            password_input = wait.until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/input[2]'))
            )
            # Даем элементу время стать полностью интерактивным
            time.sleep(2)
            context.log.info("Найдено поле для ввода пароля")
            password_input.clear()
            password_input.send_keys(OMS_PASSWORD)
            context.log.info("Пароль введен")

            # Даем время системе перед нажатием Enter
            time.sleep(2)
            context.log.info("Нажатие кнопки Enter...")
            password_input.send_keys(Keys.ENTER)

            # Ожидаем успешного входа (можно добавить проверку на элемент, который появляется после авторизации)
            time.sleep(5)
            context.log.info("Авторизация выполнена успешно")
        except Exception as e:
            context.log.error(f"Ошибка при авторизации: {e}")
            # Сохраняем скриншот с помощью универсальной функции
            screenshot_path = save_screenshot(driver, prefix="auth_error", context=context)
            raise RetryRequested(f"Ошибка при авторизации. Скриншот: {screenshot_path}")

        return target_url

    except Exception as e:
        context.log.error(f"Критическая ошибка в open_site_op: {e}")
        # Сохраняем скриншот критической ошибки
        if driver:
            screenshot_path = save_screenshot(driver, prefix="critical_error", context=context)
            context.log.info(f"Скриншот критической ошибки: {screenshot_path}")
        # НЕ закрываем драйвер здесь - это будет сделано в finally блоке ресурса
        raise RetryRequested(f"Критическая ошибка: {str(e)}")
