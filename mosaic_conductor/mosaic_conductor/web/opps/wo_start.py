from dagster import op

@op(required_resource_keys={"selenium_driver"})
def open_site_op(context) -> str:
    driver = context.resources.selenium_driver
    current_url = driver.current_url
    context.log.info(f"Сайт открыт: {current_url}")
    # Возвращаем текущий URL, чтобы передать его следующему op
    return current_url
