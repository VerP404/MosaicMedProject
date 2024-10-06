from sqlalchemy import create_engine, text

from config.settings import DATABASES

postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}')


def execute_query(sql_query):
    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        return result.fetchall()


def text_sql_query(query_id):
    # Формируем SQL-запрос для получения текста запроса по ID
    query = execute_query(f"SELECT query FROM sql_manager_sqlquery WHERE id = {query_id}")

    # Очищаем запрос от лишних символов форматирования
    if query:
        sql_query = query[0][0].replace('\r\n', ' ').replace('\n', ' ').strip()
        return sql_query
    else:
        raise ValueError("Запрос с указанным ID не найден")


def get_active_targets():
    query = """
    SELECT general_target.code
    FROM oms_reference_generalomstarget general_target
    JOIN oms_reference_medicalorganizationomstarget org_target
    ON general_target.id = org_target.general_target_id
    WHERE org_target.is_active = TRUE
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return [row[0] for row in result.fetchall()]
