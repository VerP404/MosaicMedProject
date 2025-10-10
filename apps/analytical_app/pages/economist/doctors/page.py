# File: apps/analytical_app/pages/economist/doctors/econ_doctors_talon_list.py

import json
from datetime import datetime
from dash import html, dcc, Input, Output, State, exceptions, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_years, filter_inogorod, filter_sanction, filter_amount_null,
    filter_status, status_groups, filter_report_type, filter_months,
    date_picker, update_buttons
)
from apps.analytical_app.pages.economist.doctors.query import sql_query_doctors_goal_stat
from apps.analytical_app.query_executor import engine

type_page = "econ-doctors-talon-list"


# Вспомогательная функция сортировки
def sort_key(x):
    return (0, int(x)) if x.isdigit() else (1, x.lower())


# Функция для загрузки списка конфигураций из БД
def load_configs():
    return pd.read_sql(
        text("""
            SELECT id, name, groups::text AS groups_json, created_at
            FROM plan_goalgroupconfig
            ORDER BY created_at DESC
        """),
        engine
    )


# Глобальный словарь групп целей (будет обновляться в колбэке)
GOAL_GROUPS = {}


# --- Layout как функция, чтобы при каждом заходе подтягивались свежие настройки ---
def economist_doctors_talon_list_def():
    # Загружаем конфигурации
    df_configs = load_configs()
    config_options = [
        {
            "label": f"{row['name']} ({row['created_at'].strftime('%Y-%m-%d')})",
            "value": row["id"]
        }
        for _, row in df_configs.iterrows()
    ]
    # По умолчанию не выбираем конфигурацию — пользователь может работать без неё
    default_config = None

    return html.Div([

        # Выбор конфигурации
        dbc.Row([
            dbc.Col([
                html.Label("Конфигурация групп целей:", className="me-2"),
                html.Div([
                    dcc.Dropdown(
                        id=f"dropdown-config-{type_page}",
                        options=config_options,
                        value=default_config,
                        placeholder="Выберите конфигурацию (необязательно)",
                        clearable=True,
                        style={"width": "360px", "flex": "0 0 auto"}
                    ),
                    dbc.Button(
                        "Показать все группы и цели",
                        id=f"open-offcanvas-{type_page}",
                        color="secondary",
                        n_clicks=0,
                        className="ms-2",
                        style={"flex": "0 0 auto"}
                    ),
                ],
                    style={"display": "flex", "alignItems": "center"})
            ]),
        ], className="mb-3"),
        dbc.Offcanvas(
            children=[
                html.Div(id=f"offcanvas-body-{type_page}"),
                dbc.Button(
                    "Закрыть",
                    id=f"close-offcanvas-{type_page}",
                    color="outline-secondary",
                    n_clicks=0,
                    className="mt-4"
                ),
            ],
            id=f"offcanvas-goals-{type_page}",
            title="Группы и их цели",
            is_open=False,
            scrollable=True,
            backdrop=True,
            placement="end",
            className="shadow",
            style={"maxWidth": "520px"},
        ),
        # Фильтры
        dbc.Card(
            dbc.CardBody([

                dbc.CardHeader("Фильтры"),

                # Первая строка: спиннер+кнопка, год и т.п.
                dbc.Row([
                    dbc.Col(
                        dcc.Loading(
                            id=f'loading-button-{type_page}',
                            type="circle",
                            children=html.Div(update_buttons(type_page))
                        ), width=1
                    ),
                    dbc.Col(filter_years(type_page), width=1),
                    dbc.Col(filter_report_type(type_page), width=2),
                    dbc.Col(filter_inogorod(type_page), width=2),
                    dbc.Col(filter_sanction(type_page), width=2),
                    dbc.Col(filter_amount_null(type_page), width=2),
                ], align="center", className="mb-3"),

                # Вторая строка: период и цели / статусы
                dbc.Row([

                    # Левый столбец: период + выбор целей
                    dbc.Col([

                        html.Div(filter_months(type_page),
                                 id=f'col-months-{type_page}', style={'width': '100%'}),
                        html.Div(date_picker(f'input-{type_page}'),
                                 id=f'col-input-{type_page}', style={'display': 'none', 'width': '100%'}),
                        html.Div(date_picker(f'treatment-{type_page}'),
                                 id=f'col-treatment-{type_page}', style={'display': 'none', 'width': '100%'}),

                        html.Hr(),

                        dbc.Label("Режим выбора целей:", className="mt-2"),
                        dbc.RadioItems(
                            id=f"goals-selection-mode-{type_page}",
                            options=[
                                {"label": "Группы", "value": "group"},
                                {"label": "Отдельные", "value": "individual"}
                            ],
                            value="individual",
                            inline=True,
                            className="mb-2"
                        ),

                        # Дропдаун групп целей (скрыт по умолчанию)
                        html.Div(
                            dcc.Dropdown(id=f"dropdown-goal-groups-{type_page}", multi=True),
                            id=f"goal-groups-container-{type_page}",
                            style={'display': 'none'}
                        ),

                        # Превью выбранных групп/целей
                        html.Div(
                            id=f"preview-goals-{type_page}",
                            style={"marginTop": "0.5rem", "fontStyle": "italic", "whiteSpace": "pre-line"}
                        ),

                        # Дропдаун отдельных целей
                        html.Div(
                            dcc.Dropdown(id=f"dropdown-goals-{type_page}", multi=True),
                            id=f"goals-individual-container-{type_page}"
                        ),

                    ], width=8),

                    # Правый столбец: статусы
                    dbc.Col([
                        dbc.Label("Статусы:"),
                        filter_status(type_page)
                    ], width=4),

                ], className="mb-3"),

            ])
        , className="mb-3 shadow-sm", style={"borderRadius": "8px"}),

        # Спиннер вокруг результата
        dcc.Loading(
            id=f'loading-table-{type_page}',
            type="default",
            children=html.Div(id=f'result-table-container-{type_page}')
        )

    ], style={"padding": "0rem"})


economist_doctors_talon_list = economist_doctors_talon_list_def()


# колбэк для открытия/закрытия Offcanvas
@app.callback(
    Output(f"offcanvas-goals-{type_page}", "is_open"),
    Input(f"open-offcanvas-{type_page}", "n_clicks"),
    Input(f"close-offcanvas-{type_page}", "n_clicks"),
    State(f"offcanvas-goals-{type_page}", "is_open"),
)
def toggle_offcanvas(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open


# ---------------------------
# колбэк для наполнения Offcanvas по выбранной конфигурации
@app.callback(
    Output(f"offcanvas-body-{type_page}", "children"),
    Input(f"dropdown-config-{type_page}", "value")
)
def update_offcanvas_body(config_id):
    if not config_id:
        return html.Div("Конфигурация не выбрана.", className="text-muted")
    df = load_configs()
    row = df[df["id"] == config_id].iloc[0]
    groups = json.loads(row["groups_json"])

    # строим список: заголовок группы + ul-лист целей
    content = []
    for grp, goals in sorted(groups.items(), key=lambda x: x[0].lower()):
        content.append(html.H6(grp, className="mt-3 mb-1"))
        content.append(
            html.Ul([html.Li(g) for g in sorted(goals, key=sort_key)])
        )
    return content


# --- Колбэки ---

# 1) При смене конфигурации — только обновляем список групп
@app.callback(
    Output(f"dropdown-goal-groups-{type_page}", "options"),
    Output(f"dropdown-goal-groups-{type_page}", "value"),
    Input(f"dropdown-config-{type_page}", "value")
)
def apply_config(config_id):
    if not config_id:
        return [], []

    df = load_configs()
    row = df[df["id"] == config_id].iloc[0]
    groups_dict = json.loads(row["groups_json"])

    global GOAL_GROUPS
    GOAL_GROUPS = groups_dict

    grp_opts = [
        {"label": grp, "value": grp}
        for grp in sorted(groups_dict.keys(), key=lambda x: x.lower())
    ]
    # По умолчанию выбираем все группы конфигурации
    return grp_opts, [opt["value"] for opt in grp_opts]


# 2) В зависимости от режима «Группы»/«Отдельные» наполняем дроп-целей
@app.callback(
    Output(f"dropdown-goals-{type_page}", "options"),
    Output(f"dropdown-goals-{type_page}", "value"),
    Input(f"goals-selection-mode-{type_page}", "value"),
    Input(f"dropdown-config-{type_page}", "value"),
)
def update_goals_options(mode, config_id):
    # Режим «Группы» → все цели из GOAL_GROUPS
    if mode == "group" and GOAL_GROUPS:
        all_goals = sorted(
            {g for lst in GOAL_GROUPS.values() for g in lst},
            key=sort_key
        )
        opts = [{"label": g, "value": g} for g in all_goals]
        return opts, []

    # Режим «Отдельные» → берём все уникальные цели напрямую из таблицы
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT DISTINCT goal "
            "FROM data_loader_omsdata "
            "WHERE goal IS NOT NULL AND goal <> '-'"
        )).fetchall()
    goals = sorted([r[0] for r in rows], key=sort_key)
    opts = [{"label": g, "value": g} for g in goals]
    return opts, []


# 2) Превью целей по выбранным группам
@app.callback(
    Output(f"preview-goals-{type_page}", "children"),
    Input(f"dropdown-goal-groups-{type_page}", "value")
)
def _preview_goals(selected_groups):
    if not selected_groups:
        return ""
    lines = []
    for grp in selected_groups:
        items = GOAL_GROUPS.get(grp, [])
        if items:
            lines.append(f"{grp}: {', '.join(items)}")
    return "\n".join(lines)


# 3) Toggle для периода
@app.callback(
    Output(f'range-slider-month-{type_page}', 'style'),
    Output(f'col-input-{type_page}', 'style'),
    Output(f'col-treatment-{type_page}', 'style'),
    Input(f'dropdown-report-type-{type_page}', 'value')
)
def toggle_period_inputs(report_type):
    if report_type == 'month':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    if report_type == 'initial_input':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    if report_type == 'treatment':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}


# 4) Toggle между группами и отдельными целями
@app.callback(
    Output(f'goal-groups-container-{type_page}', 'style'),
    Output(f'goals-individual-container-{type_page}', 'style'),
    Input(f'goals-selection-mode-{type_page}', 'value')
)
def toggle_goals(mode):
    return (
        {'display': 'block'}, {'display': 'none'}
    ) if mode == 'group' else (
        {'display': 'none'}, {'display': 'block'}
    )


# 5) Toggle статусов
@app.callback(
    Output(f'status-group-container-{type_page}', 'style'),
    Output(f'status-individual-container-{type_page}', 'style'),
    Input(f'status-selection-mode-{type_page}', 'value')
)
def toggle_status(mode):
    return (
        {'display': 'block'}, {'display': 'none'}
    ) if mode == 'group' else (
        {'display': 'none'}, {'display': 'block'}
    )


# 6) Основной колбэк: строим и выполняем SQL, рисуем таблицу
@app.callback(
    Output(f'result-table-container-{type_page}', 'children'),
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'dropdown-year-{type_page}', 'value'),
    State(f'dropdown-report-type-{type_page}', 'value'),
    State(f'range-slider-month-{type_page}', 'value'),
    State(f'date-picker-range-input-{type_page}', 'start_date'),
    State(f'date-picker-range-input-{type_page}', 'end_date'),
    State(f'date-picker-range-treatment-{type_page}', 'start_date'),
    State(f'date-picker-range-treatment-{type_page}', 'end_date'),
    State(f'dropdown-inogorodniy-{type_page}', 'value'),
    State(f'dropdown-sanction-{type_page}', 'value'),
    State(f'dropdown-amount-null-{type_page}', 'value'),
    State(f'goals-selection-mode-{type_page}', 'value'),
    State(f'dropdown-goals-{type_page}', 'value'),
    State(f'dropdown-goal-groups-{type_page}', 'value'),
    State(f'status-selection-mode-{type_page}', 'value'),
    State(f'status-group-radio-{type_page}', 'value'),
    State(f'status-individual-dropdown-{type_page}', 'value'),
)
def update_table_doctors_goal(
        n, year, report_type, months_range,
        start_in, end_in, start_tr, end_tr,
        inogorod, sanction, amount_null,
        goal_mode, indiv_goals, grp_goals,
        status_mode, status_grp, status_indiv
):
    if not n:
        raise exceptions.PreventUpdate

    # Группы и цели
    if goal_mode == 'group' and grp_goals:
        group_mapping = {g: GOAL_GROUPS.get(g, []) for g in grp_goals}
        goals = [item for g in grp_goals for item in GOAL_GROUPS.get(g, [])]
    elif goal_mode == 'individual' and indiv_goals:
        group_mapping = {}
        goals = indiv_goals
    else:
        # Если ничего не выбрано или режим индивидуальный без выбора — берём все цели БЕЗ применения групп конфигурации
        group_mapping = {}
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT DISTINCT goal FROM data_loader_omsdata WHERE goal IS NOT NULL AND goal <> '-'"
            )).fetchall()
        goals = [r[0] for r in rows]
    goals = sorted(dict.fromkeys(goals), key=sort_key)

    # Статусы
    statuses = (
        status_groups.get(status_grp, [])
        if status_mode == 'group' else (status_indiv or [])
    )

    # Период
    months_ph = None
    si = ei = st = et = None
    if report_type == 'month' and months_range:
        si, ei = months_range
        months_ph = ", ".join(str(m) for m in range(si, ei + 1))
    elif report_type == 'initial_input' and start_in and end_in:
        si = datetime.fromisoformat(start_in).strftime("%d-%m-%Y")
        ei = datetime.fromisoformat(end_in).strftime("%d-%m-%Y")
    elif report_type == 'treatment' and start_tr and end_tr:
        st = datetime.fromisoformat(start_tr).strftime("%d-%m-%Y")
        et = datetime.fromisoformat(end_tr).strftime("%d-%m-%Y")

    # Генерация SQL и выполнение
    sql = sql_query_doctors_goal_stat(
        selected_year=year,
        months_placeholder=months_ph,
        inogorodniy=inogorod,
        sanction=sanction,
        amount_null=amount_null,
        group_mapping=group_mapping,
        goals=goals,
        status_list=statuses,
        report_type=report_type,
        input_start=si, input_end=ei,
        treatment_start=st, treatment_end=et
    )
    cols, data = TableUpdater.query_to_df(engine, sql)
    df = pd.DataFrame(data)

    # Рендерим DataTable
    return html.Div([
        dash_table.DataTable(
            id=f"table-{type_page}",
            columns=[
                {
                    "name": c["name"] if isinstance(c, dict) else c,
                    "id": c["id"] if isinstance(c, dict) else c
                }
                for c in cols
            ],
            data=df.to_dict('records'),
            page_size=20,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            style_table={"overflowX": "auto"},
        )
    ])
