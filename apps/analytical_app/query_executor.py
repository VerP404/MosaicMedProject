import os

from sqlalchemy import create_engine, text

from config.settings import BASE_DIR

# Подключение к SQLite
engine = create_engine(f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}')


def execute_query(sql_query):
    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        return result.fetchall()


def text_sql_query(id):
    # Формируем корректный запрос с подстановкой id
    query = execute_query(f"SELECT query FROM sql_manager_sqlquery WHERE id = {id}")

    # Очищаем запрос от лишних символов форматирования
    sql_query = query[0][0].replace('\r\n', ' ').replace('\n', ' ').strip()

    return sql_query
