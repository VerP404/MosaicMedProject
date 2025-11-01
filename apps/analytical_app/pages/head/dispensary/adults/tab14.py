import base64
import io
import traceback
from dash import html, dcc, dash_table, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.pages.head.dispensary.adults.query import sql_query_dispensary_organized_collectives

type_page = "tab14-da"


def parse_xls_contents(contents, filename):
    """Парсинг xls файла: читает заголовки из строки 6 (индекс 5), фильтрует по столбцу G (Иная МО = да), возвращает список талонов из столбца A"""
    if not contents:
        return []
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        # Пробуем разные движки для чтения Excel (.xls файлы требуют xlrd)
        df = None
        error_messages = []
        
        # Сначала пробуем xlrd для старых .xls файлов
        try:
            df = pd.read_excel(io.BytesIO(decoded), header=None, engine='xlrd')
        except Exception as e:
            error_messages.append(f"xlrd: {str(e)}")
            # Пробуем openpyxl для новых .xlsx файлов
            try:
                df = pd.read_excel(io.BytesIO(decoded), header=None, engine='openpyxl')
            except Exception as e2:
                error_messages.append(f"openpyxl: {str(e2)}")
                # Последняя попытка - без указания движка
                try:
                    df = pd.read_excel(io.BytesIO(decoded), header=None)
                except Exception as e3:
                    error_messages.append(f"default: {str(e3)}")
                    raise Exception(f"Не удалось прочитать файл. Ошибки: {'; '.join(error_messages)}")
        
        if df is None or df.empty:
            raise Exception("Файл пуст или не может быть прочитан")
        
        # Проверяем, что файл содержит минимум 6 строк
        if len(df) < 6:
            return []
        
        # Пробуем найти строку с заголовками (ищем строку, содержащую "Номер талона" или похожие заголовки)
        header_row_idx = None
        for idx in range(min(10, len(df))):
            row_str = ' '.join([str(x).lower() for x in df.iloc[idx].values if pd.notna(x)])
            if 'номер' in row_str and ('талон' in row_str or 'талона' in row_str):
                header_row_idx = idx
                break
        
        # Если не нашли заголовки, используем строку 6 (индекс 5) как указано в требованиях
        if header_row_idx is None:
            header_row_idx = 5
        
        # Пропускаем строки до заголовков включительно, данные начинаются со следующей строки
        df_data = df.iloc[header_row_idx + 1:].copy()
        
        # Проверяем наличие нужных столбцов (минимум 7 столбцов, так как G - это 7-й столбец, индекс 6)
        if df_data.shape[1] < 7:
            return []
        
        # Извлекаем столбцы: A (0) - талон, G (6) - Иная МО
        talon_column = df_data.iloc[:, 0]  # Столбец A
        inaya_mo_column = df_data.iloc[:, 6]  # Столбец G
        
        # Создаем DataFrame для фильтрации
        filtered_df = pd.DataFrame({
            'talon': talon_column,
            'inaya_mo': inaya_mo_column
        })
        
        # Убираем полностью пустые строки по талону
        filtered_df = filtered_df[filtered_df['talon'].notna()]
        filtered_df = filtered_df[filtered_df['talon'].astype(str).str.strip() != '']
        
        if len(filtered_df) == 0:
            return []
        
        # Фильтруем: Иная МО = да (с учетом разных вариантов написания)
        filtered_df['inaya_mo'] = filtered_df['inaya_mo'].fillna('').astype(str).str.strip().str.lower()
        yes_values = ['да', 'yes', '1', 'true', 'д', 'дa', 'дa', '+', 'y', 'есть', 'е']
        
        # Пробуем разные варианты значения "да" и также проверяем частичные совпадения
        mask = filtered_df['inaya_mo'].isin(yes_values)
        
        # Если точных совпадений нет, проверяем, содержит ли значение "да"
        if not mask.any():
            mask = filtered_df['inaya_mo'].str.contains('да|yes|д', case=False, na=False, regex=True)
        
        filtered_df_filtered = filtered_df[mask]
        
        if len(filtered_df_filtered) == 0:
            return []
        
        filtered_df = filtered_df_filtered
        
        # Получаем список талонов, убираем пустые значения и конвертируем в строки
        talons = filtered_df['talon'].astype(str).str.strip()
        talons = talons[talons != ''].tolist()
        
        # Убираем дубликаты
        talons = list(set(talons))
        
        return talons
        
    except Exception as e:
        return []


adults_dv14 = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.CardHeader("Диспансеризация в организованных коллективах"),
            html.Div([
                html.H6("Инструкция по загрузке данных:", className="mt-3 mb-2"),
                html.P([
                    "1. Загрузите данные из Web ОМС: ",
                    html.Strong("Раздел Статистика → Модуль Выгрузка отчетов"),
                    html.Br(),
                    "2. Параметры выгрузки:",
                    html.Ul([
                        html.Li("Уровень отчета: Отчеты для внутреннего пользования"),
                        html.Li("Тип отчета: Диспансеризация Место прохождения"),
                        html.Li("Период окончания лечения: с 1 января текущего года по последнее число отчетного месяца")
                    ]),
                    "3. Загрузите полученный файл .xls в форму ниже"
                ], className="mb-3"),
            ]),
            html.Div([
                html.Table(
                    style={"width": "100%", "tableLayout": "fixed"},
                    children=[
                        html.Tr([
                            html.Td(
                                dcc.Upload(
                                    id=f"upload-xls-{type_page}",
                                    children=dbc.Button("Выбрать файл XLS", size="sm", className="w-100"),
                                    multiple=False,
                                    style={"display": "block"}
                                ),
                                style={"width": "25%", "padding": "4px"}
                            ),
                            html.Td(
                                html.Div(id=f"output-xls-filename-{type_page}"),
                                style={"width": "75%", "padding": "4px"}
                            ),
                        ]),
                    ]
                ),
                dbc.Button(
                    "Сформировать отчет",
                    id=f"generate-report-button-{type_page}",
                    color="primary",
                    className="mt-3"
                ),
                html.Div(id=f"report-status-{type_page}", className="mt-2"),
            ]),
        ]),
        className="mb-3"
    ),
    html.Div(id=f"report-table-container-{type_page}")
])


@app.callback(
    Output(f"output-xls-filename-{type_page}", "children"),
    Input(f"upload-xls-{type_page}", "filename")
)
def update_xls_filename(filename):
    return html.Div(f"Загружен файл: {filename}") if filename else ""


@app.callback(
    [
        Output(f"report-table-container-{type_page}", "children"),
        Output(f"report-status-{type_page}", "children")
    ],
    Input(f"generate-report-button-{type_page}", "n_clicks"),
    State(f"upload-xls-{type_page}", "contents"),
    State(f"upload-xls-{type_page}", "filename")
)
def generate_report(n_clicks, contents, filename):
    if not n_clicks:
        return [], ""
    
    if not contents or not filename:
        return [], dbc.Alert("Пожалуйста, загрузите файл перед формированием отчета", color="warning")
    
    try:
        # Парсим файл и получаем список талонов
        talons = parse_xls_contents(contents, filename)
        
        if not talons:
            # Собираем детальную информацию об ошибке
            error_details = f"Не удалось найти талоны в файле. Проверьте консоль браузера (F12) для подробной диагностики."
            return [], dbc.Alert([
                "Не удалось найти талоны в файле или файл пуст. ",
                html.Br(),
                "Убедитесь, что:",
                html.Ul([
                    html.Li("Файл содержит данные с заголовками в строке 6 (или раньше)"),
                    html.Li("В столбце A находятся номера талонов"),
                    html.Li("В столбце G указано 'да' (или 'ДА', 'Да', '+', '1') для строк с иной МО"),
                    html.Li("Файл имеет формат .xls или .xlsx"),
                    html.Li("Файл не пустой и содержит данные")
                ]),
                html.Br(),
                html.Strong("Откройте консоль браузера (F12 → Console) для подробной диагностики."),
                html.Br(),
                "Там будут указаны: номер строки заголовков, количество найденных строк, примеры значений в столбце G."
            ], color="warning")
        
        # Формируем 3 SQL запроса для разных таблиц
        query_40_65 = sql_query_dispensary_organized_collectives(talons, age_group='40-65')
        query_prochie = sql_query_dispensary_organized_collectives(talons, age_group='прочие')
        query_total = sql_query_dispensary_organized_collectives(talons, age_group=None)
        
        # Выполняем запросы
        try:
            columns_40_65, data_40_65 = TableUpdater.query_to_df(engine, query_40_65)
        except Exception:
            columns_40_65, data_40_65 = [], []
        
        try:
            columns_prochie, data_prochie = TableUpdater.query_to_df(engine, query_prochie)
        except Exception:
            columns_prochie, data_prochie = [], []
        
        try:
            columns_total, data_total = TableUpdater.query_to_df(engine, query_total)
        except Exception:
            columns_total, data_total = [], []
        
        # Таблица 1: 40-65
        table_40_65 = dash_table.DataTable(
            data=data_40_65 if data_40_65 else [],
            columns=columns_40_65 if columns_40_65 else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            export_format='xlsx',
            page_size=50,
            sort_action='native'
        )
        
        # Таблица 2: Прочие
        table_prochie = dash_table.DataTable(
            data=data_prochie if data_prochie else [],
            columns=columns_prochie if columns_prochie else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            export_format='xlsx',
            page_size=50,
            sort_action='native'
        )
        
        # Таблица 3: Общий итог
        table_total = dash_table.DataTable(
            data=data_total if data_total else [],
            columns=columns_total if columns_total else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            export_format='xlsx',
            page_size=50,
            sort_action='native'
        )
        
        # Собираем информацию о результатах
        count_40_65 = len(data_40_65) if data_40_65 else 0
        count_prochie = len(data_prochie) if data_prochie else 0
        count_total = len(data_total) if data_total else 0
        
        if count_40_65 == 0 and count_prochie == 0 and count_total == 0:
            status_message = dbc.Alert([
                f"Загружено талонов: {len(talons)}",
                html.Br(),
                "Не найдено данных в базе по указанным талонам. ",
                "Проверьте, что талоны существуют в таблице load_data_oms_data ",
                "и имеют корректные даты рождения и окончания лечения."
            ], color="warning")
        else:
            status_message = dbc.Alert(
                f"Отчет успешно сформирован. Обработано талонов: {len(talons)} | "
                f"40-65: {count_40_65} строк | Прочие: {count_prochie} строк | "
                f"Общий итог: {count_total} строк",
                color="success"
            )
        
        return [
            dbc.Card(
                dbc.CardBody([
                    dbc.CardHeader("40-65"),
                    table_40_65
                ]),
                className="mb-3"
            ),
            dbc.Card(
                dbc.CardBody([
                    dbc.CardHeader("Прочие"),
                    table_prochie
                ]),
                className="mb-3"
            ),
            dbc.Card(
                dbc.CardBody([
                    dbc.CardHeader("Общий итог"),
                    table_total
                ]),
                className="mb-3"
            )
        ], status_message
        
    except Exception as e:
        error_message = f"Ошибка при формировании отчета: {str(e)}"
        return [], dbc.Alert(error_message, color="danger")

