from datetime import datetime, timedelta
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text
from apps.analytical_app.app import app
from apps.analytical_app.callback import get_selected_dates, TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.statistic.eln.query import (
    sql_eln,
    sql_query_eln_doctors,
    sql_query_eln_patients,
    sql_eln_yearly,
    sql_eln_monthly,
)
from apps.analytical_app.query_executor import engine

type_page = "eln"

# --- 1) Загружаем из БД списки уникальных значений для ТВСП, Статуса и Причины --- #
with engine.connect() as conn:
    tvsp_rows = conn.execute(text("SELECT DISTINCT tvsp FROM load_data_sick_leave_sheets ORDER BY tvsp")).fetchall()
    status_rows = conn.execute(text("SELECT DISTINCT status FROM load_data_sick_leave_sheets ORDER BY status")).fetchall()
    reason_rows = conn.execute(text("""
        SELECT DISTINCT coalesce(incapacity_reason_code, '') as reason
        FROM load_data_sick_leave_sheets
        ORDER BY reason
    """)).fetchall()

# --- 2) Формируем опции для ТВСП, Статуса, Причины --- #
tvsp_options = [{"label": row[0], "value": row[0]} for row in tvsp_rows if row[0]]
tvsp_options.insert(0, {"label": "Все", "value": "all"})

status_options = [{"label": row[0], "value": row[0]} for row in status_rows if row[0]]
status_options.insert(0, {"label": "Все", "value": "all"})

# Для причины, если пустая строка => 'По уходу'
reason_options = []
for row in reason_rows:
    val = row[0] if row[0] else "По уходу"
    reason_options.append({"label": val, "value": val})
reason_options.insert(0, {"label": "Все", "value": "all"})

# Опции для "Первичный" – заменяем чекбоксы на RadioItems (три варианта: Все/Да/Нет)
first_options = [
    {"label": "Все", "value": "all"},
    {"label": "Да", "value": "да"},
    {"label": "Нет", "value": "нет"},
]

# --- 3) Layout --- #
eln_layout = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(html.H5("Фильтры", className="mb-0"), width="auto"),
                            dbc.Col(
                                html.Div(
                                    id=f"last-updated-{type_page}",
                                    style={"textAlign": "right", "fontWeight": "normal"}
                                ),
                                width=True
                            )
                        ],
                        align="center",
                        justify="between"
                    )
                ),
                dbc.CardBody(
                    [
                        # Одна строка, в которой ТРИ подкарточки: Период | Первичный/Статус/Причина | ТВСП
                        dbc.Row(
                            [
                                # Подкарточка 1: Период
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Период"),
                                            dbc.CardBody(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Дата начала:", className="mb-0"),
                                                                    dcc.DatePickerSingle(
                                                                        id=f"date-picker-start-{type_page}",
                                                                        first_day_of_week=1,
                                                                        date=datetime.now().date() - timedelta(days=1),
                                                                        display_format="DD.MM.YYYY",
                                                                        className="mt-1"
                                                                    )
                                                                ],
                                                                width=12
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
                                                                width=12
                                                            ),
                                                        ],
                                                        className="mb-2"
                                                    ),
                                                    dbc.Row(
                                                        dbc.Col(
                                                            [
                                                                dbc.Label("Выбранный период:", className="mb-0"),
                                                                html.Div(
                                                                    id=f"selected-date-{type_page}",
                                                                    className="mt-1 text-muted"
                                                                )
                                                            ],
                                                            width=12
                                                        ),
                                                        className="mb-2"
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="mb-3"
                                    ),
                                    width=3
                                ),

                                # Подкарточка 2: Первичный / Статус / Причина
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("Первичный / Статус / Причина"),
                                            dbc.CardBody(
                                                [
                                                    # Первая строка: Первичный (слева) и Статус (справа)
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Первичный:", className="mb-0"),
                                                                    dbc.RadioItems(
                                                                        id=f"radio-first-{type_page}",
                                                                        options=first_options,
                                                                        value="да",
                                                                        inline=True,
                                                                        className="mt-1"
                                                                    )
                                                                ],
                                                                width=3
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Статус:", className="mb-0"),
                                                                    dcc.Dropdown(
                                                                        id=f"dropdown-status-{type_page}",
                                                                        options=status_options,
                                                                        multi=True,
                                                                        placeholder="Выберите статус...",
                                                                        className="mt-1"
                                                                    )
                                                                ],
                                                                width=9
                                                            ),
                                                        ],
                                                        className="mb-3"
                                                    ),
                                                    # Вторая строка: Код причины (на всю ширину)
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Код причины:", className="mb-0"),
                                                                    dcc.Dropdown(
                                                                        id=f"dropdown-reason-{type_page}",
                                                                        options=reason_options,
                                                                        multi=True,
                                                                        placeholder="Выберите причину...",
                                                                        className="mt-1"
                                                                    )
                                                                ],
                                                                width=12
                                                            ),
                                                        ],
                                                        className="mb-2"
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="mb-3"
                                    ),
                                    width=4
                                ),

                                # Подкарточка 3: ТВСП
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("ТВСП"),
                                            dbc.CardBody(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("ТВСП:", className="mb-0"),
                                                                    dcc.Dropdown(
                                                                        id=f"dropdown-tvsp-{type_page}",
                                                                        options=tvsp_options,
                                                                        multi=True,
                                                                        placeholder="Выберите ТВСП...",
                                                                        className="mt-1"
                                                                    )
                                                                ],
                                                                width=12
                                                            ),
                                                        ],
                                                        className="mb-2"
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="mb-3"
                                    ),
                                    width=5
                                ),
                            ]
                        )
                    ]
                ),
            ],
            className="mb-3"
        ),

        # Вкладки с отчётами
        dbc.Tabs(
            [
                dbc.Tab(
                    card_table(f"result-table-{type_page}", "Отчет по листам нетрудоспособности", 15),
                    label="Отчет по статусам"
                ),
                dbc.Tab(
                    card_table(f"result-table1-{type_page}", "По врачам", 15),
                    label="По врачам"
                ),
                dbc.Tab(
                    card_table(f"result-table2-{type_page}", "По пациентам", 15),
                    label="По пациентам"
                ),
                dbc.Tab(
                    html.Div([
                        card_table(f"result-table3-{type_page}", "Годовой анализ первичных больничных", 15),
                        html.Br(),
                        card_table(f"result-table4-{type_page}", "Помесячный анализ первичных больничных", 15)
                    ]),
                    label="Анализ по периодам"
                ),
            ]
        ),
    ],
    style={"padding": "15px"}  # Отступ вокруг всей страницы
)

# --- 4) Callback для обновления даты окончания (если нужно) --- #
@app.callback(
    Output(f"date-picker-end-{type_page}", "date"),
    Input(f"interval-component-{type_page}", "n_intervals")
)
def update_date_picker(n_intervals):
    return datetime.now().date() - timedelta(days=7)

# --- 5) Отображаем выбранные даты --- #
@app.callback(
    Output(f"selected-date-{type_page}", "children"),
    Input(f"date-picker-start-{type_page}", "date"),
    Input(f"date-picker-end-{type_page}", "date")
)
def update_selected_dates(start_date, end_date):
    return get_selected_dates(start_date, end_date)

# --- 6) Вспомогательные коллбеки для взаимоисключающего выбора "Все" в Dropdown --- #
def enforce_all_option(selected_values):
    """Если выбрано 'Все' и что-то ещё, оставляем только 'Все'. Если выбраны другие значения, убираем 'Все'."""
    if not selected_values:
        return []
    if "all" in selected_values and len(selected_values) > 1:
        return ["all"]
    return selected_values

@app.callback(
    Output(f"dropdown-tvsp-{type_page}", "value"),
    Input(f"dropdown-tvsp-{type_page}", "value"),
    prevent_initial_call=True
)
def enforce_mutually_exclusive_tvsp(selected_values):
    return enforce_all_option(selected_values)

@app.callback(
    Output(f"dropdown-status-{type_page}", "value"),
    Input(f"dropdown-status-{type_page}", "value"),
    prevent_initial_call=True
)
def enforce_mutually_exclusive_status(selected_values):
    return enforce_all_option(selected_values)

@app.callback(
    Output(f"dropdown-reason-{type_page}", "value"),
    Input(f"dropdown-reason-{type_page}", "value"),
    prevent_initial_call=True
)
def enforce_mutually_exclusive_reason(selected_values):
    return enforce_all_option(selected_values)

# --- 7) Основной callback для обновления таблиц --- #
@app.callback(
    [
        Output(f"result-table-{type_page}", "columns"),
        Output(f"result-table-{type_page}", "data"),
        Output(f"result-table1-{type_page}", "columns"),
        Output(f"result-table1-{type_page}", "data"),
        Output(f"result-table2-{type_page}", "columns"),
        Output(f"result-table2-{type_page}", "data"),
        Output(f"result-table3-{type_page}", "columns"),
        Output(f"result-table3-{type_page}", "data"),
        Output(f"result-table4-{type_page}", "columns"),
        Output(f"result-table4-{type_page}", "data"),
        Output(f"last-updated-{type_page}", "children"),  # Вывод даты обновления
    ],
    [
        Input(f"date-picker-start-{type_page}", "date"),
        Input(f"date-picker-end-{type_page}", "date"),
        Input(f"dropdown-tvsp-{type_page}", "value"),
        Input(f"dropdown-status-{type_page}", "value"),
        Input(f"radio-first-{type_page}", "value"),
        Input(f"dropdown-reason-{type_page}", "value"),
    ]
)
def update_tables(start_date, end_date, tvsp_values, status_values, first_value, reason_values):
    if (start_date is None) or (end_date is None):
        return [], [], [], [], [], [], [], [], [], [], ""

    # Логика фильтров (без изменений)
    if first_value == "all":
        first_filter = []
        first_all = True
    else:
        first_filter = [first_value]
        first_all = False

    if not tvsp_values or "all" in tvsp_values:
        tvsp_filter = []
        tvsp_all = True
    else:
        tvsp_filter = tvsp_values
        tvsp_all = False

    if not status_values or "all" in status_values:
        status_filter = []
        status_all = True
    else:
        status_filter = status_values
        status_all = False

    if not reason_values or "all" in reason_values:
        reason_filter = []
        reason_all = True
    else:
        reason_filter = reason_values
        reason_all = False

    bind_params_eln = {
        'start_date': start_date,
        'end_date': end_date,
        'tvsp': tvsp_filter,
        'tvsp_all': tvsp_all,
        'first_list': first_filter,
        'first_all': first_all,
        'reason_list': reason_filter,
        'reason_all': reason_all
    }
    bind_params_others = {
        'start_date': start_date,
        'end_date': end_date,
        'tvsp': tvsp_filter,
        'tvsp_all': tvsp_all,
        'status_list': status_filter,
        'status_all': status_all,
        'first_list': first_filter,
        'first_all': first_all,
        'reason_list': reason_filter,
        'reason_all': reason_all
    }

    # Выполняем запросы для первых 3 вкладок
    columns, data = TableUpdater.query_to_df(engine, sql_eln, bind_params_eln)
    columns1, data1 = TableUpdater.query_to_df(engine, sql_query_eln_doctors, bind_params_others)
    columns2, data2 = TableUpdater.query_to_df(engine, sql_query_eln_patients, bind_params_others)

    # --- Получаем MAX(updated_at) из базы --- #
    with engine.connect() as conn:
        row = conn.execute(text("SELECT MAX(updated_at) FROM load_data_sick_leave_sheets")).fetchone()

    if row and row[0]:
        last_updated_str = row[0].strftime("Обновлено: %d.%m.%Y %H:%M")
    else:
        last_updated_str = "Обновлено: Нет данных"

    # --- Анализ первичных больничных через SQL (агрегация на стороне БД) --- #
    aggr_params = {
        'start_date': start_date,
        'end_date': end_date,
        'tvsp': tvsp_filter,
        'tvsp_all': tvsp_all,
        'first_list': first_filter if first_filter else ['да'],  # по умолчанию первичные
        'first_all': first_all,
        'reason_list': reason_filter,
        'reason_all': reason_all
    }
    yearly_columns, yearly_data = TableUpdater.query_to_df(engine, sql_eln_yearly, aggr_params)
    monthly_columns, monthly_data = TableUpdater.query_to_df(engine, sql_eln_monthly, aggr_params)

    return (columns, data,
            columns1, data1,
            columns2, data2,
            yearly_columns, yearly_data,
            monthly_columns, monthly_data,
            last_updated_str)
