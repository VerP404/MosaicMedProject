import os
import json
from dagster import asset, OpExecutionContext, Field, StringSource, AssetIn, String
from django.utils import timezone
from sqlalchemy import text

from apps.analytical_app.query_executor import engine
from mosaic_conductor.etl.common.universal_load import load_dataframe, save_load_log_pg


def clear_data_folder(data_folder):
    items = os.listdir(data_folder)
    for item in items:
        path = os.path.join(data_folder, item)
        if os.path.isdir(path):
            continue
        try:
            os.remove(path)
            print(f"Удалён файл: {path}")
        except Exception as e:
            print(f"Не удалось удалить {path}: {e}")

def kvazar_sql_generator(data, table_name, mapping_file):
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Mapping file {mapping_file} not found.")
    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)
    table_config = mappings.get("tables", {}).get(table_name, {})
    conflict_columns = table_config.get("column_check", [])
    if not conflict_columns:
        raise ValueError(f"Conflict columns (column_check) not specified for table {table_name}.")
    conflict_columns_str = ", ".join(conflict_columns)
    use_timestamps = table_config.get("use_timestamps", True)
    if use_timestamps:
        cols = [col for col in data.columns if col.lower() not in ("created_at", "updated_at")]
        insert_columns = cols + ["created_at", "updated_at"]
    else:
        cols = list(data.columns)
        insert_columns = cols
    update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_columns])
    for _, row in data.iterrows():
        if use_timestamps:
            placeholders = ", ".join(["%s"] * len(cols)) + ", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP"
        else:
            placeholders = ", ".join(["%s"] * len(cols))
        sql = f"""
        INSERT INTO {table_name} ({', '.join(insert_columns)})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_columns_str})
        DO UPDATE SET {update_clause};
        """
        yield sql, tuple(row[col] for col in cols)

@asset(
    config_schema={
        "table_name": Field(StringSource, is_required=True, description="Имя таблицы для загрузки"),
        "data_folder": Field(String, is_required=True, description="Путь к папке с CSV-файлами"),
        "mapping_file": Field(String, is_required=True, description="Путь к файлу mapping.json")
    },
    ins={"kvazar_transform": AssetIn()}
)
def kvazar_load(context: OpExecutionContext, kvazar_transform: dict):
    table_name = context.op_config["table_name"]
    data_folder = context.op_config["data_folder"]
    mapping_file = context.op_config["mapping_file"]
    enable_logging = context.op_config.get("enable_logging", True)

    # Замер времени начала загрузки
    start_time = timezone.now()
    result = None
    error_occurred = False
    error_code = None

    try:
        if "normal" in kvazar_transform and "complex" in kvazar_transform:
            normal_payload = kvazar_transform["normal"]
            complex_payload = kvazar_transform["complex"]
            context.log.info("ℹ️ Загружаются данные для нормальных и комплексных талонов")
            result_normal = load_dataframe(
                context,
                normal_payload["table_name"],
                normal_payload["data"],
                db_alias="default",
                mapping_file=mapping_file,
                sql_generator=lambda d, t: kvazar_sql_generator(d, t, mapping_file)
            )
            result_complex = load_dataframe(
                context,
                complex_payload["table_name"],
                complex_payload["data"],
                db_alias="default",
                mapping_file=mapping_file,
                sql_generator=lambda d, t: kvazar_sql_generator(d, t, mapping_file)
            )
            result = {"normal": result_normal, "complex": result_complex}
        else:
            data = kvazar_transform.get("data")
            if data is None or data.empty:
                context.log.info(f"ℹ️ Нет данных для загрузки в таблицу {table_name}.")
                result = {"table_name": table_name, "status": "skipped"}
            else:
                result = load_dataframe(
                    context,
                    table_name,
                    data,
                    db_alias="default",
                    mapping_file=mapping_file,
                    sql_generator=lambda d, t: kvazar_sql_generator(d, t, mapping_file)
                )
        clear_data_folder(data_folder)
        context.log.info(f"✅ Папка {data_folder} очищена")
    except Exception as exc:
        error_occurred = True
        error_code = str(exc)
        raise
    finally:
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        if result and not error_occurred:
            if "normal" in result and "complex" in result:
                count_after = result["normal"].get("final_count", 0) + result["complex"].get("final_count", 0)
            else:
                count_after = result.get("final_count", 0)
        else:
            count_after = 0
        count_before = 0  # При необходимости можно получить из БД до загрузки

        # Формируем run_url, используя run_id из context и базовый URL для Dagster.
        run_id = context.run_id if hasattr(context, "run_id") else "unknown"
        with engine.connect() as connection:
            query_result = connection.execute(text("SELECT dagster_ip, dagster_port FROM home_mainsettings LIMIT 1"))
            row = query_result.fetchone()
            # Преобразуем результат в dict, чтобы сделать его сериализуемым:
            if row:
                row = dict(row._mapping)
                dagster_base_url = f"http://{row['dagster_ip']}:{row['dagster_port']}"
            else:
                dagster_base_url = "http://127.0.0.1:3000"
        run_url = f"{dagster_base_url}/runs/{run_id}"

        log_data = {
            "table_name": table_name,
            "start_time": start_time,
            "end_time": end_time,
            "count_before": count_before,
            "count_after": count_after,
            "duration": duration,
            "error_occurred": error_occurred,
            "error_code": error_code,
            "run_url": run_url,
        }
        if enable_logging:
            try:
                save_load_log_pg(context, log_data)
                context.log.info("ℹ️ Лог загрузки сохранен в Postgres")
            except Exception as log_exc:
                context.log.error(f"Ошибка сохранения лога загрузки: {log_exc}")
    return result
