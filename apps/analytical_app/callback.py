from sqlalchemy import text
import pandas as pd


class TableUpdater:

    @staticmethod
    def query_to_df(engine, sql_query, bind_params=None):
        # Очищаем запрос от переносов строк и лишних пробелов
        sql_query_cleaned = sql_query.replace('\n', ' ').replace('\r', ' ').strip()

        # Выполняем запрос с параметрами
        with engine.connect() as conn:
            query = text(sql_query_cleaned)
            if bind_params:
                query = query.bindparams(**bind_params)
            result = conn.execute(query)

            # Получаем результаты
            columns = [desc[0] for desc in result.cursor.description]
            rows = result.fetchall()

            # Преобразуем результат в DataFrame
            df = pd.DataFrame(rows, columns=columns)

            if len(df) == 0:
                return [], []

            # Преобразуем для отображения в таблице Dash
            columns = [{'name': col, 'id': col} for col in df.columns]
            data = df.to_dict('records')
            return columns, data
