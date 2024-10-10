import datetime

from sqlalchemy import text
import pandas as pd

from apps.analytical_app.query_executor import engine


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


def get_selected_dates(start_date, end_date):
    start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    start_date_formatted = start_date_obj.strftime('%d.%m.%Y')
    end_date_formatted = end_date_obj.strftime('%d.%m.%Y')

    selected_dates_text = f'Выбранные даты: с {start_date_formatted} по {end_date_formatted}'
    return selected_dates_text


def get_extracted_names_list_doctors(engine):
    with engine.connect() as conn:
        sql_query = """
        SELECT DISTINCT
        department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) || '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
        CASE
            WHEN doctor_profile ~ '\(.*\)' THEN
                substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
             ELSE
                 doctor_profile
        END AS extracted_names
        FROM data_loader_omsdata
        order by extracted_names
        """
        query = text(sql_query)
        result = conn.execute(query)
        extracted_names_list = [row[0] for row in result.fetchall()]
        return extracted_names_list


def get_selected_doctors(selected_value):
    extracted_names_list = get_extracted_names_list_doctors(engine)
    dropdown_options = [{'label': item, 'value': item} for item in extracted_names_list if item]
    selected_item_text = f'Выбранный врач: {selected_value}' if selected_value else 'Доктор не выбран'
    return dropdown_options, selected_item_text


def get_extracted_names_list_specialist(engine, sql_query):
    with engine.connect() as conn:
        query = text(sql_query)
        result = conn.execute(query)
        extracted_names_list = [row[0] for row in result.fetchall()]
        return extracted_names_list


def get_selected_specialist(selected_value, sql_query):
    extracted_names_list = get_extracted_names_list_specialist(engine, sql_query)
    dropdown_options = [{'label': item, 'value': item} for item in extracted_names_list]
    selected_item_text = f'Выбранная специальность: {selected_value}'
    return dropdown_options, selected_item_text
