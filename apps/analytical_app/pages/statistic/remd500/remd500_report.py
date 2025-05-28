# remd500.py
import base64
import io
import re
import pandas as pd
from datetime import datetime, timedelta

import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine

type_page = "remd500"


# Утилита для парсинга загруженных файлов
def parse_contents(contents, filename):
    if not contents:
        return pd.DataFrame()
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        return pd.read_csv(io.StringIO(decoded.decode('cp1251')), sep=';', low_memory=False, dtype=str)
    except Exception:
        return pd.DataFrame()


layout_remd500 = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(html.H5("Фильтры (РЭМД 500)", className="mb-0"), width="auto"),
                        ],
                        align="center",
                        justify="between"
                    )
                ),
                dbc.CardBody(
                    [
                        # ------ Блок фильтров (дата начала, дата окончания, кнопка) ------
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Дата начала:", className="mb-0"),
                                        dcc.DatePickerSingle(
                                            id=f"date-picker-start-{type_page}",
                                            first_day_of_week=1,
                                            date=datetime.now().date() - timedelta(days=7),
                                            display_format="DD.MM.YYYY",
                                            className="mt-1"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Дата окончания:", className="mb-0"),
                                        dcc.DatePickerSingle(
                                            id=f"date-picker-end-{type_page}",
                                            first_day_of_week=1,
                                            date=datetime.now().date(),
                                            display_format="DD.MM.YYYY",
                                            className="mt-1"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Сформировать отчет",
                                            id=f"generate-report-button-{type_page}",
                                            color="primary",
                                            className="mt-4"
                                        )
                                    ],
                                    width=3
                                )
                            ],
                            className="mb-3"
                        ),

                        # ------ ВМЕСТО старой строки с html.Div(...) -> 4 карточки в одной строке ------
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("ЭМД", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-emd-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([
                                                html.Div([
                                                    dcc.Dropdown(
                                                        id=f"emd-date-type-dropdown-{type_page}",
                                                        options=[
                                                            {"label": "По дате исходного документа",
                                                             "value": "document_date"},
                                                            {"label": "По дате формирования ЭМД",
                                                             "value": "formation_date"},
                                                            {"label": "По дате последней отправки в РИР",
                                                             "value": "sending_date"}
                                                        ],
                                                        value="formation_date",  # Значение по умолчанию
                                                        clearable=False,
                                                        style={"marginBottom": "10px"}
                                                    ),
                                                    dcc.Dropdown(
                                                        id=f"emd-status-dropdown-{type_page}",
                                                        options=[
                                                            {"label": "Все", "value": "all"},
                                                            {"label": "Ошибка отправки", "value": "Ошибка отправки"},
                                                            {"label": "Ошибка регистрации документа",
                                                             "value": "Ошибка регистрации документа"},
                                                            {"label": "Документ успешно зарегистрирован",
                                                             "value": "Документ успешно зарегистрирован"},
                                                            {"label": "Не отправлено", "value": "-"},
                                                            {"label": "Отправлен в РИР", "value": "Отправлен в РИР"},
                                                            {"label": "Прочие", "value": "other"}
                                                        ],
                                                        value=["Документ успешно зарегистрирован"],
                                                        # По умолчанию выбираем "Все"
                                                        multi=True,  # Включаем мультивыбор
                                                        clearable=False,
                                                        style={"marginBottom": "10px"}
                                                    ),
                                                    html.Div(
                                                        id=f"emd-count-{type_page}",
                                                        style={"fontSize": "16px", "marginTop": "10px",
                                                               "fontWeight": "bold"}
                                                    )
                                                ])
                                            ])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("Рецепты", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-recipes-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([
                                                html.Div(
                                                    [
                                                        dcc.Dropdown(
                                                            id=f"recipe-verification-dropdown-{type_page}",
                                                            options=[
                                                                {"label": "Все", "value": "all"},
                                                                {"label": "2 из 2", "value": "2 из 2"},
                                                                {"label": "Не подлежит отправке в РЭМД",
                                                                 "value": "Не подлежит отправке в РЭМД"},
                                                                {"label": "0 из 2", "value": "0 из 2"},
                                                                {"label": "1 из 2", "value": "1 из 2"},
                                                                {"label": "-", "value": "-"},
                                                                {"label": "Прочие", "value": "other"}
                                                            ],
                                                            value=["2 из 2"],
                                                            multi=True,
                                                            clearable=False,
                                                            style={"marginBottom": "10px"}
                                                        ),
                                                        dcc.Dropdown(
                                                            id=f"recipe-status-dropdown-{type_page}",
                                                            options=[
                                                                {"label": "Все", "value": "all"},
                                                                {"label": "Отправлен", "value": "Отправлен"},
                                                                {"label": "Зарегистрирован",
                                                                 "value": "Зарегистрирован"},
                                                                {"label": "Ошибка регистрации",
                                                                 "value": "Ошибка регистрации"},
                                                                {"label": "Не подлежит отправке",
                                                                 "value": "Не подлежит отправке"},
                                                                {"label": "-", "value": "-"},
                                                                {"label": "Прочие", "value": "other"}
                                                            ],
                                                            value=["Зарегистрирован"],
                                                            multi=True,
                                                            clearable=False,
                                                            style={"marginBottom": "10px"}
                                                        ),
                                                        html.Div(
                                                            id=f"recipe-count-{type_page}",
                                                            style={"fontSize": "16px", "marginTop": "10px",
                                                                   "fontWeight": "bold"}
                                                        )
                                                    ]
                                                )
                                            ])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("Справки", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-reference-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("Смертность", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-death-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                            ],
                            className="mb-3"
                        ),
                    ]
                ),
            ],
            className="mb-3"
        ),

        dbc.Tabs(
            [
                dbc.Tab(
                    dbc.Card(
                        [
                            dbc.CardHeader("Отчет по группе"),
                            dbc.CardBody(
                                dash_table.DataTable(
                                    id=f"group-report-table-{type_page}",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left'},
                                    export_format="xlsx",
                                    page_size=15
                                )
                            ),
                        ],
                        className="mb-3"
                    ),
                    label="По специальности (групповой)"
                ),
                dbc.Tab(
                    dbc.Card(
                        [
                            dbc.CardHeader("Отчет по врачу"),
                            dbc.CardBody(
                                dash_table.DataTable(
                                    id=f"doctor-report-table-{type_page}",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left'},
                                    export_format="xlsx",
                                    page_size=15
                                )
                            ),
                        ],
                        className="mb-3"
                    ),
                    label="По врачам"
                ),
                dbc.Tab(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Table(
                                    style={"width": "100%", "tableLayout": "fixed"},
                                    children=[
                                        html.Tr([
                                            html.Td(
                                                dcc.Upload(
                                                    id=f"upload-emd-{type_page}",
                                                    children=dbc.Button("Выбрать файл ЭМД", size="sm",
                                                                        className="w-100"),
                                                    multiple=False,
                                                    style={"display": "block"}
                                                ),
                                                style={"width": "25%", "padding": "4px"}
                                            ),
                                            html.Td(
                                                html.Div(id=f"output-emd-filename-{type_page}"),
                                                style={"width": "75%", "padding": "4px"}
                                            ),
                                        ]),
                                        html.Tr([
                                            html.Td(
                                                dcc.Upload(
                                                    id=f"upload-spr-{type_page}",
                                                    children=dbc.Button("Выбрать файл Справки", size="sm",
                                                                        className="w-100"),
                                                    multiple=False,
                                                    style={"display": "block"}
                                                ),
                                                style={"padding": "4px"}
                                            ),
                                            html.Td(
                                                html.Div(id=f"output-spr-filename-{type_page}"),
                                                style={"padding": "4px"}
                                            ),
                                        ]),
                                        html.Tr([
                                            html.Td(
                                                dcc.Upload(
                                                    id=f"upload-smer-{type_page}",
                                                    children=dbc.Button("Выбрать файл Смертность", size="sm",
                                                                        className="w-100"),
                                                    multiple=False,
                                                    style={"display": "block"}
                                                ),
                                                style={"padding": "4px"}
                                            ),
                                            html.Td(
                                                html.Div(id=f"output-smer-filename-{type_page}"),
                                                style={"padding": "4px"}
                                            ),
                                        ]),
                                        html.Tr([
                                            html.Td(
                                                dcc.Upload(
                                                    id=f"upload-rec-{type_page}",
                                                    children=dbc.Button("Выбрать файл Рецепты", size="sm",
                                                                        className="w-100"),
                                                    multiple=False,
                                                    style={"display": "block"}
                                                ),
                                                style={"padding": "4px"}
                                            ),
                                            html.Td(
                                                html.Div(id=f"output-rec-filename-{type_page}"),
                                                style={"padding": "4px"}
                                            ),
                                        ]),
                                    ]
                                ),
                                # Отдельная зелёная кнопка снизу, растянутая по ширине таблицы
                                dbc.Button(
                                    "Обработать файлы",
                                    id=f"manual-process-button-{type_page}",
                                    color="success",
                                    className="mt-3"
                                ),
                                # Статус после нажатия
                                html.Div(id=f"manual-process-status-{type_page}", className="mt-2")
                            ]
                        )
                    ),
                    label="Отчет по ручной выгрузке"
                ),
            ]
        ),

        html.Div(id=f"report-status-{type_page}", className="mt-2"),
        html.Div(id=f"manual-new-tables-{type_page}", className="mt-3"),
    ],
    style={"padding": "15px"}
)


# Callbacks для обновления имён загруженных файлов
@app.callback(
    Output(f"output-emd-filename-{type_page}", "children"),
    Input(f"upload-emd-{type_page}", "filename")
)
def update_emd_filename(filename):
    return html.Div(f"Загружен файл: {filename}") if filename else ""


@app.callback(
    Output(f"output-spr-filename-{type_page}", "children"),
    Input(f"upload-spr-{type_page}", "filename")
)
def update_spr_filename(filename):
    return html.Div(f"Загружен файл: {filename}") if filename else ""


@app.callback(
    Output(f"output-smer-filename-{type_page}", "children"),
    Input(f"upload-smer-{type_page}", "filename")
)
def update_smer_filename(filename):
    return html.Div(f"Загружен файл: {filename}") if filename else ""


@app.callback(
    Output(f"output-rec-filename-{type_page}", "children"),
    Input(f"upload-rec-{type_page}", "filename")
)
def update_rec_filename(filename):
    return html.Div(f"Загружен файл: {filename}") if filename else ""


# Новый callback для ручной выгрузки
@app.callback(
    Output(f"manual-new-tables-{type_page}", "children"),
    Output(f"manual-process-status-{type_page}", "children"),
    Input(f"manual-process-button-{type_page}", "n_clicks"),
    State(f"upload-emd-{type_page}", "contents"),
    State(f"upload-emd-{type_page}", "filename"),
    State(f"upload-spr-{type_page}", "contents"),
    State(f"upload-spr-{type_page}", "filename"),
    State(f"upload-smer-{type_page}", "contents"),
    State(f"upload-smer-{type_page}", "filename"),
    State(f"upload-rec-{type_page}", "contents"),
    State(f"upload-rec-{type_page}", "filename"),
)
def process_manual(n_clicks, emd_c, emd_fn, spr_c, spr_fn, smer_c, smer_fn, rec_c, rec_fn):
    if not n_clicks:
        return [], ""
    try:
        # Парсим данные
        df_emd = parse_contents(emd_c, emd_fn)
        df_spr = parse_contents(spr_c, spr_fn)
        df_smer = parse_contents(smer_c, smer_fn)
        df_rec = parse_contents(rec_c, rec_fn)

        # --- Обработка ЭМД ---
        df_emd['Тип'] = 'ЭМД'
        df_emd['Подразделение'] = df_emd['Подразделение'].str.lower()
        df_emd['Обособленное подразделение'] = df_emd['Обособленное подразделение'].str.lower()
        df_emd['Врач'] = df_emd.apply(
            lambda
                row: f"{row['Врач']}, {row['Подразделение'] if pd.notna(row['Подразделение']) else row['Обособленное подразделение']}",
            axis=1
        )
        result_df_emd = df_emd[['Врач', 'Статус отправки в РИР.РЭМД', 'Тип']].rename(
            columns={'Статус отправки в РИР.РЭМД': 'Статус'}
        )

        # --- Обработка Справок ---
        df_spr['Тип'] = 'Справки'
        result_df_spr = df_spr[['Врач', 'Статус', 'Тип']]

        # --- Обработка Смертность ---
        df_smer['Тип'] = 'Смертность'

        def split_vrach_and_department(vrach_str):
            if pd.isna(vrach_str): return pd.Series([vrach_str, ''])
            parts = vrach_str.split(') (')
            if len(parts) == 2:
                name_specialty = parts[0] + ')'
                dept = parts[1].rstrip(')')
                return pd.Series([name_specialty.strip(), dept.lower()])
            return pd.Series([vrach_str, ''])

        df_smer[['Врач', 'Подразделение']] = df_smer['Врач'].apply(split_vrach_and_department)
        result_df_smer = df_smer[['Врач', 'Статус отправки ЭМД', 'Тип']].rename(
            columns={'Статус отправки ЭМД': 'Статус'}
        )

        # --- Обработка Рецептов ---
        df_rec['Тип'] = 'Рецепты'
        df_rec['Подразделение'] = df_rec['Подразделение'].str.lower()

        def convert_name(full_name):
            parts = full_name.split()
            if len(parts) >= 3:
                return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
            if len(parts) == 2:
                return f"{parts[0]} {parts[1][0]}."
            return full_name

        df_rec['Ф.И.О. врача'] = df_rec['Ф.И.О. врача'].apply(convert_name)
        df_rec['Врач'] = df_rec.apply(
            lambda
                r: f"{r['Ф.И.О. врача']} ({r['Должность врача']}), {r['Подразделение'] if pd.notna(r['Подразделение']) else r['Обособленное подразделение']}",
            axis=1
        )
        result_df_rec = df_rec[['Врач', 'Статус отправки в РЭМД', 'Тип']].rename(
            columns={'Статус отправки в РЭМД': 'Статус'}
        )

        # --- Объединяем и фильтруем ---
        combined = pd.concat([result_df_emd, result_df_spr, result_df_smer, result_df_rec], ignore_index=True)
        filtered = combined[combined['Статус'].isin([
            'Документ успешно зарегистрирован', 'Зарегистрирован',
            'Зарегистрирована', 'Зарегистрировано'
        ])].copy()

        # --- Специальности ---
        filtered['Специальность'] = filtered['Врач'].str.extract(r'\((.*?)\)')

        def replace_specialty(s):
            m = s.lower() if isinstance(s, str) else s
            if 'семейный врач' in m: return 'ВОП'
            if m in ['врач по медицинской профилактике', 'врач-терапевт',
                     'врач-терапевт участковый']: return 'Терапевт'
            if m in ['врач-педиатр', 'врач-педиатр участковый']: return 'Педиатр'
            return s

        filtered['Специальность'] = filtered['Специальность'].apply(replace_specialty)
        filtered = filtered[filtered['Специальность'].isin(['ВОП', 'Терапевт', 'Педиатр'])]

        # --- Категории ---
        bins = [0, 99, 499, float('inf')]
        labels = ['до 100', '100-499', '>500']

        # --- Сводная таблица по группам ---
        doctor_pivot = filtered.pivot_table(
            index=['Специальность', 'Врач'],
            columns='Тип',
            aggfunc='size',
            fill_value=0
        )
        doctor_pivot['Итого'] = doctor_pivot.sum(axis=1)
        doctor_df = doctor_pivot.reset_index()
        doctor_df['Категория'] = pd.cut(doctor_df['Итого'], bins=bins, labels=labels)

        grouped_pivot = doctor_df.groupby(['Специальность', 'Категория']).size().unstack(fill_value=0)
        grouped_pivot['Итого'] = grouped_pivot.sum(axis=1)

        # Таблицы Dash
        table_group = dash_table.DataTable(
            data=grouped_pivot.reset_index().to_dict('records'),
            columns=[{'name': i, 'id': i} for i in grouped_pivot.reset_index().columns],
            export_format='xlsx', page_size=15
        )
        table_doctor = dash_table.DataTable(
            data=doctor_df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in doctor_df.columns],
            export_format='xlsx', page_size=15
        )

        return [
            html.H5("Сводная информация (Новые данные)"),
            table_group,
            html.H5("Список по врачам (Новые данные)"),
            table_doctor
        ], "Обработка завершена успешно."

    except Exception as e:
        return [], f"Ошибка при обработке: {str(e)}"


# ОБЪЕДИНЁННЫЙ CALLBACK: формирует отчет и получает даты обновления для каждой таблицы
@app.callback(
    [
        Output(f"group-report-table-{type_page}", "data"),
        Output(f"group-report-table-{type_page}", "columns"),
        Output(f"doctor-report-table-{type_page}", "data"),
        Output(f"doctor-report-table-{type_page}", "columns"),
        Output(f"last-updated-emd-{type_page}", "children"),
        Output(f"last-updated-recipes-{type_page}", "children"),
        Output(f"last-updated-reference-{type_page}", "children"),
        Output(f"last-updated-death-{type_page}", "children"),
        Output(f"report-status-{type_page}", "children"),
        Output(f"emd-count-{type_page}", "children"),
        Output(f"recipe-count-{type_page}", "children"),
    ],
    Input(f"generate-report-button-{type_page}", "n_clicks"),
    State(f"date-picker-start-{type_page}", "date"),
    State(f"date-picker-end-{type_page}", "date"),
    State(f"emd-date-type-dropdown-{type_page}", "value"),
    State(f"emd-status-dropdown-{type_page}", "value"),
    State(f"recipe-verification-dropdown-{type_page}", "value"),
    State(f"recipe-status-dropdown-{type_page}", "value"),
)
def generate_remd500_report(n_clicks, start_date, end_date, emd_date_type, emd_selected_statuses, recipe_verification,
                            recipe_status):
    if not n_clicks:
        return [], [], [], [], "", "", "", "", "", "итого: 0", "итого: 0"

    if not start_date or not end_date:
        return [], [], [], [], "", "", "", "", "Не выбраны даты!", "итого: 0", "итого: 0"

    try:
        start_date_str = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date_str = pd.to_datetime(end_date).strftime("%Y-%m-%d")

        accepted_statuses = [
            "Документ успешно зарегистрирован",
            "Зарегистрирован",
            "Зарегистрирована",
            "Зарегистрировано"
        ]

        emd_known_statuses = [
            "Ошибка отправки",
            "Ошибка регистрации документа",
            "Документ успешно зарегистрирован",
            "-",
            "Отправлен в РИР"
        ]
        # Получаем все возможные статусы из базы данных
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT DISTINCT sending_status
                FROM load_data_emd
            """)).fetchall()
        emd_all_statuses = [row[0] for row in result]  # Все статусы в базе
        emd_unknown_statuses = [status for status in emd_all_statuses if
                                status not in emd_known_statuses]  # Неизвестные статусы

        # ✅ Если список пуст или None — также выбираем все статусы
        if not emd_selected_statuses or len(emd_selected_statuses) == 0:
            emd_selected_statuses = emd_known_statuses + emd_unknown_statuses

        # ✅ Если выбрано "Прочие" — добавляем только неизвестные статусы
        if "other" in emd_selected_statuses:
            emd_selected_statuses.remove("other")
            emd_selected_statuses += emd_unknown_statuses

        # ✅ Если выбрано "Все" — добавляем все статусы (известные + неизвестные)
        if "all" in emd_selected_statuses:
            emd_selected_statuses.remove("all")
            emd_selected_statuses = emd_known_statuses + emd_unknown_statuses

        # Получаем данные по каждой таблице с учетом форматов даты
        # 1) ЭМД (формат "DD.MM.YYYY HH24:MI")
        query_emd = f"""
            SELECT
                doctor,
                sending_status AS status,
                'ЭМД' AS type,
                {emd_date_type} AS document_date
            FROM load_data_emd
            WHERE NULLIF({emd_date_type}, '-') IS NOT NULL
                  AND {emd_date_type} ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}$'
                  AND to_date({emd_date_type}, 'DD.MM.YYYY HH24:MI')
                      BETWEEN to_date('{start_date}', 'YYYY-MM-DD')
                          AND to_date('{end_date}', 'YYYY-MM-DD')
                  AND sending_status IN ({",".join(f"'{status}'" for status in emd_selected_statuses)})
        """
        if not emd_selected_statuses:
            df_emd = pd.DataFrame()
        else:
            df_emd = pd.read_sql(query_emd, con=engine)
        # 2) Рецепты
        # Получаем все возможные статусы из базы данных
        recipe_known_verifications = [
            "2 из 2",
            "Не подлежит отправке в РЭМД",
            "0 из 2",
            "1 из 2",
            "-"
        ]
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT distinct emd_verification
                FROM load_data_recipes
            """)).fetchall()
        recipe_all_verifications = [row[0] for row in result]
        recipe_unknown_verifications = [status for status in recipe_all_verifications if
                                        status not in recipe_known_verifications]

        # ✅ Если список пуст или None — также выбираем все статусы
        if not recipe_verification or len(recipe_verification) == 0:
            recipe_verification = recipe_known_verifications + recipe_unknown_verifications
        # ✅ Если выбрано "Прочие" — добавляем только неизвестные статусы
        if "other" in recipe_verification:
            recipe_verification.remove("other")
            recipe_verification += recipe_unknown_verifications
        # ✅ Если выбрано "Все" — добавляем все статусы (известные + неизвестные)
        if "all" in recipe_verification:
            recipe_verification.remove("all")
            recipe_verification = recipe_known_verifications + recipe_unknown_verifications

        recipe_known_status = [
            "Отправлен",
            "Зарегистрирован",
            "Ошибка регистрации",
            "Не подлежит отправке",
            "-"]

        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT distinct sending_status_remd
                FROM load_data_recipes
            """)).fetchall()

        recipe_all_status = [row[0] for row in result]
        recipe_unknown_status = [status for status in recipe_all_status if
                                 status not in recipe_known_status]
        # ✅ Если список пуст или None — также выбираем все статусы
        if not recipe_status or len(recipe_status) == 0:
            recipe_status = recipe_known_status + recipe_unknown_status
        # ✅ Если выбрано "Прочие" — добавляем только неизвестные статусы
        if "other" in recipe_status:
            recipe_status.remove("other")
            recipe_status += recipe_unknown_status
        # ✅ Если выбрано "Все" — добавляем все статусы (известные + неизвестные)
        if "all" in recipe_status:
            recipe_status.remove("all")
            recipe_status = recipe_known_status + recipe_unknown_status

        query_recipes = f"""
            SELECT
                doctor_full_name AS doctor,
                sending_status_remd AS status,
                'Рецепты' AS type,
                date AS document_date
            FROM load_data_recipes
            WHERE to_date(date, 'DD.MM.YYYY')
                      BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD')
                          AND to_date('{end_date_str}', 'YYYY-MM-DD')
                      AND emd_verification IN ({",".join(f"'{v}'" for v in recipe_verification)})
                      AND sending_status_remd IN ({",".join(f"'{s}'" for s in recipe_status)})
        """
        df_recipes = pd.read_sql(query_recipes, con=engine)

        # 3) Справки (формат "DD.MM.YYYY")
        query_reference = f"""
            SELECT
                doctor,
                status,
                'Справки' AS type,
                issue_date AS document_date
            FROM load_data_reference
            WHERE to_date(issue_date, 'DD.MM.YYYY')
                  BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD')
                      AND to_date('{end_date_str}', 'YYYY-MM-DD')
        """
        df_reference = pd.read_sql(query_reference, con=engine)

        # 4) Смертность (формат "YYYY-MM-DD")
        query_death = f"""
            SELECT doctor, emd_sending_status AS status, 'Смертность' AS type, issue_date AS document_date 
            FROM load_data_death 
            WHERE issue_date != '-' 
            AND to_date(issue_date, 'YYYY-MM-DD') BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD') AND to_date('{end_date_str}', 'YYYY-MM-DD')
        """
        df_death = pd.read_sql(query_death, con=engine)

        # Объединяем данные
        combined_df = pd.concat([df_emd, df_recipes, df_reference, df_death], ignore_index=True)

        # Фильтруем по статусам
        filtered_df = combined_df[combined_df['status'].isin(accepted_statuses)].copy()

        # Извлечение специальности из строки врача (если указано в скобках)
        def extract_specialty(doctor_str):
            if pd.isna(doctor_str):
                return None
            match = re.search(r"\((.*?)\)", doctor_str)
            return match.group(1) if match else None

        filtered_df['specialty'] = filtered_df['doctor'].apply(extract_specialty)

        # Формируем отчет по врачам: группировка по (doctor, specialty, type)
        doctor_pivot = (
            filtered_df
            .groupby(['doctor', 'specialty', 'type'], observed=False)
            .size()
            .reset_index(name='count')
        )

        # Формируем групповой отчет: группировка по специальности
        group_pivot = (
            filtered_df
            .groupby('specialty', observed=False)
            .size()
            .reset_index(name='total')
        )

        bins = [0, 99, 499, float('inf')]
        labels = ['до 100', '100-499', '>500']
        group_pivot['Категория'] = pd.cut(group_pivot['total'], bins=bins, labels=labels)
        group_summary = group_pivot.groupby('Категория', observed=False)['total'].sum().reset_index()

        group_columns = [{"name": col, "id": col} for col in group_summary.columns]
        doctor_columns = [{"name": col, "id": col} for col in doctor_pivot.columns]

        # Получаем дату последнего обновления для каждой таблицы
        with engine.connect() as conn:
            row_emd = conn.execute(text("SELECT MAX(updated_at) FROM load_data_emd")).fetchone()
            row_recipes = conn.execute(text("SELECT MAX(updated_at) FROM load_data_recipes")).fetchone()
            row_reference = conn.execute(text("SELECT MAX(updated_at) FROM load_data_reference")).fetchone()
            row_death = conn.execute(text("SELECT MAX(updated_at) FROM load_data_death")).fetchone()

        last_updated_emd = row_emd[0].strftime('%d.%m.%Y %H:%M') if row_emd and row_emd[0] else "Нет данных"
        last_updated_recipes = row_recipes[0].strftime('%d.%m.%Y %H:%M') if row_recipes and row_recipes[
            0] else "Нет данных"
        last_updated_reference = row_reference[0].strftime('%d.%m.%Y %H:%M') if row_reference and row_reference[
            0] else "Нет данных"
        last_updated_death = row_death[0].strftime('%d.%m.%Y %H:%M') if row_death and row_death[0] else "Нет данных"

        return (
            group_summary.to_dict('records'),
            group_columns,
            doctor_pivot.to_dict('records'),
            doctor_columns,
            f"{last_updated_emd}",
            f"{last_updated_recipes}",
            f"{last_updated_reference}",
            f"{last_updated_death}",
            "",
            f"итого: {len(df_emd)}",
            f"итого: {len(df_recipes)}"
        )

    except Exception as e:
        return [], [], [], [], "", "", "", "", f"Ошибка при формировании отчета: {str(e)}", "итого: 0", "итого: 0"
