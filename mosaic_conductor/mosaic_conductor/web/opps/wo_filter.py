from dagster import op
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

@op(required_resource_keys={"selenium_driver"})
def search_text_op(context, site_url: str):
    driver = context.resources.selenium_driver
    context.log.info(f"Получен URL из предыдущего op: {site_url}")

    try:
        search_box = driver.find_element(By.NAME, "q")
    except Exception as e:
        context.log.info(f"Не удалось найти поисковую строку: {e}")
        raise e

    context.log.info("Поисковая строка найдена.")
    search_query = "что такое дагстер"
    search_box.clear()
    search_box.send_keys(search_query)
    context.log.info(f"Введён запрос: {search_query}")
    search_box.send_keys(Keys.RETURN)
    context.log.info("Нажата клавиша Enter для выполнения поиска.")

    return "Поисковый запрос выполнен успешно."
