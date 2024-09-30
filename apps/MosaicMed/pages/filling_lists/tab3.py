import base64
import os
import tempfile
import pandas as pd
from dash import dcc, html, Input, Output, State, dash_table
from sqlalchemy import create_engine
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc

type_page = "tab-layout-smo"

markdown_text = """  
Обрабатывает стандартные файлы, присланные страховыми медицинскими организациями.
В файле должна быть 1 лист с данными пациентов - остальные листы убрать!
"""

def get_sql_data(talons):
    query = f"""
    SELECT "Талон", "Источник", "Цель", "Начало лечения", "Окончание лечения", "Врач", "Подразделение",
           SUBSTRING("Диагноз основной (DS1)", 1, POSITION(' ' IN "Диагноз основной (DS1)") - 1) AS "DS1"
    FROM oms_data
    WHERE "Талон" IN ({', '.join([f"'{talon}'" for talon in talons])})
    """
    return pd.read_sql(query, engine)


def process_insurance_file(file_path, insurance):
    try:
        if file_path.endswith('.xls'):
            read_engine = 'xlrd'
        else:
            read_engine = 'openpyxl'

        if insurance == 'ИНКОМЕД':
            df = pd.read_excel(file_path, engine=read_engine, dtype=str)  # Считываем весь файл как есть для ИНКОМЕД
            card_column = "№ карты"
        elif insurance == 'СОГАЗ':
            header_row = 4  # Заголовки в 5 строке
            data_start_row = 6  # Данные с 7 строки

            # Читаем заголовки отдельно
            headers_df = pd.read_excel(file_path, engine=read_engine, dtype=str, header=None, nrows=1,
                                       skiprows=header_row)
            headers = headers_df.iloc[0].tolist()

            # Читаем данные начиная с нужной строки
            df = pd.read_excel(file_path, engine=read_engine, dtype=str, header=None, skiprows=data_start_row)
            df.columns = headers  # Присваиваем заголовки

            # Убираем ';' в конце значений столбца "Номер карты"
            if 'Номер карты' in df.columns:
                df['Номер карты'] = df['Номер карты'].str.replace(';', '')
            card_column = "Номер карты"
        else:
            df = pd.read_excel(file_path, engine=read_engine, dtype=str)
            card_column = ""

        if card_column:
            talons = df[card_column].unique().tolist()
            sql_data = get_sql_data(talons)
            df = df.merge(sql_data, how='left', left_on=card_column, right_on='Талон')

        return df
    except Exception as e:
        print(f"Error processing file: {e}")
        return pd.DataFrame()  # Возвращаем пустой DataFrame в случае ошибки


tab_layout_smo = html.Div([
    dbc.Alert(html.Div(
        [
            dcc.Markdown(markdown_text),
        ]
    ),
        color="info"),
    html.Div("Выберите страховую компанию:", className='mb-2'),
    dcc.Dropdown(
        id=f'insurance-dropdown-{type_page}',
        options=[
            {'label': 'ИНКОМЕД', 'value': 'ИНКОМЕД'},
            {'label': 'СОГАЗ', 'value': 'СОГАЗ'}
        ],
        placeholder="Выберите страховую компанию"
    ),
    dcc.Upload(
        id=f'upload-data-{type_page}',
        children=html.Button('Выберите файл xls или xlsx', id=f'select-file-button-{type_page}',
                             className='btn btn-primary'),
        multiple=False,  # Только один файл
        className='mb-3'
    ),
    html.Button('Заполнить', id=f'process-button-{type_page}', className='btn btn-success'),
    html.Div(id=f'output-table-{type_page}', className='mt-3')
])


@app.callback(
    Output(f'output-table-{type_page}', 'children'),
    Input(f'process-button-{type_page}', 'n_clicks'),
    State(f'upload-data-{type_page}', 'contents'),
    State(f'upload-data-{type_page}', 'filename'),
    State(f'insurance-dropdown-{type_page}', 'value')
)
def process_file(n_clicks, contents, filename, insurance):
    if n_clicks is not None and contents is not None and insurance is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            # Сохраняем файл с нужным расширением
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + filename.split('.')[-1]) as temp_file:
                temp_file.write(decoded)
                temp_file_path = temp_file.name
            df = process_insurance_file(temp_file_path, insurance)
            if df.empty:
                return 'Ошибка обработки файла. Пожалуйста, проверьте правильность файла и попробуйте снова.'

            # Преобразуем все ключи и значения в строки
            df.columns = df.columns.astype(str)
            df = df.map(str)

            return dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                page_size=7,  # Пагинация на 15 строк
                export_format='xlsx',  # Выгрузка в xlsx
                style_table={'overflowX': 'auto'},
                style_header={'whiteSpace': 'normal', 'textAlign': 'center'},
                style_data={'whiteSpace': 'normal', 'textAlign': 'center'}
            )
        except Exception as e:
            return f'Ошибка при загрузке файла: {e}'
    return ''


if __name__ == '__main__':
    app.layout = tab_layout_smo
    app.run_server(debug=True)
