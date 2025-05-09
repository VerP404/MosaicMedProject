import datetime
import os
import json
import fnmatch
import pandas as pd
from dagster import OpExecutionContext


def universal_extract(
        context: OpExecutionContext,
        mapping_file: str,
        data_folder: str,
        table_name: str
) -> dict:
    """
    Универсальная функция для извлечения данных.

    Параметры:
      context: Dagster execution context
      mapping_file: Путь к файлу mapping.json с настройками таблиц
      data_folder: Путь к папке, в которой находятся файлы данных (CSV)
      table_name: Имя таблицы в mapping.json, для которой производится поиск файла

    Функция:
      1. Загружает настройки из mapping.json.
      2. Получает настройки для указанной таблицы (шаблон файла, формат, кодировку, разделитель).
      3. Ищет файлы в data_folder, удовлетворяющие шаблону.
      4. Выбирает последний (по сортировке) файл из найденных.
      5. Считывает CSV-файл с использованием заданных параметров.
      6. Возвращает словарь с ключами "table_name" и "data" (pandas DataFrame).
    """
    # Проверяем наличие файла маппинга
    if not os.path.exists(mapping_file):
        context.log.info(f"❌ Файл маппинга {mapping_file} не найден.")
        raise FileNotFoundError(f"❌ Файл маппинга {mapping_file} не найден.")

    # Загружаем настройки маппинга
    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    table_config = mappings.get("tables", {}).get(table_name)
    if not table_config:
        context.log.info(f"❌ Настройки для таблицы '{table_name}' не найдены в {mapping_file}.")
        raise ValueError(f"❌ Настройки для таблицы '{table_name}' не найдены.")

    file_pattern = table_config.get("file", {}).get("file_pattern", "")
    file_format = table_config.get("file", {}).get("file_format", "")

    # Проверяем наличие папки с данными
    if not os.path.exists(data_folder):
        context.log.info(f"❌ Папка {data_folder} не найдена.")
        raise FileNotFoundError(f"❌ Папка {data_folder} не найдена.")

    data_files = os.listdir(data_folder)
    if not data_files:
        context.log.info(f"❌ Нет файлов в папке {data_folder}.")
        raise FileNotFoundError(f"❌ Нет файлов в папке {data_folder}.")

    # Ищем файлы, удовлетворяющие шаблону: file_pattern.file_format
    matching_files = [
        f for f in data_files if fnmatch.fnmatch(f, f"{file_pattern}.{file_format}")
    ]
    if not matching_files:
        context.log.info(f"❌ Не найдено файлов по шаблону {file_pattern}.{file_format} в {data_folder}.")
        raise ValueError(f"❌ Не найдено файлов по шаблону {file_pattern}.{file_format} в {data_folder}.")

    # Выбираем последний файл из отсортированного списка
    matched_file = sorted(matching_files)[-1]
    file_path = os.path.join(data_folder, matched_file)

    # Читаем CSV с использованием параметров из маппинга
    encoding = table_config.get("encoding", "utf-81")
    delimiter = table_config.get("delimiter", ",")
    context.log.info(f"🔎 Используем кодировку: {encoding}")
    context.log.info(f"🔎 Используем разделитель: {delimiter}")
    try:
        # df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, dtype=str)
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            delimiter=delimiter,
            dtype=str,
            on_bad_lines='skip'
        )
    except pd.errors.ParserError as e:
        # Если CSV битый — переносим в папку ошибок
        context.log.error(f"Файл {file_path} битый (ParserError): {e}")

        # Формируем название с датой/временем
        now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        error_file_name = f"{now_str}_{matched_file}"

        # Создаём папку "error_files" (или "error") внутри data_folder
        error_folder = os.path.join(data_folder, "error_files")
        if not os.path.exists(error_folder):
            os.makedirs(error_folder)

        error_file_path = os.path.join(error_folder, error_file_name)
        os.rename(file_path, error_file_path)

        context.log.info(f"Файл перемещён в {error_file_path}")
        # Останавливаем шаг (если хотим зафейлить)
        raise

    text_value = f"📥 Загружено {len(df)} строк из {matched_file}"
    context.log.info(text_value)

    return {"table_name": table_name, "data": df}
