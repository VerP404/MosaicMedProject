from dagster import op, Field, String
from selenium.webdriver.common.by import By


@op(
    config_schema={
        "username": Field(String, description="Логин для сайта"),
        "password": Field(String, description="Пароль для сайта"),
        "target_url": Field(String, description="URL для авторизации")
    },
    required_resource_keys={"selenium_driver"}
)
def authenticate_op(context):
    driver = context.resources.selenium_driver
    target_url = context.op_config["target_url"]
    username = context.op_config["username"]
    password = context.op_config["password"]

    context.log.info("Переход на сайт для авторизации")
    driver.get(target_url)

    try:
        login_input = driver.find_element(By.XPATH, '/html/body/div/form/input[1]')
        login_input.clear()
        login_input.send_keys(username)
        password_input = driver.find_element(By.XPATH, '/html/body/div/form/input[2]')
        password_input.clear()
        password_input.send_keys(password)
        password_input.send_keys("\n")
        context.log.info("Авторизация выполнена")
    except Exception as e:
        context.log.error(f"Ошибка авторизации: {e}")
        raise e
    return True
