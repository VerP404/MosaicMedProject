from sqlalchemy import create_engine, text

from config.settings import DATABASES

postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}')


def execute_query(sql_query, params=None):
    with engine.connect() as connection:
        result = connection.execute(text(sql_query), params)
        if result.returns_rows:
            return result.fetchall()
        else:
            return result.rowcount



def text_sql_query(query_id):
    # Формируем SQL-запрос для получения текста запроса по ID
    query = execute_query(f"SELECT query FROM sql_manager_sqlquery WHERE id = {query_id}")

    # Очищаем запрос от лишних символов форматирования
    if query:
        sql_query = query[0][0].replace('\r\n', ' ').replace('\n', ' ').strip()
        return sql_query
    else:
        raise ValueError("Запрос с указанным ID не найден")
