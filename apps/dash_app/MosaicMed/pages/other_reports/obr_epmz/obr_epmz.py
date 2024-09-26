import base64
import io
from datetime import datetime

import pandas as pd
from dash import html, dcc, Output, Input, dash_table, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from services.MosaicMed.app import app

type_page = "obr_epmz"

alert_text = """Условия:
Необходимо выгрузить 2 файла: журнал ЭПМЗ и журнал обращений за одинаковый период.  
- ### Журнал ЭПМЗ  
	фильтры:  
		-начало и окончание париода (должно совпадать)  
		-тип ЭПМЗ - посещение врача (указывает на то, что берется конкретнный прием врача - даже если амбулаторная цель 30.  
		 Диспансеризация не учитывается, так как запись через ЕПГУ на нее осуществляется иначе)  
- ### Журнал обращений  
	фильтры:  
		-начало и окончание париода (должно совпадать)  
		-тип приема - первичный  
	сортировки:  
		-источник записи - ЕПГУ  (указывает на то, что это слот выложен на ЕПГУ)  
		-создавший - ЕПГУ (указывает на то, что записан через ЕПГУ, то есть не конкурентный)
"""


def record_requests_report(df_obr, df_epmz):
    '''
    Обрабатываем файл выгрузки записанных из журнала ЭПМЗ
    '''
    df_obr = df_obr[(df_obr['Источник записи'] == 'ЕПГУ') & (df_obr['Создавший'] == 'ЕПГУ')]
    df_obr = df_obr[
        df_obr['Должность'].str.contains('терапевт', case=False, na=False) | df_obr['Должность'].str.contains('общей',
                                                                                                              case=False,
                                                                                                              na=False)]
    hospital_dict = {
        'ГП 3, ДП 1 (пер. Ботанический, 49)': 'ДП 1',
        'ГП 11, ДП 8 (ул. Машиностроителей, 76)': 'ДП 8',
        'ГП 3, Корпус №1 (пер. Ботанический, 47)': 'ГП 3',
        'Городская поликлиника 3, Корпус 4 Отделение женской консультации ул Геращенко, 3, Акушерско-гинекологическое отделение': 'ЖК',
        'Городская поликлиника 11, Корпус 3, ул Машиностроителей, 13б': 'ГП 11',
        'Городская поликлиника 3, Отделение амбулаторно-поликлинической помощи №2, Корпус 6 (ул Остроухова, 1)': 'ОАПП 2',
        'Городская поликлиника 3, Отделение амбулаторно-поликлинической помощи №1, Корпус 2 (ул Шишкова, 71)': 'ОАПП 1',
        'Городская поликлиника 11, Детская поликлиника 8, Корпус №7, ул Машиностроителей, 51, Профилактическое отделение': 'ДП 8 к7'
    }
    df_obr['Подразделение'] = df_obr['Подразделение'].map(hospital_dict)
    # Преобразование столбца 'Дата приема' в формат "гггг-мм-дд"
    df_obr['Дата приема'] = df_obr['Дата приема'].apply(
        lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d'))
    df_obr['Отчество'] = df_obr['Отчество'].fillna('')
    df_obr['Пациент_дата_записи'] = df_obr['Фамилия'] + ' ' + df_obr['Имя'] + ' ' + df_obr['Отчество'] + ' ' + df_obr[
        'Дата рождения'] + ' ' + df_obr['Дата приема'] + ' ' + df_obr['Фамилия.1']
    '''
    Обрабатываем файл выгрузки ЭПМЗ
    '''
    df_epmz = df_epmz[df_epmz['Тип ЭПМЗ'].str.contains('Посещение врача', case=False, na=False)]
    # Преобразование столбцов 'Дата окончания лечения' в формат "гггг-мм-дд" и 'Д.р. пациента' в формат "гггг-мм-дд"
    df_epmz['Дата окончания лечения'] = df_epmz['Дата окончания лечения'].apply(
        lambda x: datetime.strptime(x, '%d.%m.%Y %H:%M').strftime('%Y-%m-%d'))
    df_epmz['Д.р. пациента'] = df_epmz['Д.р. пациента'].apply(
        lambda x: datetime.strptime(x, '%d.%m.%Y').strftime('%Y-%m-%d'))
    df_epmz['Врач'] = df_epmz['ФИО врача'].apply(lambda x: x.split()[0])
    df_epmz['Пациент_дата_приема'] = df_epmz['ФИО пациента'] + ' ' + df_epmz['Д.р. пациента'] + ' ' + df_epmz[
        'Дата окончания лечения'] + ' ' + df_epmz['Врач']

    '''
    Объединяем датафреймы и получаем итоговый датафрейм
    '''
    df_itog = df_obr.merge(df_epmz, left_on='Пациент_дата_записи', right_on='Пациент_дата_приема', how='left')
    df_grouped = df_itog.groupby('Подразделение_x').agg({
        'Фамилия': 'count',
        'ФИО пациента': [('Нет ЭПМЗ', lambda x: x.isna().sum())],
        'Не явился': [
            ('Отмечена неявка', lambda x: ((x == 'Да') & df_itog['ФИО пациента'].isna()).sum()),
            ('Не создан ЭПМЗ', lambda x: ((x == 'Нет') & df_itog['ФИО пациента'].isna()).sum())
        ]
    }).reset_index()
    # Выпрямление иерархии столбцов
    df_grouped.columns = df_grouped.columns.get_level_values(1)
    # Переименование столбцов
    df_grouped = df_grouped.rename(columns={'': 'Корпус', 'count': 'Всего'})
    # Создание строки итого
    df_itogo = pd.concat([df_grouped, pd.DataFrame(df_grouped.sum(axis=0)).T], ignore_index=True)
    # Переименование последней строки
    df_itogo.iloc[-1, 0] = 'Итого'
    df_itogo['% Не создан ЭПМЗ от Всего'] = round((df_itogo['Не создан ЭПМЗ'] / df_itogo['Всего'] * 100).fillna(0), 2)
    return df_itogo


tab_layout_other_obr_epmz = html.Div([
    html.H3('Отчет по записанным пациентам через ЕПГУ и созданным на них ЭПМЗ по взрослой участковой службе',
            className='label'),
    dbc.Alert(dcc.Markdown(alert_text), color="danger", style={'padding': '0 0 0 10px'}),
    dcc.Upload(
        id=f'upload-data1-{type_page}',
        children=html.Div([
            'Файл из журнала ЭПМЗ',
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True,

    ),
    html.Hr(),
    dcc.Upload(
        id=f'upload-data2-{type_page}',
        children=html.Div([
            'Файл из журнала ОБРАЩЕНИЙ',
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True,
    ),
    html.Label('Выгрузка электронных медицинских карт'),
    dcc.Loading(id=f'loading-output1-{type_page}', type='default'),
    html.Div(id=f'output-data-upload1-{type_page}'),
    html.Hr(),
    html.Label('Выгрузка записанных пациентов'),
    dcc.Loading(id=f'loading-output2-{type_page}', type='default'),
    html.Div(id=f'output-data-upload2-{type_page}'),
    html.Hr(),
    html.Button('Обработать данные', id=f'process-button-{type_page}'),
    dcc.Loading(id=f'loading-output3-{type_page}', type='default'),
    html.Hr(),
    html.H3('Отчет по записанным пациентам через ЕПГУ и созданным на них ЭПМЗ по взрослой участковой службе',
            className='label'),
    html.Div(id=f'output-data-{type_page}'),
])


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('cp1251')), sep=';', dtype='str', on_bad_lines='skip')
    # Сбрасываем индекс
    df.reset_index(drop=True, inplace=True)
    return html.Div([
        html.H5(filename),
        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            export_format='xlsx',
            export_headers='display',
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode='multi',
            page_size=2
        )
    ])


@app.callback([Output(f'output-data-upload1-{type_page}', 'children'),
               Output(f'loading-output1-{type_page}', 'children')],
              Input(f'upload-data1-{type_page}', 'contents'),
              State(f'upload-data1-{type_page}', 'filename'),
              )
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        loading_output1 = html.Div([dcc.Loading(type="default")])
        children1 = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        return children1, loading_output1
    else:
        return [], []


@app.callback([Output(f'output-data-upload2-{type_page}', 'children'),
               Output(f'loading-output2-{type_page}', 'children')],
              Input(f'upload-data2-{type_page}', 'contents'),
              State(f'upload-data2-{type_page}', 'filename'),
              )
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        loading_output = html.Div([dcc.Loading(type="default")])
        children1 = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        return children1, loading_output
    else:
        return [], []


@app.callback(Output(f'output-data-{type_page}', 'children'),
              Output(f'loading-output3-{type_page}', 'children'),
              [Input(f'process-button-{type_page}', 'n_clicks')],
              [State(f'output-data-upload1-{type_page}', 'children'),
               State(f'output-data-upload2-{type_page}', 'children')])
def process_data(n_clicks, upload1_children, upload2_children):
    if n_clicks is None:
        raise PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    # Получаем данные из выгрузок
    df_obr = extract_dataframe_from_children(upload2_children)
    df_epmz = extract_dataframe_from_children(upload1_children)
    if df_obr is None or df_epmz is None:
        return "Загрузите корректные данныe. Файлы не загружены!.", loading_output
    # Обрабатываем данные
    try:
        result_df = record_requests_report(df_obr, df_epmz)
    except KeyError:
        return "Загрузите корректные данные. Не найдены поля в таблиц!", loading_output
    # Возвращаем результат в виде таблицы
    return dash_table.DataTable(
        data=result_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in result_df.columns],
        export_format='xlsx',
        export_headers='display',
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode='multi',
        style_table={'width': '600px'}
    ), loading_output


def extract_dataframe_from_children(children):
    if not children:
        return None

    table = children[0]
    try:
        data_list = table["props"]["children"][1]["props"]["data"]
        df = pd.DataFrame(data_list)
        return df
    except:
        return None
