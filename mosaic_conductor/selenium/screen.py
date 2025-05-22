import os
import time
from pathlib import Path


# Добавляем универсальную функцию для сохранения скриншотов
def save_screenshot(driver, prefix="error", context=None):
    """
    Универсальная функция для сохранения скриншотов при ошибках Selenium.

    Args:
        driver: Объект WebDriver Selenium
        prefix: Префикс для имени файла (например, "login_error", "auth_error")
        context: Контекст Dagster для логирования (опционально)

    Returns:
        str: Абсолютный путь к сохраненному скриншоту или None в случае ошибки
    """
    if not driver:
        if context:
            context.log.error("Невозможно сохранить скриншот: драйвер не инициализирован")
        return None

    try:
        # Создаем директорию для скриншотов
        screenshots_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "selenium", "screenshots"
        )
        Path(screenshots_dir).mkdir(exist_ok=True, parents=True)

        # Генерируем уникальное имя файла с временной меткой и информацией об URL
        timestamp = int(time.time())

        # Пытаемся получить текущий URL для более информативного имени файла
        try:
            current_url = driver.current_url
            # Извлекаем домен и путь, избегая специальных символов
            url_part = current_url.split("//")[-1].split("/")[0][:30]
            url_part = "".join(c if c.isalnum() else "_" for c in url_part)
        except:
            url_part = "unknown_page"

        filename = f"{prefix}_{url_part}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)

        # Сохраняем скриншот
        driver.save_screenshot(filepath)

        # Логируем информацию
        message = f"Скриншот сохранен: {filepath}"
        if context:
            context.log.info(message)

        return filepath

    except Exception as e:
        error_message = f"Ошибка при сохранении скриншота: {str(e)}"
        if context:
            context.log.error(error_message)
        return None
