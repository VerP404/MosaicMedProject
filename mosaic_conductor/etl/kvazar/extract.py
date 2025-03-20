from dagster import asset, Field, String, OpExecutionContext, AssetIn

from mosaic_conductor.etl.common.universal_extract import universal_extract


@asset(
    config_schema={
        "mapping_file": Field(String),
        "data_folder": Field(String),
        "table_name": Field(String),
    },
    ins={"kvazar_db_check": AssetIn()}
)
def kvazar_extract(context: OpExecutionContext, kvazar_db_check: dict) -> dict:
    """
    Извлекает CSV-файл для таблицы.
    Перед выполнением происходит проверка БД (результат передаётся через db_check).
    Все параметры можно переопределить через интерфейс Dagster.
    """

    config = context.op_config
    mapping_file = config["mapping_file"]
    data_folder = config["data_folder"]
    table_name = config["table_name"]

    result = universal_extract(context, mapping_file, data_folder, table_name)
    return result
