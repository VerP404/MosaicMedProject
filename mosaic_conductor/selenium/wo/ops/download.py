from dagster import op, Field, String
from selenium.webdriver.common.by import By
import time
import glob
import os


@op(
    config_schema={
        "file_pattern": Field(String, default_value="journal_*.csv", description="Шаблон имени файла"),
        "destination_folder": Field(String, is_required=False, description="Папка для поиска файла")
    },
    required_resource_keys={"selenium_driver"}
)
def download_file_op(context):
    driver = context.resources.selenium_driver
    context.log.info("Выбор всех результатов")
    try:
        select_all = driver.find_element(By.XPATH,
                                         '//*[@id="root"]/div/div[2]/div[2]/div[2]/div/div[2]/table[1]/thead/tr[1]/th[1]/span')
        select_all.click()
    except Exception as e:
        context.log.error(f"Ошибка выбора результатов: {e}")
        raise e

    context.log.info("Нажатие кнопки скачивания файла")
    try:
        download_button = driver.find_element(By.XPATH, '//*[@id="menu"]/div/div[3]/div/div/div[5]/a/button')
        download_button.click()
    except Exception as e:
        context.log.error(f"Ошибка нажатия кнопки скачивания: {e}")
        raise e

    time.sleep(5)

    browser = driver.capabilities.get("browserName", "firefox")
    if browser.lower() == "chrome":
        file_folder = context.op_config.get("destination_folder")
        if not file_folder:
            file_folder = os.getcwd()
    else:
        file_folder = os.path.expanduser('~/Downloads')

    file_pattern = context.op_config.get("file_pattern", "journal_*.csv")
    search_pattern = os.path.join(file_folder, file_pattern)
    files = glob.glob(search_pattern)
    if not files:
        error_msg = f"Файл не найден в папке {file_folder}"
        context.log.error(error_msg)
        raise Exception(error_msg)

    latest_file = max(files, key=os.path.getctime)
    context.log.info(f"Найден файл: {latest_file}")
    return latest_file
