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
         Если в CSV присутствуют лишние поля – они игнорируются (выводится предупреждение).
         Если отсутствуют ожидаемые – выбрасывается ошибка с подробностями.
      3. Добавляет отсутствующие обязательные столбцы со значением "-" по умолчанию.
      4. Возвращает словарь с ключами "table_name" и "data".
    """
    # Получаем конфигурацию
    config = context.op_config
    mapping_file = config["mapping_file"]
    table_name = config["table_name"]

    # Извлекаем DataFrame из предыдущего этапа
    df = kvazar_extract.get("data")
    if df is None:
        context.log.info("⚠️ Нет данных для трансформации!")
        raise ValueError("❌ Нет данных для трансформации.")

    # Загружаем маппинг
    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)
    table_config = mappings.get("tables", {}).get(table_name, {})
    column_mapping = table_config.get("mapping_fields", {})

    # Ожидаемые столбцы до переименования (ключи маппинга)
    expected_original_cols = list(column_mapping.keys())
    # Фактические столбцы в CSV
    actual_cols = list(df.columns)

    problems = []
    missing_in_csv = set(expected_original_cols) - set(actual_cols)
    if missing_in_csv:
        problems.append(f"❌ Отсутствуют следующие столбцы в CSV: {missing_in_csv}")
    extra_in_csv = set(actual_cols) - set(expected_original_cols)
    if extra_in_csv:
        context.log.info(f"⚠️ Лишние столбцы в CSV обнаружены и будут проигнорированы: {extra_in_csv}")

    if problems:
        context.log.info(
            f"❗ Проблемы с исходными столбцами. Ожидалось: {expected_original_cols}, обнаружено: {actual_cols}. "
            f"Подробности: {'; '.join(problems)}"
        )
        raise KeyError(f"Несоответствие столбцов в CSV: {'; '.join(problems)}")

    # Ограничиваем DataFrame только столбцами, указанными в маппинге (лишние игнорируем)
    df = df[expected_original_cols]

    # Переименовываем столбцы согласно маппингу
    df = df.rename(columns=column_mapping)

    # Теперь ожидаемые столбцы после переименования
    expected_cols = list(column_mapping.values())
    actual_transformed_cols = list(df.columns)

    problems = []
    missing_after_rename = set(expected_cols) - set(actual_transformed_cols)
    if missing_after_rename:
        problems.append(f"❌ Отсутствуют после переименования: {missing_after_rename}")
    extra_after_rename = set(actual_transformed_cols) - set(expected_cols)
    if extra_after_rename:
        context.log.info(f"⚠️ Лишние столбцы после переименования обнаружены: {extra_after_rename}")

    if problems:
        context.log.info(
            f"❗ Проблемы с переименованными столбцами. Ожидалось: {expected_cols}, обнаружено: {actual_transformed_cols}. "
            f"Подробности: {'; '.join(problems)}"
        )
        raise KeyError(f"Несоответствие столбцов после переименования: {'; '.join(problems)}")

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
        context.log.info(f"❌ Не удалось получить список обязательных столбцов для таблицы {table_name}.")
        raise ValueError(f"❌ Нет обязательных столбцов для таблицы {table_name}.")

    use_timestamps = table_config.get("use_timestamps", True)
    context.log.info(f"ℹ️ Обязательные столбцы из БД (обновление дат: {use_timestamps}): {db_columns}")

    # Заполняем отсутствующие обязательные столбцы дефолтным значением "-"
    for col in db_columns:
        if col not in df.columns:
            context.log.info(f"⚠️ Добавляем отсутствующий столбец '{col}' со значением '-' по умолчанию.")
            df[col] = "-"

    context.log.info(f"✅ Трансформация для {table_name} завершена. Всего строк: {len(df)}")
    return {"table_name": table_name, "data": df}
