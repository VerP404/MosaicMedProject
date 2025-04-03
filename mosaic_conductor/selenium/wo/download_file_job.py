from dagster import op, job, Field, String
from mosaic_conductor.selenium.wo.oms import selenium_oms



@op(
    config_schema={
        "username": Field(String, description="Логин для OMS"),
        "password": Field(String, description="Пароль для OMS"),
        "start_date": Field(String, description="Начало периода изменения талонов (например, 2023-01-01)"),
        "end_date": Field(String, description="Конец периода изменения талонов (например, 2023-01-31)"),
        "start_date_treatment": Field(String, description="Дата начала лечения (например, 2023-01-05)"),
        "browser": Field(String, default_value="firefox", description="Браузер для работы: 'firefox' или 'chrome'"),
    }
)
def download_file_op(context):
    config = context.op_config
    username = config["username"]
    password = config["password"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    start_date_treatment = config["start_date_treatment"]
    browser = config["browser"]

    context.log.info("Запуск процесса скачивания файла через Selenium")
    success, file_path = selenium_oms(context, username, password, start_date, end_date, start_date_treatment, browser)
    if success:
        context.log.info(f"Файл успешно скачан: {file_path}")
    else:
        context.log.error("Скачивание файла завершилось ошибкой")
    return file_path


@job
def download_file_job():
    download_file_op()
