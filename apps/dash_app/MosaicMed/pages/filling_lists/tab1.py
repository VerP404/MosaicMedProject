import base64
import io
import pandas as pd
from sqlalchemy import text
from dash import html, dcc, Output, Input, dash_table, State, callback_context
from database.db_conn import engine
from services.MosaicMed.app import app
from services.MosaicMed.pages.filling_lists.query import sql_query_df_from_sql
import dash_bootstrap_components as dbc

type_page = "add-contact-info"
alert_text = """Поиск возможен по нескольким полям, но точнее находится по номеру полиса (ЕНП)  
Информация ищется в базе IT-отдела и может отличаться от реальной!!!
"""
tab_layout_add_contact_info = html.Div([
    dcc.Store(id='selected-column-name-store'),
    dbc.Alert(dcc.Markdown(alert_text), color="danger", style={'padding': '0 0 0 10px'}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Нажмите или перетащите файл Excel для добавления контактной информации',
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
        multiple=True
    ),
    html.Hr(),
    html.Div(id='file-inform'),
    html.Hr(),
    html.H5("Выберите тип сопоставления:"),
    dcc.RadioItems(
        id='processing-type',
        options=[
            {'label': 'По ЕНП', 'value': 'ENP'},
            {'label': 'По ФИО и ДР', 'value': 'FIO_DR'},
            {'label': 'По Фамилии, Имени, Отчеству и Дате рождения', 'value': 'FIO_DR_etc'}
        ],
        value='ENP'
    ),
    html.Hr(),
    html.H5("Укажите столбцы в файле:"),
    html.Div(id='column-selected'),
    html.Hr(),
    html.Button('Обработать файл', id=f'get-data-button-{type_page}'),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    html.Hr(),
    html.Div(
        [
            html.H3('Обработанный файл', className='label'),
            dash_table.DataTable(id=f'result-table-{type_page}', columns=[],
                                 editable=True,
                                 filter_action="native",
                                 sort_action="native",
                                 sort_mode='multi',
                                 export_format='xlsx',
                                 export_headers='display',
                                 ),
        ], className='block'),
])


def file_processing(data, eng, **kwargs):
    # Получаем выгрузку из базы населения в виде датафрейма
    df_from_sql = pd.read_sql(text(sql_query_df_from_sql), eng.connect(), dtype='str')
    df_from_sql_enp = 'ЕНП'
    df_from_sql_fam = 'Фамилия'
    df_from_sql_name = 'Имя'
    df_from_sql_sur = 'Отчество'
    df_from_sql_dr = 'Дата рождения'

    data_enp = kwargs.get('data_enp')
    data_fio = kwargs.get('data_fio')
    data_fam = kwargs.get('data_fam')
    data_name = kwargs.get('data_name')
    data_sur = kwargs.get('data_sur')
    data_dr = kwargs.get('data_dr')

    if data_enp is not None:
        result_df = data.merge(df_from_sql, left_on=data_enp, right_on=df_from_sql_enp, how='left')
    elif data_fio is not None:
        # Форматирование даты рождения в нужный формат
        data[data_dr] = pd.to_datetime(data[data_dr], format='%d.%m.%Y')
        data[data_dr] = data[data_dr].dt.strftime('%d.%m.%Y')
        df_from_sql['ФИО'] = df_from_sql[df_from_sql_fam] + ' ' + df_from_sql[df_from_sql_name] + ' ' + df_from_sql[
            df_from_sql_sur]
        result_df = data.merge(df_from_sql, left_on=[data_fio, data_dr], right_on=['ФИО', df_from_sql_dr], how='left')
    else:
        # Форматирование даты рождения в нужный формат
        try:
            data[data_dr] = pd.to_datetime(data[data_dr], format='%d.%m.%Y')
            data[data_dr] = data[data_dr].dt.strftime('%d.%m.%Y')
        except ValueError:
            data[data_dr] = pd.to_datetime(data[data_dr])
            data[data_dr] = data[data_dr].dt.strftime('%d.%m.%Y')
        data['ФИО ДР'] = data[data_fam] + ' ' + data[data_name] + ' ' + data[data_sur] + ' ' + data[data_dr]
        data['ФИО ДР'] = data['ФИО ДР'].str.replace(' ', '')
        df_from_sql['ФИО ДР'] = df_from_sql[df_from_sql_fam] + ' ' + df_from_sql[df_from_sql_name] + ' ' + df_from_sql[
            df_from_sql_sur] + ' ' + df_from_sql[df_from_sql_dr]
        df_from_sql['ФИО ДР'] = df_from_sql['ФИО ДР'].str.replace(' ', '')

        result_df = data.merge(df_from_sql, left_on='ФИО ДР', right_on='ФИО ДР', how='left')
    return result_df


@app.callback(Output('file-inform', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_file_info(contents, filename):
    if contents is None:
        return None

    content_type, content_string = contents[0].split(',')
    decoded = io.BytesIO(base64.b64decode(content_string))

    df = pd.read_excel(decoded, dtype=str)
    columns = df.columns
    info_page = html.Div([
        html.Div(f'Файл загружен: {filename[0]}'),
        html.Div(f'Столбцы: {", ".join(columns)}')
    ])

    return info_page


@app.callback(
    Output('column-selected', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    Input('processing-type', 'value')
)
def update_column_selection(contents, filename, report_type):
    if contents is None:
        return None

    content_type, content_string = contents[0].split(',')
    decoded = io.BytesIO(base64.b64decode(content_string))
    # Преобразуйте байтовые данные в датафрейм
    df = pd.read_excel(decoded, dtype=str)
    # Получите список столбцов из датафрейма
    columns = df.columns

    dropdown = html.Div([])
    if report_type == 'ENP':
        dropdown = html.Div([
            html.Label("ЕНП", style={'width': '150px'}),
            dcc.Dropdown(
                id='column-enp',
                options=[{'label': col, 'value': col} for col in columns],
                style={'width': '300px'}
            ),
            html.Div(id='column-fio'),
            html.Div(id='column-fam'),
            html.Div(id='column-name'),
            html.Div(id='column-sur'),
            html.Div(id='column-dr'),
        ], style={'display': 'flex', 'align-items': 'center'})

    elif report_type == 'FIO_DR':
        dropdown = html.Div([
            html.Div([
                html.Label("ФИО", style={'width': '150px'}),
                dcc.Dropdown(
                    id='column-fio',
                    options=[{'label': col, 'value': col} for col in columns],
                    style={'width': '300px'}
                )
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div([
                html.Label("Дата рождения", style={'width': '150px'}),
                dcc.Dropdown(
                    id='column-dr',
                    options=[{'label': col, 'value': col} for col in columns],
                    style={'width': '300px'}
                )
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div(id='column-enp'),
            html.Div(id='column-fam'),
            html.Div(id='column-name'),
            html.Div(id='column-sur'),
        ], style={'display': 'flex', 'flex-direction': 'column'})
    elif report_type == 'FIO_DR_etc':
        dropdown = html.Div([
            html.Div([
                html.Label("Фамилия", style={'width': '150px'}),
                dcc.Dropdown(
                    id='column-fam',
                    options=[{'label': col, 'value': col} for col in columns],
                    style={'width': '300px'}
                )
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div([
                html.Label("Имя", style={'width': '150px'}),
                dcc.Dropdown(
                    id='column-name',
                    options=[{'label': col, 'value': col} for col in columns],
                    style={'width': '300px'}
                )
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div([
                html.Label("Отчество", style={'width': '150px'}),
                dcc.Dropdown(
                    id='column-sur',
                    options=[{'label': col, 'value': col} for col in columns],
                    style={'width': '300px'}
                )
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div([
                html.Label("Дата рождения", style={'width': '150px'}),
                dcc.Dropdown(
                    id='column-dr',
                    options=[{'label': col, 'value': col} for col in columns],
                    style={'width': '300px'}
                )
            ], style={'display': 'flex', 'align-items': 'center'}),
            html.Div(id='column-enp'),
            html.Div(id='column-fio'),
        ], style={'display': 'flex', 'flex-direction': 'column'})

    return dropdown


@app.callback(
    Output('selected-column-name-store', 'data'),
    Input('column-enp', 'value'),
    Input('column-fio', 'value'),
    Input('column-fam', 'value'),
    Input('column-name', 'value'),
    Input('column-sur', 'value'),
    Input('column-dr', 'value')
)
def update_selected_fam_name_sur_columns(column_enp, column_fio, column_fam, column_name, column_sur, column_dr):
    selected_columns = []
    if column_enp:
        selected_columns.append(column_enp)
    elif column_fio:
        selected_columns.append(column_fio)
        selected_columns.append(column_dr)
    elif column_fam:
        selected_columns.append(column_fam)
        selected_columns.append(column_name)
        selected_columns.append(column_sur)
        selected_columns.append(column_dr)
    return selected_columns


@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')
     ],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('processing-type', 'value'),
     State('selected-column-name-store', 'data')]
)
def data_processing(n_clicks, contents, report_type, selected_column_name):
    if n_clicks is None:
        return [], [], html.Div()

    # Получить контекст вызова
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == f'get-data-button-{type_page}' and None not in selected_column_name:
        loading_output = html.Div([dcc.Loading(type="default")])
        content_type, content_string = contents[0].split(',')
        decoded = io.BytesIO(base64.b64decode(content_string))
        # Преобразуйте байтовые данные в датафрейм
        df = pd.read_excel(decoded, dtype=str)

        processed_data = pd.DataFrame()
        if report_type == 'ENP' and (selected_column_name is not None):
            processed_data = file_processing(df, engine,
                                             data_enp=selected_column_name[0])
        elif report_type == 'FIO_DR':
            processed_data = file_processing(df, engine,
                                             data_fio=selected_column_name[0],
                                             data_dr=selected_column_name[1])
        elif report_type == 'FIO_DR_etc':
            processed_data = file_processing(df, engine,
                                             data_fam=selected_column_name[0],
                                             data_name=selected_column_name[1],
                                             data_sur=selected_column_name[2],
                                             data_dr=selected_column_name[3])

        columns = [{'name': col, 'id': col} for col in processed_data.columns]
        data = processed_data.to_dict('records')
        return columns, data, loading_output
    else:
        return [], [], html.Div()


