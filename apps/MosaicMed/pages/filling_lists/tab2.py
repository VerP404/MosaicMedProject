import base64
import io
import os
import re
import tempfile
import pandas as pd
from openpyxl import load_workbook
from dash import dcc, html, Input, Output, State, dash_table
from database.db_conn import engine
from services.MosaicMed.app import app
from sqlalchemy import create_engine


def clean_diagnosis(diagnosis):
    return re.sub(r'(\.\d).*', r'\1', str(diagnosis))


def auto_adjust_column_width(file_path):
    wb = load_workbook(file_path)
    ws = wb.active
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    wb.save(file_path)


def create_comparison_string(row):
    patient = row['Пациент']
    dob = row['ДР']
    combined = f"{patient}{dob}"
    clean_combined = re.sub(r'[\s\-\ё]', '', combined).lower()
    return clean_combined


def clean_excel(file_path):
    group_name = pd.read_excel(file_path, header=None).iloc[0, 0]
    df = pd.read_excel(file_path, skiprows=5, header=None)
    column_names = ['Пациент', 'ДР', 'Пол', 'Взят на учет: Дата', 'Взят на учет: Код',
                    'Диагноз: Код', 'Диагноз: Дата', 'Диагноз: Стадия', 'Снят с учета: Дата', 'Снят с учета: Код',
                    'Рег. номер', 'Код района', 'Адрес']
    df.columns = column_names[:df.shape[1]]
    df = df.ffill()
    df['Диагноз: Код'] = df['Диагноз: Код'].apply(clean_diagnosis)
    df['Группа'] = group_name
    df['для сравнения'] = df.apply(create_comparison_string, axis=1)
    return df


def process_folder(folder_path):
    all_data = pd.DataFrame()
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx'):
            file_path = os.path.join(folder_path, file_name)
            df = clean_excel(file_path)
            all_data = pd.concat([all_data, df], ignore_index=True)
    output_file_path = os.path.join(folder_path, 'combined_cleaned.xlsx')
    all_data.to_excel(output_file_path, index=False)
    auto_adjust_column_width(output_file_path)
    return output_file_path


def add_enp(df, engine):
    query_people = 'SELECT "FIO", "DR", "ENP" FROM iszl.people_data'
    db_data = pd.read_sql(query_people, engine)


    db_data['для сравнения'] = db_data.apply(
        lambda row: re.sub(r'[\s\-\ё]', '', f"{row['FIO']}{row['DR']}").lower(),
        axis=1
    )

    df = df.merge(db_data[['для сравнения', 'ENP']], on='для сравнения', how='left')
    df['ENP'] = df['ENP'].fillna('не найден')
    return df


def add_oms_status(df, engine):
    query_oms = f"""
    SELECT "ЕНП", "Диагноз основной (DS1)"
    FROM oms.oms_data
    WHERE "Цель" = '3'
    """
    oms_data = pd.read_sql(query_oms, engine)

    oms_data['ЕНП_DS1'] = oms_data.apply(
        lambda row: row['ЕНП'] + re.sub(r' .+', '', row['Диагноз основной (DS1)']),
        axis=1
    )

    oms_dict = set(oms_data['ЕНП_DS1'].values)

    df['Статус талона'] = df.apply(
        lambda row: 'да' if row['ENP'] + row['Диагноз: Код'] in oms_dict else 'нет', axis=1
    )

    return df


def calculate_status_counts(df):
    status_counts = {
        'Да': df[df['Статус талона'] == 'да'].shape[0],
        'Нет': df[(df['Статус талона'] == 'нет') & (df['ENP'] != 'не найден')].shape[0],
        'Не найдено': df[df['ENP'] == 'не найден'].shape[0]
    }
    return status_counts


def create_status_table(status_counts):
    total = sum(status_counts.values())
    data = [
        {'Статус': 'Да', 'Количество': status_counts['Да']},
        {'Статус': 'Нет', 'Количество': status_counts['Нет']},
        {'Статус': 'Не найдено', 'Количество': status_counts['Не найдено']},
        {'Статус': 'Итого', 'Количество': total}
    ]
    return dash_table.DataTable(
        data=data,
        columns=[{'name': 'Статус', 'id': 'Статус'}, {'name': 'Количество', 'id': 'Количество'}],
        style_table={'width': '50%', 'margin': 'auto'},
        style_header={'textAlign': 'center', 'fontWeight': 'bold'},
        style_data={'textAlign': 'center'}
    )


tab_layout_vokod = html.Div([
    html.Div(
        "Выберите файлы xlsx, полученные из ВОКОД. Где всего столбцов 13, а строка с пациентами начинается с 5. Будут корректно отображены Пациенты, добавлены ЕНП и проставлено наличие любого талона по цели 3 с диагнозом в таблице.",
        className='alert alert-info mt-3'
    ),
    html.Div(id='status-table'),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Выберите файлы xlsx из ВОКОД', id='select-files-button', className='btn btn-primary'),
        multiple=True,
        className='mb-3'
    ),
    html.Div(id='file-list', className='mb-3'),
    html.Button('Обработать', id='process-button', className='btn btn-success'),
    html.Div(id='output-table', className='mt-3'),
])


@app.callback(
    Output('file-list', 'children'),
    Input('upload-data', 'filename')
)
def display_files(filenames):
    if filenames is not None:
        return html.Ul([html.Li(filename) for filename in filenames])
    return 'Выберите файлы'


@app.callback(
    [Output('output-table', 'children'),
     Output('status-table', 'children')],
    Input('process-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_files(n_clicks, contents, filenames):
    if n_clicks is not None and contents is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for content, filename in zip(contents, filenames):
                data = base64.b64decode(content.split(',')[1])
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(data)
            combined_file_path = process_folder(temp_dir)
            df = pd.read_excel(combined_file_path)


            df = add_enp(df, engine)
            df = add_oms_status(df, engine)

            # Удаляем столбец 'для сравнения' перед отображением
            df.drop(columns=['для сравнения'], inplace=True)

            status_counts = calculate_status_counts(df)
            status_table = create_status_table(status_counts)

            return dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                page_size=5,
                export_format='xlsx',
                style_table={'overflowX': 'auto'},
                style_header={'whiteSpace': 'normal', 'textAlign': 'center'},
                style_data={'whiteSpace': 'normal', 'textAlign': 'center'}
            ), status_table
    return '', ''
