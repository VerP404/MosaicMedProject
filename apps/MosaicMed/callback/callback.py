import os

import pandas as pd
import datetime
from sqlalchemy import text

from database.db_conn import engine
from services.MosaicMed.utils import get_extracted_names_list_doctors, get_extracted_names_list_specialist

months_dict = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
    7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}


# получаем текущий отчетный месяц (по 4 число следующего за отчетным)
def get_current_reporting_month():
    current_date = datetime.datetime.now()
    current_day = current_date.day
    current_month_number = current_date.month

    if current_day <= 4:
        if current_month_number == 1:  # для января возвращаем декабрь
            current_month_number = 12
        else:
            current_month_number = current_month_number - 1
    current_month_name = f"Текущий отчетный месяц: {months_dict.get(current_month_number)}"
    return current_month_number, current_month_name


# Фильтр по месяцам
def get_filter_month(sel_month):
    selected_month = months_dict.get(sel_month)
    selected_month_name = f'Выбранный месяц: {selected_month}'
    return selected_month_name


# Фильтр по начале и окончанию отчета
def get_selected_dates(start_date, end_date):
    start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    start_date_formatted = start_date_obj.strftime('%d.%m.%Y')
    end_date_formatted = end_date_obj.strftime('%d.%m.%Y')

    selected_dates_text = f'Выбранные даты: с {start_date_formatted} по {end_date_formatted}'
    return selected_dates_text


# Фильтр по специальности
def get_selected_specialist(selected_value, sql_query):
    extracted_names_list = get_extracted_names_list_specialist(engine, sql_query)
    dropdown_options = [{'label': item, 'value': item} for item in extracted_names_list]
    selected_item_text = f'Выбранная специальность: {selected_value}'
    return dropdown_options, selected_item_text


# Фильтр по врачу
def get_selected_doctors(selected_value):
    extracted_names_list = get_extracted_names_list_doctors(engine)
    # Убедимся, что все значения корректны
    dropdown_options = [{'label': item, 'value': item} for item in extracted_names_list if item]
    selected_item_text = f'Выбранный врач: {selected_value}' if selected_value else 'Доктор не выбран'
    return dropdown_options, selected_item_text




def query_last_record_sql(schema_name, name_table):
    # Получить последнюю запись из базы данных
    with engine.connect() as conn:
        query = text(f'''
        SELECT "File_name", "File_date", "Count", "name_text"
        FROM {schema_name}.{name_table}
        ORDER BY CAST("File_date" AS TIMESTAMP) DESC
        LIMIT 1
        ''')
        result = conn.execute(query)
        last_record = result.fetchone()
        file_name = last_record[0] if last_record else None
        return file_name


def last_file_csv_in_directory(directory):
    try:
        # Проверка существования директории
        if not os.path.exists(directory):
            return None, f"Директория не найдена: {directory}"

        # Получение списка файлов в директории
        files = os.listdir(directory)

        # Фильтрация списка файлов по расширению .csv
        csv_files = [file for file in files if file.endswith('.csv')]
        # Сортировка файлов по дате последнего изменения
        sorted_files = sorted(csv_files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
        if sorted_files:
            latest_file = sorted_files[0]
            return latest_file, None
        else:
            return None, 'Нет CSV файлов в директории'

    except Exception as e:
        return None, f"Ошибка: {str(e)}"


class TableUpdater:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def build_sql_query(sql_q, sql_conditions):
        return sql_q

    @staticmethod
    def get_sql_conditions(month, cur_month):
        if (month == str(cur_month)) or (month == '0'):
            return 'or ("Номер счёта" is null)'
        else:
            return ''

    @staticmethod
    def get_sql_month(month):
        if month == '0':
            return '%%'
        elif len(month) == 1:
            return f'%/0{month}/%'
        else:
            return f'%/{month}/%'

    def query_to_df(self, s_q: object, bind_params: object = None) -> object:
        with self.engine.connect() as conn:
            query = text(s_q)
            if bind_params:
                query = query.bindparams(**bind_params)
            result = conn.execute(query)
            columns = [desc[0] for desc in result.cursor.description]
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=columns)
            if len(df) == 0:
                return [], []
            columns = [{'name': col, 'id': col} for col in df.columns]
            data = df.to_dict('records')
            return columns, data

    def query_to_df_data(self, s_q: object, bind_params: object = None) -> object:
        with self.engine.connect() as conn:
            query = text(s_q)
            if bind_params:
                query = query.bindparams(**bind_params)
            result = conn.execute(query)
            columns = [desc[0] for desc in result.cursor.description]
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=columns)
            return df
