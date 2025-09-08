# -*- coding: utf-8 -*-
"""
АНАЛИЗ ЗАПИСАННЫХ НА ПРИЕМ
Dash-приложение для анализа данных пациентов
Находит пересечения между списком ЕНП и обращениями пациентов
"""

import pandas as pd
import chardet
import io
import base64
from datetime import datetime
from dash import html, dcc, Input, Output, State, callback_context, dash_table, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

type_page = "appointment_analysis"


def detect_encoding(file_content):
    """Определяет кодировку файла"""
    result = chardet.detect(file_content)
    return result['encoding']


def read_csv_with_encoding(file_content, encoding):
    """Читает CSV файл с указанной кодировкой"""
    encodings_to_try = [encoding, 'utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']

    for enc in encodings_to_try:
        try:
            return pd.read_csv(io.StringIO(file_content.decode(enc)), sep=';', dtype=str)
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise Exception("Не удалось прочитать CSV файл ни с одной кодировкой")


# Статистика (замена твоего stats_html)
def build_stats_card(stats):
    total_enp = stats['total_enp_records']
    total_req = stats['total_requests_records']
    unique_enp = stats['unique_enp_in_file']
    unique_req = stats['unique_requests_in_file']
    common = stats['common_enp']
    result = stats['result_records']
    enp_field = stats.get('enp_field_used', 'ЕНП')

    return dbc.Card(
        dbc.CardBody([
            html.H5("📊 Результаты сверки", className="mb-3"),

            html.P(
                f"Сравнение выполнено по полю «{enp_field}». ",
                className="text-muted small"
            ),

            dbc.Row([
                dbc.Col([
                    html.H6("Файл с ЕНП - список людей/пациентов", className="mb-2"),
                    html.Div(f"Всего записей - строк в файле: {total_enp}", className="mb-1"),
                    html.Div(f"Всего уникальных людей/пациентов по ЕНП: {unique_enp}", className="mb-1"),
                ], md=4),

                dbc.Col([
                    html.H6("Файл из модуля обращений - записи пациентов на прием", className="mb-2"),
                    html.Div(f"Всего записей - строк в файле: {total_req}", className="mb-1"),
                    html.Div(f"Всего уникальных людей/пациентов по ЕНП: {unique_req}", className="mb-1"),
                ], md=4),

                dbc.Col([
                    html.H6("Совпадения - найденные люди из списка в записях на прием", className="mb-2"),
                    html.Div(f"Всего найдено записей - записано на прием: {result}", className="mb-1"),
                    html.Div(f"Всего уникальных людей/пациентов - записано на прием: {common}", className="mb-1"),
                ], md=4),
            ])
        ]),
        className="shadow-sm mb-4"
    )


def process_data(enp_df, requests_df, enp_field='ЕНП'):
    """Обрабатывает данные и находит пересечения"""
    try:
        # Проверяем наличие колонки ЕНП в Excel файле
        if enp_field not in enp_df.columns:
            return None, f"Ошибка: В файле с ЕНП нет колонки '{enp_field}'. Доступные колонки: {enp_df.columns.tolist()}"

        if 'ЕНП' not in requests_df.columns:
            return None, f"Ошибка: В файле с обращениями нет колонки 'ЕНП'. Доступные колонки: {requests_df.columns.tolist()}"

        # Очищаем данные от пустых ЕНП
        enp_clean = enp_df.dropna(subset=[enp_field])
        requests_clean = requests_df.dropna(subset=['ЕНП'])

        # Находим пересечения
        enp_set = set(enp_clean[enp_field].astype(str).str.replace('.0', '').str.strip())
        requests_set = set(requests_clean['ЕНП'].astype(str).str.replace('.0', '').str.strip())
        common_enp = enp_set.intersection(requests_set)

        if len(common_enp) == 0:
            return None, "Общих ЕНП не найдено!"

        # Фильтруем записи
        requests_clean = requests_clean.copy()
        requests_clean['ЕНП_str'] = requests_clean['ЕНП'].astype(str).str.replace('.0', '').str.strip()
        result_df = requests_clean[requests_clean['ЕНП_str'].isin(common_enp)]

        # Добавляем поле "Прием" с датой
        if 'Дата приема' in result_df.columns:
            result_df = result_df.copy()
            result_df['Прием'] = pd.to_datetime(result_df['Дата приема'], format='%Y-%m-%dT%H:%M',
                                                errors='coerce').dt.date

        # Удаляем служебную колонку
        if 'ЕНП_str' in result_df.columns:
            result_df = result_df.drop('ЕНП_str', axis=1)

        # Статистика
        stats = {
            'total_enp_records': len(enp_df),
            'total_requests_records': len(requests_df),
            'unique_enp_in_file': len(enp_set),
            'unique_requests_in_file': len(requests_set),
            'common_enp': len(common_enp),
            'result_records': len(result_df),
            'enp_field_used': enp_field
        }

        return result_df, stats

    except Exception as e:
        return None, f"Ошибка при обработке данных: {str(e)}"


# Layout страницы
appointment_analysis_page = html.Div([
    # Заголовок
    dbc.Row([
        dbc.Col([
            html.H2("Анализ записанных на прием", className="mb-4"),
            html.P("Загрузите файлы с ЕНП (Excel) и обращениями (CSV) для анализа пересечений",
                   className="text-muted mb-4")
        ], width=12)
    ], className="px-3"),

    # Загрузка файлов
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Загрузка файлов"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Файл с ЕНП для поиска записанных на прием (Excel)",
                                       style={"font-weight": "bold"}),
                            dcc.Upload(
                                id=f"upload-enp-{type_page}",
                                children=html.Div([
                                    "Перетащите файл сюда или ",
                                    html.A("выберите файл")
                                ]),
                                style={
                                    "width": "100%",
                                    "height": "60px",
                                    "lineHeight": "60px",
                                    "borderWidth": "1px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px",
                                    "textAlign": "center",
                                    "margin": "10px"
                                },
                                multiple=False,
                                accept=".xlsx,.xls"
                            ),
                            html.Div(id=f"enp-loading-{type_page}", className="mt-2"),
                            html.Div(id=f"enp-file-info-{type_page}", className="mt-2"),
                            html.Div(id=f"enp-field-selector-{type_page}", className="mt-2")
                        ], width=12, md=6, className="mb-3 mb-md-0"),
                        dbc.Col([
                            html.Label("Файл из модуля Обращения Квазар (CSV)", style={"font-weight": "bold"}),
                            dcc.Upload(
                                id=f"upload-requests-{type_page}",
                                children=html.Div([
                                    "Перетащите файл сюда или ",
                                    html.A("выберите файл")
                                ]),
                                style={
                                    "width": "100%",
                                    "height": "60px",
                                    "lineHeight": "60px",
                                    "borderWidth": "1px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px",
                                    "textAlign": "center",
                                    "margin": "10px"
                                },
                                multiple=False,
                                accept=".csv"
                            ),
                            html.Div(id=f"requests-loading-{type_page}", className="mt-2"),
                            html.Div(id=f"requests-file-info-{type_page}", className="mt-2")
                        ], width=12, md=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Анализировать данные",
                                id=f"analyze-button-{type_page}",
                                color="primary",
                                className="mt-3",
                                disabled=True
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=12)
    ], className="mb-4 px-3"),

    # Индикатор загрузки
    dbc.Row([
        dbc.Col([
            html.Div(id=f"loading-indicator-{type_page}")
        ], width=12)
    ], className="mb-3 px-3"),

    # Результаты
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Результаты анализа"),
                dbc.CardBody([
                    html.Div(id=f"analysis-results-{type_page}"),
                    html.Div(id=f"analysis-table-{type_page}")
                ])
            ])
        ], width=12)
    ], className="px-3")
])


# Callback для показа индикатора загрузки при загрузке Excel файла
@app.callback(
    Output(f"enp-loading-{type_page}", "children"),
    Input(f"upload-enp-{type_page}", "contents"),
    prevent_initial_call=True
)
def show_enp_loading(contents):
    if contents is None:
        raise PreventUpdate

    return dbc.Alert([
        dbc.Spinner(
            html.Div([
                html.Strong("📤 Загружаю Excel файл..."),
                html.Br(),
                "Пожалуйста, подождите"
            ])
        )
    ], color="info", className="mb-2")


# Callback для обработки загрузки файла с ЕНП
@app.callback(
    Output(f"enp-loading-{type_page}", "children", allow_duplicate=True),
    Output(f"enp-file-info-{type_page}", "children"),
    Output(f"enp-field-selector-{type_page}", "children"),
    Output(f"analyze-button-{type_page}", "disabled"),
    Input(f"upload-enp-{type_page}", "contents"),
    State(f"upload-enp-{type_page}", "filename"),
    prevent_initial_call=True
)
def handle_enp_upload(contents, filename):
    if contents is None:
        return "", "", "", True

    try:
        # Декодируем файл
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Читаем Excel файл
        df = pd.read_excel(io.BytesIO(decoded))

        info = dbc.Alert([
            html.Strong(f"✅ {filename}"),
            html.Br(),
            f"Загружено записей: {len(df)}",
            html.Br(),
            f"Колонки: {', '.join(df.columns.tolist())}"
        ], color="success", className="mb-0")

        # Создаем селектор полей
        field_options = [{'label': col, 'value': col} for col in df.columns.tolist()]
        field_selector = html.Div([
            html.Label("Выберите поле с ЕНП:", style={"font-weight": "bold", "font-size": "0.9rem"}),
            dcc.Dropdown(
                id=f"enp-field-dropdown-{type_page}",
                options=field_options,
                value=field_options[0]['value'] if field_options else None,
                clearable=False,
                placeholder="Выберите поле...",
                style={"font-size": "0.9rem"}
            )
        ])

        return "", info, field_selector, False

    except Exception as e:
        error = dbc.Alert([
            html.Strong(f"❌ Ошибка загрузки {filename}"),
            html.Br(),
            str(e)
        ], color="danger", className="mb-0")
        return "", error, "", True


# Callback для показа индикатора загрузки при загрузке CSV файла
@app.callback(
    Output(f"requests-loading-{type_page}", "children"),
    Input(f"upload-requests-{type_page}", "contents"),
    prevent_initial_call=True
)
def show_requests_loading(contents):
    if contents is None:
        raise PreventUpdate

    return dbc.Alert([
        dbc.Spinner(
            html.Div([
                html.Strong("📤 Загружаю CSV файл..."),
                html.Br(),
                "Пожалуйста, подождите"
            ])
        )
    ], color="info", className="mb-2")


# Callback для обработки загрузки файла с обращениями
@app.callback(
    Output(f"requests-loading-{type_page}", "children", allow_duplicate=True),
    Output(f"requests-file-info-{type_page}", "children"),
    Output(f"analyze-button-{type_page}", "disabled", allow_duplicate=True),
    Input(f"upload-requests-{type_page}", "contents"),
    State(f"upload-requests-{type_page}", "filename"),
    prevent_initial_call=True
)
def handle_requests_upload(contents, filename):
    if contents is None:
        return "", "", True

    try:
        # Декодируем файл
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Определяем кодировку
        encoding = detect_encoding(decoded)

        # Читаем CSV файл
        df = read_csv_with_encoding(decoded, encoding)

        info = dbc.Alert([
            html.Strong(f"✅ {filename}"),
            html.Br(),
            f"Загружено записей: {len(df)}",
            html.Br(),
            f"Кодировка: {encoding}",
            html.Br(),
            f"Колонки: {', '.join(df.columns.tolist())}"
        ], color="success", className="mb-0")

        return "", info, False

    except Exception as e:
        error = dbc.Alert([
            html.Strong(f"❌ Ошибка загрузки {filename}"),
            html.Br(),
            str(e)
        ], color="danger", className="mb-0")
        return "", error, True


# Callback для показа индикатора загрузки
@app.callback(
    Output(f"loading-indicator-{type_page}", "children"),
    Input(f"analyze-button-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def show_loading_indicator(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    return dbc.Alert([
        dbc.Spinner(
            html.Div([
                html.Strong("🔄 Анализирую данные..."),
                html.Br(),
                "Пожалуйста, подождите, это может занять некоторое время."
            ])
        )
    ], color="info", className="mb-3")


# Callback для анализа данных
@app.callback(
    Output(f"loading-indicator-{type_page}", "children", allow_duplicate=True),
    Output(f"analysis-results-{type_page}", "children"),
    Output(f"analysis-table-{type_page}", "children"),
    Input(f"analyze-button-{type_page}", "n_clicks"),
    State(f"upload-enp-{type_page}", "contents"),
    State(f"upload-requests-{type_page}", "contents"),
    State(f"enp-field-dropdown-{type_page}", "value"),
    prevent_initial_call=True
)
def analyze_data(n_clicks, enp_contents, requests_contents, enp_field):
    if n_clicks is None or enp_contents is None or requests_contents is None:
        raise PreventUpdate

    try:
        # Декодируем файлы
        _, enp_string = enp_contents.split(',')
        enp_decoded = base64.b64decode(enp_string)
        enp_df = pd.read_excel(io.BytesIO(enp_decoded))

        _, requests_string = requests_contents.split(',')
        requests_decoded = base64.b64decode(requests_string)
        encoding = detect_encoding(requests_decoded)
        requests_df = read_csv_with_encoding(requests_decoded, encoding)

        # Обрабатываем данные
        result_df, stats = process_data(enp_df, requests_df, enp_field)

        if result_df is None:
            # Ошибка обработки
            error_alert = dbc.Alert([
                html.Strong("❌ Ошибка анализа"),
                html.Br(),
                stats
            ], color="danger")
            return "", error_alert, ""

        # Статистика
        stats_html = build_stats_card(stats)
        stats_html2 = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Статистика", className="card-title"),
                        html.P([
                            html.Strong("Записей в файле с ЕНП: "), str(stats['total_enp_records']), html.Br(),
                            html.Strong("Записей в файле с обращениями: "), str(stats['total_requests_records']),
                            html.Br(),
                            html.Strong("Поле для поиска ЕНП: "), str(stats.get('enp_field_used', 'ЕНП')), html.Br(),
                            html.Strong("Уникальных ЕНП в файле с ЕНП: "), str(stats['unique_enp_in_file']), html.Br(),
                            html.Strong("Уникальных ЕНП в файле с обращениями: "),
                            str(stats['unique_requests_in_file']), html.Br(),
                            html.Strong("Общих ЕНП: "), str(stats['common_enp']), html.Br(),
                            html.Strong("Записей в результате: "), str(stats['result_records'])
                        ])
                    ])
                ])
            ], width=12)
        ])

        # Таблица с результатами
        table = dash_table.DataTable(
            id=f"results-table-{type_page}",
            data=result_df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in result_df.columns],
            page_size=15,
            sort_action="native",
            filter_action="native",
            style_cell={"textAlign": "left", "minWidth": "120px", "maxWidth": "400px", "whiteSpace": "normal"},
            style_header={"fontWeight": "bold"},
            export_format="xlsx",
            # Настройки для прокрутки внутри контейнера
            style_table={
                "height": "500px",
                "overflowY": "auto",
                "overflowX": "auto",
                "border": "1px solid #dee2e6",
                "borderRadius": "0.375rem"
            },
            fixed_rows={"headers": True},
            virtualization=True
        )

        return "", stats_html, table

    except Exception as e:
        error_alert = dbc.Alert([
            html.Strong("❌ Ошибка анализа"),
            html.Br(),
            str(e)
        ], color="danger")
        return "", error_alert, ""
