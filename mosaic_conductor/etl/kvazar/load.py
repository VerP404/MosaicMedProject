import json
from dagster import asset, Field, String, OpExecutionContext, AssetIn

from config.settings import ORGANIZATIONS
from mosaic_conductor.etl.common.connect_db import connect_to_db


@asset(
    config_schema={
        "mapping_file": Field(String),
        "table_name": Field(String)
    },
    ins={"kvazar_extract": AssetIn()}
)
def kvazar_transform(context: OpExecutionContext, kvazar_extract: dict) -> dict:
    """
    Универсальная трансформация данных:
      1. Загружает настройки маппинга из mapping.json и переименовывает столбцы.
      2. Сравнивает ожидаемые и фактические столбцы в CSV.
      3. Выводит в INFO список проблем:
         - Если отсутствуют ожидаемые столбцы – выбрасывает ошибку.
         - Если обнаружены лишние столбцы – выводит предупреждение и игнорирует их.
      4. Добавляет отсутствующие обязательные столбцы из БД со значением "-" по умолчанию.
      5. Возвращает словарь с ключами "table_name" и "data".
    """
    # Получаем конфигурацию
    config = context.op_config
    mapping_file = config["mapping_file"]
    table_name = config["table_name"]

    # Извлекаем DataFrame из предыдущего этапа
    df = kvazar_extract.get("data")
    if df is None:
        context.log.info("INFO: Нет данных для трансформации!")
        raise ValueError("Нет данных для трансформации.")

    # Загружаем маппинг из mapping.json
    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)
    table_config = mappings.get("tables", {}).get(table_name, {})
    column_mapping = table_config.get("mapping_fields", {})

    # Ожидаемые столбцы до переименования (ключи маппинга)
    expected_original_cols = list(column_mapping.keys())
    # Фактические столбцы в CSV
    actual_cols = list(df.columns)

    missing_in_csv = set(expected_original_cols) - set(actual_cols)
    extra_in_csv = set(actual_cols) - set(expected_original_cols)

    if missing_in_csv:
        context.log.info(
            f"INFO: Проблемы с исходными столбцами. Ожидалось: {expected_original_cols}, "
            f"обнаружено: {actual_cols}. Отсутствуют: {missing_in_csv}."
        )
        raise KeyError(f"Отсутствуют ожидаемые столбцы в CSV: {missing_in_csv}")

    if extra_in_csv:
        context.log.info(
            f"INFO: Лишние столбцы в CSV обнаружены: {extra_in_csv}. Они будут проигнорированы."
        )

    # Ограничиваем DataFrame только столбцами, указанными в маппинге (игнорируя лишние)
    df = df[expected_original_cols]

    # Переименовываем столбцы согласно маппингу
    df = df.rename(columns=column_mapping)

    # Теперь ожидаемые столбцы после переименования
    expected_cols = list(column_mapping.values())
    actual_transformed_cols = list(df.columns)
    missing_after_rename = set(expected_cols) - set(actual_transformed_cols)
    extra_after_rename = set(actual_transformed_cols) - set(expected_cols)

    if missing_after_rename:
        context.log.info(
            f"INFO: Проблемы с переименованными столбцами. Ожидалось: {expected_cols}, "
            f"обнаружено: {actual_transformed_cols}. Отсутствуют: {missing_after_rename}. "
            f"Лишние: {extra_after_rename}."
        )
        raise KeyError(f"Отсутствуют ожидаемые столбцы после переименования: {missing_after_rename}")

    # Ограничиваем DataFrame только ожидаемыми столбцами
    df = df[expected_cols]

    # Получаем обязательные столбцы (varchar) из схемы таблицы в базе данных
    engine, conn = connect_to_db(organization=ORGANIZATIONS, context=context)
    sql = f"""
      SELECT column_name 
      FROM information_schema.columns 
      WHERE table_name = '{table_name}' 
        AND data_type = 'character varying';
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        db_columns = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not db_columns:
        context.log.info(f"INFO: Не удалось получить список обязательных столбцов для таблицы {table_name}.")
        raise ValueError(f"Нет обязательных столбцов для таблицы {table_name}.")

    use_timestamps = table_config.get("use_timestamps", True)
    context.log.info(f"INFO: Обязательные столбцы из БД (обновление дат: {use_timestamps}): {db_columns}")

    # Заполняем отсутствующие обязательные столбцы дефолтным значением "-"
    for col in db_columns:
        if col not in df.columns:
            df[col] = "-"

    context.log.info(f"INFO: Трансформация для {table_name} завершена. Всего строк: {len(df)}")
    return {"table_name": table_name, "data": df}
