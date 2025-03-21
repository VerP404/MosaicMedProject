# common/universal_load.py
import json
import os

import psycopg2
from dagster import OpExecutionContext

from config.settings import ORGANIZATIONS
from mosaic_conductor.etl.common.connect_db import connect_to_db


def load_dataframe(context: OpExecutionContext, table_name: str, data, db_alias: str, mapping_file: str,
                   sql_generator) -> dict:
    """
    Универсальная функция для загрузки DataFrame в таблицу БД.
    Использует уже настроенное подключение через connect_to_db.

    :param context: Dagster execution context.
    :param table_name: Имя таблицы в БД.
    :param data: Pandas DataFrame с данными для загрузки.
    :param db_alias: Ключ подключения (например, 'default').
    :param sql_generator: Функция, генерирующая SQL-запросы и параметры.
    :return: Словарь с итоговым числом строк, статусом и именем таблицы.
    """
    # Загружаем настройки маппинга
    if not os.path.exists(mapping_file):
        context.log.error(f"Mapping file {mapping_file} not found.")
        raise FileNotFoundError(f"Mapping file {mapping_file} not found.")

    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    table_config = mappings.get("tables", {}).get(table_name, {})
    conflict_columns = table_config.get("column_check", [])
    if not conflict_columns:
        context.log.error(f"Conflict columns (column_check) not specified for table {table_name}.")
        raise ValueError(f"Conflict columns not specified for table {table_name}.")
    conflict_columns_str = ", ".join(conflict_columns)

    # Определяем, использовать ли столбцы created_at и updated_at
    use_timestamps = table_config.get("use_timestamps", True)

    # Если timestamps используются, удаляем их из DataFrame (чтобы они не попали в список исходных столбцов)
    if use_timestamps:
        data = data.drop(columns=[col for col in data.columns if col.lower() in ("created_at", "updated_at")],
                         errors='ignore')

    # Формируем список столбцов для вставки
    cols = list(data.columns)
    if use_timestamps:
        insert_columns = cols + ["created_at", "updated_at"]
    else:
        insert_columns = cols

    # Генерируем SQL-запросы с использованием conflict_columns из маппинга
    def sql_generator_fn(data, table_name):
        for _, row in data.iterrows():
            if use_timestamps:
                placeholders = ", ".join(["%s"] * len(cols)) + ", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP"
            else:
                placeholders = ", ".join(["%s"] * len(cols))
            sql = f"""
                INSERT INTO {table_name} ({', '.join(insert_columns)})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_columns_str})
                DO UPDATE SET {', '.join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_columns])};
                """
            yield sql, tuple(row[col] for col in cols)

    # Получаем подключение к базе (используется уже настроенная функция)
    engine, conn = connect_to_db(db_alias=db_alias, organization=ORGANIZATIONS, context=context)
    cursor = conn.cursor()

    # Заполняем отсутствующие значения
    data.fillna("-", inplace=True)

    # Выполняем SQL-запросы, сгенерированные sql_generator_fn
    for sql, params in sql_generator_fn(data, table_name):
        cursor.execute(sql, params)

    conn.commit()

    # Получаем итоговое число строк в таблице
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    final_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    context.log.info(f"📤 Данные загружены в {table_name}. Итоговое число строк: {final_count}")
    return {"table_name": table_name, "status": "success", "final_count": final_count}