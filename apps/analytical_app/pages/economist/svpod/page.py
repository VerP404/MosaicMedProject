from datetime import datetime

from dash import html, dcc, Output, Input, State, ALL, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.svpod.query import sql_query_rep, get_filter_conditions
from apps.analytical_app.query_executor import engine

type_page = "econ-sv-pod"


def get_level_options(parent_id=None):
    """Возвращает список опций для выбора уровня."""
    if parent_id is None:
        query = "SELECT DISTINCT id, name FROM plan_groupindicators WHERE parent_id IS NULL"
    else:
        query = f"SELECT id, name FROM plan_groupindicators WHERE parent_id = {parent_id}"
    levels = pd.read_sql(query, engine)
    return [{'label': level['name'], 'value': level['id']} for _, level in levels.iterrows()]


economist_sv_pod = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row([
                                dbc.Col(update_buttons(type_page), width=2),
                                dbc.Col(filter_years(type_page), width=1),
                                dbc.Col(dbc.Alert(
                                    "Отобраны талоны: без санкций, местные (по полису ОМС), сумма талона не равна 0",
                                    color="primary"), width=4),
                                dbc.Col(
                                    dbc.Alert(
                                        [
                                            html.P("Примененные фильтры:", style={"margin-bottom": "5px"}),
                                            html.Div(id=f"applied-filters-{type_page}", style={"margin-top": "10px"})
                                        ],
                                        color="warning"
                                    ),
                                    width=4
                                ),
                            ]),
                            dbc.Row([
                                html.Div(id='dropdown-container', children=[
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id={'type': 'dynamic-dropdown', 'index': 0},
                                            options=[],
                                            placeholder="Выберите уровень 1",
                                            value=None
                                        ),
                                        width=3
                                    ),
                                ]),
                            ]),
                            dbc.Row([
                                dbc.Col(
                                    dcc.RadioItems(
                                        id=f'mode-toggle-{type_page}',
                                        options=[
                                            {'label': 'Объемы', 'value': 'volumes'},
                                            {'label': 'Финансы', 'value': 'finance'}
                                        ],
                                        value='volumes',  # По умолчанию отображаем объемы
                                        inline=True,
                                        labelStyle={'margin-right': '15px'}
                                    ),
                                    width=4
                                ),
                                dbc.Col(
                                    dcc.Checklist(
                                        id=f'unique-toggle-{type_page}',
                                        options=[{"label": "Уникальные пациенты", "value": "unique"}],
                                        value=[],  # По умолчанию выключено
                                        inline=True,
                                        style={"margin-left": "20px"}
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=f'month-selector-{type_page}',
                                        options=[
                                            {'label': 'Январь', 'value': 1},
                                            {'label': 'Февраль', 'value': 2},
                                            {'label': 'Март', 'value': 3},
                                            {'label': 'Апрель', 'value': 4},
                                            {'label': 'Май', 'value': 5},
                                            {'label': 'Июнь', 'value': 6},
                                            {'label': 'Июль', 'value': 7},
                                            {'label': 'Август', 'value': 8},
                                            {'label': 'Сентябрь', 'value': 9},
                                            {'label': 'Октябрь', 'value': 10},
                                            {'label': 'Ноябрь', 'value': 11},
                                            {'label': 'Декабрь', 'value': 12}
                                        ],
                                        placeholder="Выберите месяц",
                                        value=None
                                    ),
                                    width=2
                                )
                            ], style={'margin-bottom': '10px'})
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "Данные", column_selectable='multi'),
        dcc.Store(id=f'selected-data-{type_page}'),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    Output(f'sum-result-result-table1-{type_page}', 'children'),
    Input(f'sum-button-result-table1-{type_page}', 'n_clicks'),
    State(f'result-table1-{type_page}', 'derived_virtual_data'),
    State(f'result-table1-{type_page}', 'selected_cells'),
    State(f'mode-toggle-{type_page}', 'value')
)
def calculate_sum_and_count(n_clicks, rows, selected_cells, mode):
    if n_clicks is None:
        raise PreventUpdate

    if rows is None or not selected_cells:
        return "Нет данных или не выбраны ячейки для подсчета."

    total_sum = 0
    count = 0
    for cell in selected_cells:
        row_idx = cell['row']
        col_id = cell['column_id']
        value = rows[row_idx].get(col_id, 0)
        if isinstance(value, (int, float)):
            total_sum += value
            count += 1

    if mode == 'finance':
        total_sum = f"{total_sum:,.2f}".replace(",", " ")
    else:
        total_sum = f"{int(total_sum):,}".replace(",", " ")
    return f"Количество: {count}, Сумма: {total_sum}"


@app.callback(
    Output('dropdown-container', 'children'),
    Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
)
def display_dynamic_dropdowns(values):
    dropdowns = []
    level = 0
    options = get_level_options()
    value = values[0] if values else None

    dropdown = dbc.Col(
        dcc.Dropdown(
            id={'type': 'dynamic-dropdown', 'index': level},
            options=options,
            placeholder="Выберите уровень 1",
            value=value
        ),
        width=3
    )
    dropdowns.append(dropdown)

    while True:
        if value is None:
            break
        options = get_level_options(value)
        if not options:
            break
        level += 1
        value = values[level] if len(values) > level else None
        dropdown = dbc.Col(
            dcc.Dropdown(
                id={'type': 'dynamic-dropdown', 'index': level},
                options=options,
                placeholder=f"Выберите уровень {level + 1}",
                value=value
            ),
            width=3
        )
        dropdowns.append(dropdown)

    return dropdowns


def fetch_plan_data(selected_level, year, mode='volumes'):
    """Получение плановых данных (помесячно) из БД."""
    plan_field = "quantity" if mode == 'volumes' else "amount"
    query = text(f"""
        SELECT mp.month, SUM(mp.{plan_field}) AS plan
        FROM plan_monthlyplan AS mp
        INNER JOIN plan_annualplan AS ap ON mp.annual_plan_id = ap.id
        WHERE ap.group_id = :selected_level AND ap.year = :year
        GROUP BY mp.month
        ORDER BY mp.month
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"selected_level": selected_level, "year": year}).mappings()
        plan_data = {row["month"]: row["plan"] for row in result}
    return plan_data


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'applied-filters-{type_page}', 'children'),
     ],
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'mode-toggle-{type_page}', 'value'),
    State(f'unique-toggle-{type_page}', 'value'),
    State(f'dropdown-year-{type_page}', 'value'),
    State({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
    State(f'month-selector-{type_page}', 'value')
)
def update_table_with_plan_and_balance(n_clicks,
                                       mode,
                                       unique_flag,
                                       selected_year,
                                       selected_levels,
                                       selected_month):
    if n_clicks is None:
        raise PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    selected_levels = [lvl for lvl in selected_levels if lvl is not None]
    if not selected_levels:
        raise PreventUpdate

    selected_level = selected_levels[-1]
    filter_conditions = get_filter_conditions([selected_level], selected_year)

    unique = "unique" in unique_flag

    # Загружаем фактические данные
    fact_columns, fact_data_list = TableUpdater.query_to_df(
        engine,
        sql_query_rep(selected_year,
                      group_id=[selected_level],
                      filter_conditions=filter_conditions,
                      mode=mode,
                      unique_flag=unique)
    )
    # Добавляем общую сумму "исправлено"
    total_ispravleno_all_months = sum(row.get("исправлено", 0) or 0 for row in fact_data_list)
    # Превращаем список словарей fact_data_list в dict по ключу "month" (можно и так).
    # Будем потом "сливать" с заготовкой всех месяцев.
    fact_dict = {}
    for row in fact_data_list:
        m = row["month"]
        fact_dict[m] = row

    # Загружаем плановые данные
    plan_data = fetch_plan_data(selected_level, selected_year, mode)

    today = datetime.today()
    default_month = today.month
    current_day = today.day
    # Если пользователь выбрал месяц вручную, берём его, иначе - текущий
    current_month = selected_month if selected_month is not None else default_month

    # Формируем список месяцев для отображения: от 1 до current_month
    months_to_show = list(range(1, current_month + 1))

    # Создаём «заготовку» для итоговой таблицы.
    # Для каждого месяца делаем словарь со всеми нужными полями, заполненными нулями.
    # Потом при наличии данных - перезапишем.
    fact_data = []
    for m in months_to_show:
        # Базовая заготовка на случай, если нет данных вообще
        row_template = {
            "month": m,
            "План 1/12": 0,
            "Входящий остаток": 0,
            "План": 0,
            "Факт": 0,
            "%": 0,
            "Остаток": 0,
            "новые": 0,
            "в_тфомс": 0,
            "оплачено": 0,
            "исправлено": 0,
            "отказано": 0,
            "отменено": 0,
        }

        # Если в fact_dict есть запись для этого месяца, берём данные
        if m in fact_dict:
            source = fact_dict[m]
            # mode='finance' -> суммы, mode='volumes' -> кол-во
            row_template["новые"] = source.get("новые", 0) or 0
            row_template["в_тфомс"] = source.get("в_тфомс", 0) or 0
            row_template["оплачено"] = source.get("оплачено", 0) or 0
            row_template["исправлено"] = source.get("исправлено", 0) or 0
            row_template["отказано"] = source.get("отказано", 0) or 0
            row_template["отменено"] = source.get("отменено", 0) or 0

        # Подставляем план, если он есть
        row_template["План 1/12"] = plan_data.get(m, 0)

        fact_data.append(row_template)

    # Теперь пробегаемся по fact_data и рассчитываем Факт, Остаток, % и т.д.
    incoming_balance = 0
    for row in fact_data:
        m = row["month"]
        row["Входящий остаток"] = incoming_balance
        row["План"] = (row["План 1/12"] or 0) + (row["Входящий остаток"] or 0)

        # Расчёт «Факт» по текущему дню.
        manually_selected = selected_month is not None and m == selected_month

        # Расчёт «Факт» по текущему дню.
        if manually_selected:
            # Если пользователь выбрал месяц, то как раньше — только оплаченные
            row["Факт"] = row.get("оплачено", 0)
        else:
            if m < current_month - 1:
                row["Факт"] = row.get("оплачено", 0)
            elif m == current_month - 1:
                if current_day <= 10:
                    # Используем total_ispravleno_all_months вместо row["исправлено"]
                    row["Факт"] = (
                            row.get("новые", 0) +
                            row.get("в_тфомс", 0) +
                            row.get("оплачено", 0) +
                            total_ispravleno_all_months
                    )
                else:
                    row["Факт"] = row.get("оплачено", 0)
            elif m == current_month:
                # Для текущего месяца тоже используем total_ispravleno_all_months
                row["Факт"] = (
                        row.get("новые", 0) +
                        row.get("в_тфомс", 0) +
                        row.get("оплачено", 0) +
                        total_ispravleno_all_months
                )
            else:
                row["Факт"] = 0

        if row["План"] > 0:
            row["%"] = round(row["Факт"] / row["План"] * 100, 1)
        else:
            row["%"] = 0

        row["Остаток"] = (row["План"] or 0) - (row["Факт"] or 0)
        incoming_balance = row["Остаток"]

    # Добавим строку «Нарастающе»
    if fact_data:
        total_plan_12 = sum(r["План 1/12"] for r in fact_data)
        total_fact = sum(r["Факт"] for r in fact_data)
        total_new = sum(r["новые"] for r in fact_data)
        total_tfoms = sum(r["в_тфомс"] for r in fact_data)
        total_oplacheno = sum(r["оплачено"] for r in fact_data)
        total_ispravleno = sum(r["исправлено"] for r in fact_data)
        total_otkazano = sum(r["отказано"] for r in fact_data)
        total_otmeneno = sum(r["отменено"] for r in fact_data)
        cumulative_row = {
            "month": "Нарастающе",
            "План 1/12": 0,
            "Входящий остаток": 0,
            "План": total_plan_12,
            "Факт": total_fact,
            "Остаток": fact_data[-1]["Остаток"],
            "%": round(total_fact / total_plan_12 * 100, 1) if total_plan_12 > 0 else 0,
            "новые": total_new,
            "в_тфомс": total_tfoms,
            "оплачено": total_oplacheno,
            "исправлено": total_ispravleno,
            "отказано": total_otkazano,
            "отменено": total_otmeneno,
        }
        fact_data.append(cumulative_row)

    # Добавим строку «Год» (1..12)
    year_plan = sum(plan_data.get(m, 0) for m in range(1, 13))
    if fact_data:
        total_fact_overall = sum(r["Факт"] for r in fact_data if isinstance(r["month"], int))
        year_row = {
            "month": "Год",
            "План 1/12": 0,
            "Входящий остаток": 0,
            "План": year_plan,
            "Факт": total_fact_overall,
            "Остаток": year_plan - total_fact_overall,
            "%": round(total_fact_overall / year_plan * 100, 1) if year_plan else 0,
            "новые": sum(r["новые"] for r in fact_data if isinstance(r["month"], int)),
            "в_тфомс": sum(r["в_тфомс"] for r in fact_data if isinstance(r["month"], int)),
            "оплачено": sum(r["оплачено"] for r in fact_data if isinstance(r["month"], int)),
            "исправлено": sum(r["исправлено"] for r in fact_data if isinstance(r["month"], int)),
            "отказано": sum(r["отказано"] for r in fact_data if isinstance(r["month"], int)),
            "отменено": sum(r["отменено"] for r in fact_data if isinstance(r["month"], int)),
        }
        fact_data.append(year_row)

    columns = [
        {"name": ["", "Месяц"], "id": "month"},
        {"name": ["Итог", "План"], "id": "План"},
        {"name": ["Итог", "Факт"], "id": "Факт"},
        {"name": ["Итог", "%"], "id": "%"},
        {"name": ["Итог", "Остаток"], "id": "Остаток"},
        {"name": ["Факт", "Новые"], "id": "новые"},
        {"name": ["Факт", "В ТФОМС"], "id": "в_тфомс"},
        {"name": ["Факт", "Оплачено"], "id": "оплачено"},
        {"name": ["Факт", "Исправлено"], "id": "исправлено"},
        {"name": ["Факт", "Отказано"], "id": "отказано"},
        {"name": ["Факт", "Отменено"], "id": "отменено"},
        {"name": ["План 1/12", "План 1/12"], "id": "План 1/12"},
        {"name": ["План 1/12", "Входящий остаток"], "id": "Входящий остаток"},
    ]

    return columns, fact_data, loading_output, filter_conditions
