from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import re
import base64
import io
from services.MosaicMed.app import app
from database.db_conn import engine


# Загрузка последних данных из базы данных
def load_latest_data():
    latest_data = {}
    try:
        with engine.connect() as connection:
            doctor_data_query = 'SELECT * FROM emd_500_doctor_data ORDER BY "Дата" DESC, "Время" DESC'
            doctor_svod_data_query = 'SELECT * FROM emd_500_doctor_svod_data ORDER BY "Дата" DESC, "Время" DESC'
            latest_data['doctor_data'] = pd.read_sql(doctor_data_query, connection)
            latest_data['doctor_svod_data'] = pd.read_sql(doctor_svod_data_query, connection)
    except Exception as e:
        print(f"Ошибка при загрузке данных из базы: {str(e)}")
        latest_data['doctor_data'] = pd.DataFrame()
        latest_data['doctor_svod_data'] = pd.DataFrame()
    return latest_data

latest_data = load_latest_data()

# Извлекаем дату, время и отчетный месяц из первых строк
if not latest_data['doctor_data'].empty:
    last_date = latest_data['doctor_data']['Дата'].iloc[0]
    last_time = latest_data['doctor_data']['Время'].iloc[0]
    last_month = latest_data['doctor_data']['Отчетный месяц'].iloc[0]
else:
    last_date = ''
    last_time = ''
    last_month = ''

remd_500 = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Загрузка и обработка данных"), className="mb-2")
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Загрузите файлы"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-emd',
                        children=html.Div(['выберите файл ЭМД']),
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
                        multiple=False
                    ),
                    html.Div(id='output-emd-filename', className="mb-2"),
                    dcc.Upload(
                        id='upload-spr',
                        children=html.Div(['выберите файл Справки']),
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
                        multiple=False
                    ),
                    html.Div(id='output-spr-filename', className="mb-2"),
                    dcc.Upload(
                        id='upload-smer',
                        children=html.Div(['выберите файл Смертность']),
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
                        multiple=False
                    ),
                    html.Div(id='output-smer-filename', className="mb-2"),
                    dcc.Upload(
                        id='upload-rec',
                        children=html.Div(['выберите файл Рецепты']),
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
                        multiple=False
                    ),
                    html.Div(id='output-rec-filename', className="mb-2"),
                    dbc.Button("Обработать файлы", id="process-button", color="primary", className="mt-3"),
                    html.Div(id='process-status', className="mt-2")
                ])
            ]),
            width=6
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Сохранить результат"),
                dbc.CardBody([
                    dbc.Label("Дата и время"),
                    dcc.DatePickerSingle(
                        id='report-date',
                        display_format='YYYY-MM-DD',
                        date=pd.to_datetime('today').date()
                    ),
                    dbc.InputGroup([
                        dbc.InputGroupText("Время"),
                        dbc.Input(id='report-time', value=pd.to_datetime('now').strftime('%H:%M:%S'))
                    ], className="mb-3"),
                    dbc.Label("Отчетный месяц"),
                    dcc.Dropdown(
                        id='report-month',
                        options=[
                            {'label': month, 'value': month} for month in [
                                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
                            ]
                        ],
                        value=pd.to_datetime('today').strftime('%B')
                    ),
                    dbc.Button("Сохранить", id="save-button", color="success", className="mt-3"),
                    html.Div(id='save-status', className="mt-2")
                ])
            ]),
            width=6
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Div(id='old-tables', children=[
                html.H3("Сводная информация (Старые данные)"),
                dash_table.DataTable(
                    id='old-grouped-pivot-table',
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    export_format="xlsx"
                ),
                html.H3("Список по врачам (Старые данные)"),
                dash_table.DataTable(
                    id='old-pivot-table',
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    page_action='native',
                    page_current=0,
                    page_size=15,
                    export_format="xlsx"
                )
            ])
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Div(id='new-tables', children=[
                html.H3("Сводная информация (Новые данные)"),
                dash_table.DataTable(
                    id='grouped-pivot-table',
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    export_format="xlsx"
                ),
                html.H3("Список по врачам (Новые данные)"),
                dash_table.DataTable(
                    id='pivot-table',
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    filter_action="native",
                    page_action='native',
                    page_current=0,
                    page_size=15,
                    export_format="xlsx"
                )
            ])
        )
    ])
], fluid=True)

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('cp1251')), sep=';', low_memory=False, dtype='str')
    return df


@app.callback(
    Output('output-emd-filename', 'children'),
    Input('upload-emd', 'filename')
)
def update_emd_filename(filename):
    if filename is not None:
        return html.Div(f'Загружен файл: {filename}')
    return ""


@app.callback(
    Output('output-spr-filename', 'children'),
    Input('upload-spr', 'filename')
)
def update_spr_filename(filename):
    if filename is not None:
        return html.Div(f'Загружен файл: {filename}')
    return ""


@app.callback(
    Output('output-smer-filename', 'children'),
    Input('upload-smer', 'filename')
)
def update_smer_filename(filename):
    if filename is not None:
        return html.Div(f'Загружен файл: {filename}')
    return ""


@app.callback(
    Output('output-rec-filename', 'children'),
    Input('upload-rec', 'filename')
)
def update_rec_filename(filename):
    if filename is not None:
        return html.Div(f'Загружен файл: {filename}')
    return ""


@app.callback(
    Output('new-tables', 'children'),
    Output('process-status', 'children'),
    Input('process-button', 'n_clicks'),
    State('upload-emd', 'contents'),
    State('upload-emd', 'filename'),
    State('upload-spr', 'contents'),
    State('upload-spr', 'filename'),
    State('upload-smer', 'contents'),
    State('upload-smer', 'filename'),
    State('upload-rec', 'contents'),
    State('upload-rec', 'filename')
)
def update_output(n_clicks, emd_contents, emd_filename, spr_contents, spr_filename, smer_contents, smer_filename, rec_contents, rec_filename):
    if not n_clicks:
        return "", ""

    try:
        df_emd = parse_contents(emd_contents, emd_filename)
        df_spr = parse_contents(spr_contents, spr_filename)
        df_smer = parse_contents(smer_contents, smer_filename)
        df_rec = parse_contents(rec_contents, rec_filename)

        # Обработка ЭМД
        df_emd['Тип'] = 'ЭМД'
        df_emd['Подразделение'] = df_emd['Подразделение'].str.lower()
        df_emd['Обособленное подразделение'] = df_emd['Обособленное подразделение'].str.lower()
        df_emd['Врач и Подразделение'] = df_emd.apply(
            lambda row: f"{row['Врач']}, {row['Подразделение'] if pd.notna(row['Подразделение']) else row['Обособленное подразделение']}", axis=1
        )
        result_df_emd = df_emd[['Врач и Подразделение', 'Статус отправки в РИР.РЭМД', 'Тип']]

        # Обработка Справки
        df_spr['Тип'] = 'Справки'
        result_df_spr = df_spr[['Врач', 'Статус', 'Тип']]

        # Обработка Смертность
        df_smer['Тип'] = 'Смертность'

        def split_vrach_and_department(vrach_str):
            if pd.isna(vrach_str):
                return pd.Series([vrach_str, ''])
            parts = vrach_str.split(') (')
            if len(parts) == 2:
                name_specialty = parts[0] + ')'
                department = parts[1].strip().lower()
                if department.endswith(')'):
                    department = department[:-1]
                return pd.Series([name_specialty.strip(), department])
            return pd.Series([vrach_str, ''])

        df_smer[['Врач и специальность', 'Подразделение']] = df_smer['Врач'].apply(split_vrach_and_department)

        def remove_space_between_initials(vrach_specialty):
            if pd.isna(vrach_specialty):
                return vrach_specialty
            return re.sub(r'(\b\w\.)\s+(\w\.)', r'\1\2', str(vrach_specialty))

        df_smer['Врач и специальность'] = df_smer['Врач и специальность'].apply(remove_space_between_initials)

        df_smer['Врач'] = df_smer.apply(lambda row: f"{row['Врач и специальность']}, {row['Подразделение']}", axis=1)
        result_df_smer = df_smer[['Врач', 'Статус отправки ЭМД', 'Тип']]

        # Обработка льготных рецептов
        df_rec['Тип'] = 'Рецепты'
        df_rec['Подразделение'] = df_rec['Подразделение'].str.lower()

        def convert_name(full_name):
            parts = full_name.split()
            if len(parts) >= 3:
                last_name = parts[0]
                first_name = parts[1]
                middle_name = parts[2]
                return f"{last_name} {first_name[0]}.{middle_name[0]}."
            else:
                return full_name

        df_rec['Ф.И.О. врача'] = df_rec['Ф.И.О. врача'].apply(convert_name)
        df_rec['ФИО и Должность'] = df_rec.apply(lambda row: f"{row['Ф.И.О. врача']} ({row['Должность врача']})", axis=1)
        df_rec['ФИО, Должность и Подразделение'] = df_rec.apply(
            lambda row: f"{row['ФИО и Должность']}, {row['Подразделение'] if pd.notna(row['Подразделение']) else row['Обособленное подразделение']}", axis=1
        )
        result_df_rec = df_rec[['ФИО, Должность и Подразделение', 'Статус отправки в РЭМД', 'Тип']]

        result_df_emd.rename(columns={'Врач и Подразделение': 'Врач', 'Статус отправки в РИР.РЭМД': 'Статус'}, inplace=True)
        result_df_rec.rename(columns={'ФИО, Должность и Подразделение': 'Врач', 'Статус отправки в РЭМД': 'Статус'}, inplace=True)
        result_df_smer.rename(columns={'Статус отправки ЭМД': 'Статус'}, inplace=True)

        combined_df = pd.concat([result_df_emd, result_df_rec, result_df_spr, result_df_smer])

        filtered_df = combined_df[combined_df['Статус'].isin(['Документ успешно зарегистрирован', 'Зарегистрирован', 'Зарегистрирована', 'Зарегистрировано'])]

        def extract_specialty(vrach_str):
            match = re.search(r'\((.*?)\)', vrach_str)
            return match.group(1) if match else None

        filtered_df['Специальность'] = filtered_df['Врач'].apply(extract_specialty)

        def replace_specialty(specialty):
            if specialty in ['врач общей практики (семейный врач']:
                return 'ВОП'
            elif specialty in ['врач по медицинской профилактике', 'врач-терапевт', 'врач-терапевт участковый']:
                return 'Терапевт'
            elif specialty in ['врач-педиатр', 'врач-педиатр участковый']:
                return 'Педиатр'
            else:
                return specialty

        filtered_df['Специальность'] = filtered_df['Специальность'].apply(replace_specialty)
        filtered_df = filtered_df[filtered_df['Специальность'].isin(['ВОП', 'Терапевт', 'Педиатр'])]

        pivot_table = filtered_df.pivot_table(index=['Врач', 'Специальность'], columns='Тип', aggfunc='size', fill_value=0)
        pivot_table['Итого'] = pivot_table.sum(axis=1)

        bins = [0, 99, 499, float('inf')]
        labels = ['до 100', '100-499', '>500']
        pivot_table['Категория'] = pd.cut(pivot_table['Итого'], bins=bins, labels=labels)

        grouped_pivot = pivot_table.pivot_table(index='Специальность', columns='Категория', aggfunc='size', fill_value=0)
        grouped_pivot['Итого'] = grouped_pivot.sum(axis=1)

        return [
            html.H3("Сводная информация (Новые данные)"),
            dash_table.DataTable(
                data=grouped_pivot.reset_index().to_dict('records'),
                columns=[{"name": i, "id": i} for i in grouped_pivot.reset_index().columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                filter_action="native",
                export_format="xlsx"
            ),
            html.H3("Список по врачам (Новые данные)"),
            dash_table.DataTable(
                data=pivot_table.reset_index().to_dict('records'),
                columns=[{"name": i, "id": i} for i in pivot_table.reset_index().columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                filter_action="native",
                page_action='native',
                page_current=0,
                page_size=15,
                export_format="xlsx"
            )
        ], "Обработка завершена успешно."
    except Exception as e:
        return "", f"Ошибка при обработке файлов: {str(e)}"


@app.callback(
    Output('save-status', 'children'),
    Input('save-button', 'n_clicks'),
    State('report-date', 'date'),
    State('report-time', 'value'),
    State('report-month', 'value'),
    State('grouped-pivot-table', 'data'),
    State('pivot-table', 'data')
)
def save_to_database(n_clicks, report_date, report_time, report_month, grouped_pivot_data, pivot_table_data):
    if not n_clicks:
        return ""

    try:
        grouped_pivot_df = pd.DataFrame(grouped_pivot_data)
        pivot_table_df = pd.DataFrame(pivot_table_data)

        grouped_pivot_df['Дата'] = report_date
        grouped_pivot_df['Время'] = report_time
        grouped_pivot_df['Отчетный месяц'] = report_month

        pivot_table_df['Дата'] = report_date
        pivot_table_df['Время'] = report_time
        pivot_table_df['Отчетный месяц'] = report_month

        grouped_pivot_df.to_sql('emd_500_doctor_svod_data', con=engine, if_exists='replace', index=False)
        pivot_table_df.to_sql('emd_500_doctor_data', con=engine, if_exists='replace', index=False)

        return "Данные успешно сохранены."
    except Exception as e:
        return f"Ошибка при сохранении данных: {str(e)}"


@app.callback(
    Output('old-tables', 'children'),
    Input('url', 'pathname')
)
def load_old_data(pathname):
    try:
        grouped_pivot_df = pd.read_sql('SELECT * FROM emd_500_doctor_svod_data', con=engine)
        pivot_table_df = pd.read_sql('SELECT * FROM emd_500_doctor_data', con=engine)

        date_info = grouped_pivot_df[['Дата', 'Время', 'Отчетный месяц']].iloc[0].to_dict()

        return [
            html.H3(f"Сводная информация (Предыдущая выгрузка) Дата: {date_info['Дата']} Время: {date_info['Время']} Отчетный месяц: {date_info['Отчетный месяц']}"),
            dash_table.DataTable(
                data=grouped_pivot_df.drop(columns=['Дата', 'Время', 'Отчетный месяц']).reset_index().to_dict('records'),
                columns=[{"name": i, "id": i} for i in grouped_pivot_df.drop(columns=['Дата', 'Время', 'Отчетный месяц']).reset_index().columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                filter_action="native",
                export_format="xlsx"
            ),
            html.H3("Список по врачам (Предыдущая выгрузка)"),
            dash_table.DataTable(
                data=pivot_table_df.drop(columns=['Дата', 'Время', 'Отчетный месяц']).reset_index().to_dict('records'),
                columns=[{"name": i, "id": i} for i in pivot_table_df.drop(columns=['Дата', 'Время', 'Отчетный месяц']).reset_index().columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                filter_action="native",
                page_action='native',
                page_current=0,
                page_size=15,
                export_format="xlsx"
            )
        ]
    except Exception as e:
        return [html.Div(f"Ошибка при загрузке данных: {str(e)}")]
