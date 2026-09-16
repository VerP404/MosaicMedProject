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
from apps.analytical_app.pages.economist.doctors.query import (
    sql_query_doctors_goal_stat,
    sql_query_buildings_goal_stat,
    sql_query_unmatched_doctors,
    sql_query_doctors_goal_details,
)
from apps.analytical_app.query_executor import engine

type_page = "econ-doctors-talon-list"


# Вспомогательная функция сортировки
def sort_key(x):
    return (0, int(x)) if x.isdigit() else (1, x.lower())


def _parse_dash_date(value):
    """Дата из DatePickerRange → DD-MM-YYYY для SQL."""
    if not value:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y")
    s = str(value).split("T")[0]
    return datetime.strptime(s, "%Y-%m-%d").strftime("%d-%m-%Y")


def _resolve_period(report_type, months_range, start_in, end_in, start_tr, end_tr):
    """
    Возвращает (months_ph, input_start, input_end, treatment_start, treatment_end, error).
    Для дат формирования/лечения отчётный месяц не используется.
    """
    report_type = report_type or "month"
    if report_type == "month":
        if not months_range or len(months_range) != 2:
            return None, None, None, None, None, "Укажите диапазон отчётных месяцев."
        si, ei = int(months_range[0]), int(months_range[1])
        months_ph = ", ".join(str(m) for m in range(si, ei + 1))
        return months_ph, None, None, None, None, None

    if report_type == "initial_input":
        si, ei = _parse_dash_date(start_in), _parse_dash_date(end_in)
        if not si or not ei:
            return None, None, None, None, None, "Укажите период по дате формирования."
        return None, si, ei, None, None, None

    if report_type == "treatment":
        st, et = _parse_dash_date(start_tr), _parse_dash_date(end_tr)
        if not st or not et:
            return None, None, None, None, None, "Укажите период по дате окончания лечения."
        return None, None, None, st, et, None

    return None, None, None, None, None, "Неизвестный тип периода."


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

                    # Правый столбец: статусы + сопоставление со справочником
                    dbc.Col([
                        dbc.Label("Статусы:"),
                        filter_status(type_page),
                        html.Hr(),
                        dbc.Label("Врачи в справочнике:"),
                        dbc.RadioItems(
                            id=f"doctor-match-mode-{type_page}",
                            options=[
                                {"label": "Все", "value": "all"},
                                {"label": "Только в справочнике", "value": "matched"},
                                {"label": "Только не заведены", "value": "unmatched"},
                            ],
                            value="all",
                            className="mb-1",
                        ),
                        html.Small(
                            "«Не заведены» — код из талона ОМС нет в personnel (карточка врача).",
                            className="text-muted",
                        ),
                    ], width=4),

                ], className="mb-3"),

            ])
        , className="mb-3 shadow-sm", style={"borderRadius": "8px"}),

        # Результаты: вкладки
        dbc.Tabs([
            dbc.Tab(
                label="По врачам",
                tab_id=f"tab-doctors-{type_page}",
                children=[
                    dcc.Loading(
                        id=f'loading-table-{type_page}-doctors',
                        type="default",
                        children=html.Div(id=f'result-table-container-{type_page}-doctors')
                    ),
                    dbc.Card(
                        [
                            dbc.CardHeader("Детализация по талонам"),
                            dbc.CardBody(
                                [
                                    html.Div(
                                        id=f"details-title-{type_page}",
                                        style={"fontWeight": "bold", "marginBottom": "10px"},
                                    ),
                                    dbc.Button(
                                        "Детализация",
                                        id=f"details-button-{type_page}",
                                        color="primary",
                                        size="sm",
                                        disabled=True,
                                        className="mb-2",
                                    ),
                                    html.Small(
                                        "Выберите ячейку цели (или группы / Итого) в таблице выше и нажмите «Детализация».",
                                        className="text-muted d-block mb-2",
                                    ),
                                    dcc.Loading(
                                        id=f"loading-details-{type_page}",
                                        type="default",
                                        children=html.Div(id=f"details-table-container-{type_page}"),
                                    ),
                                ]
                            ),
                        ],
                        className="mt-3 shadow-sm",
                    ),
                ]
            ),
            dbc.Tab(
                label="По корпусам",
                tab_id=f"tab-buildings-{type_page}",
                children=[
                    dcc.Loading(
                        id=f'loading-table-{type_page}-buildings',
                        type="default",
                        children=html.Div(id=f'result-table-container-{type_page}-buildings')
                    )
                ]
            ),
            dbc.Tab(
                label="Не заведены в справочник",
                tab_id=f"tab-unmatched-{type_page}",
                children=[
                    html.Div(
                        [
                            html.P(
                                "Коды врачей из талонов ОМС, для которых нет записи в personnel "
                                "(нужно завести DoctorRecord с этим кодом).",
                                className="text-muted small mt-2 mb-2",
                            ),
                            dcc.Loading(
                                id=f'loading-table-{type_page}-unmatched',
                                type="default",
                                children=html.Div(id=f'result-table-container-{type_page}-unmatched')
                            ),
                        ]
                    )
                ]
            ),
        ], active_tab=f"tab-doctors-{type_page}")

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

# 1) При смене конфигурации — обновляем список групп и переключаем режим
@app.callback(
    Output(f"dropdown-goal-groups-{type_page}", "options"),
    Output(f"dropdown-goal-groups-{type_page}", "value"),
    Output(f"goals-selection-mode-{type_page}", "value"),
    Input(f"dropdown-config-{type_page}", "value")
)
def apply_config(config_id):
    if not config_id:
        return [], [], "individual"

    df = load_configs()
    row = df[df["id"] == config_id].iloc[0]
    groups_dict = json.loads(row["groups_json"])

    global GOAL_GROUPS
    GOAL_GROUPS = groups_dict

    grp_opts = [
        {"label": grp, "value": grp}
        for grp in sorted(groups_dict.keys(), key=lambda x: x.lower())
    ]
    # По умолчанию выбираем все группы конфигурации и переключаем в режим "Группы"
    return grp_opts, [opt["value"] for opt in grp_opts], "group"


# 2) Скрытие/показ полей периода в зависимости от типа отчёта
@app.callback(
    Output(f"col-months-{type_page}", "style"),
    Output(f"col-input-{type_page}", "style"),
    Output(f"col-treatment-{type_page}", "style"),
    Input(f"dropdown-report-type-{type_page}", "value")
)
def toggle_period_inputs(report_type):
    if report_type == 'month':
        return {'width': '100%'}, {'display': 'none', 'width': '100%'}, {'display': 'none', 'width': '100%'}
    elif report_type == 'initial_input':
        return {'display': 'none', 'width': '100%'}, {'width': '100%'}, {'display': 'none', 'width': '100%'}
    elif report_type == 'treatment':
        return {'display': 'none', 'width': '100%'}, {'display': 'none', 'width': '100%'}, {'width': '100%'}
    else:
        return {'width': '100%'}, {'display': 'none', 'width': '100%'}, {'display': 'none', 'width': '100%'}


# 3) В зависимости от режима «Группы»/«Отдельные» наполняем дроп-целей
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


# 4) Превью целей по выбранным группам
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


# 5) Toggle между группами и отдельными целями
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


# 6a) Таблица по врачам
@app.callback(
    Output(f'result-table-container-{type_page}-doctors', 'children'),
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
    State(f'doctor-match-mode-{type_page}', 'value'),
)
def update_table_doctors_goal(
        n, year, report_type, months_range,
        start_in, end_in, start_tr, end_tr,
        inogorod, sanction, amount_null,
        goal_mode, indiv_goals, grp_goals,
        status_mode, status_grp, status_indiv,
        match_mode,
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
    months_ph, si, ei, st, et, period_err = _resolve_period(
        report_type, months_range, start_in, end_in, start_tr, end_tr
    )
    if period_err:
        return html.Div(dbc.Alert(period_err, color="warning", className="mt-3"))

    match_mode = match_mode or "all"

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
        treatment_start=st, treatment_end=et,
        match_mode=match_mode,
    )
    cols, data = TableUpdater.query_to_df(engine, sql)
    df = pd.DataFrame(data)

    # Проверяем, пустая ли таблица
    if df.empty:
        return html.Div([
            dbc.Alert([
                html.H5("Данные не найдены", className="alert-heading"),
                html.P("По выбранным условиям не найдено ни одной записи."),
                html.Hr(),
                html.H6("💡 Попробуйте изменить условия:"),
                html.Ul([
                    html.Li("Проверьте выбранный период (год, месяцы или даты)"),
                    html.Li("Измените фильтры по статусам"),
                    html.Li("Выберите другие цели или группы целей"),
                    html.Li("Проверьте режим «Врачи в справочнике»"),
                    html.Li("Проверьте фильтры по типу пациентов (местные/иногородние)"),
                    html.Li("Попробуйте другой тип отчёта")
                ]),
                html.P("Если проблема сохраняется, обратитесь к администратору.", className="mb-0")
            ], color="info", className="mt-3")
        ])

    # Рендерим DataTable
    return html.Div([
        dash_table.DataTable(
            id=f"table-{type_page}-doctors",
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
            cell_selectable=True,
            style_table={"overflowX": "auto"},
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": (
                            '{specialty} eq "" || {specialty} is blank'
                        )
                    },
                    "backgroundColor": "#fff3cd",
                }
            ],
        )
    ])


# 6b) Таблица по корпусам
@app.callback(
    Output(f'result-table-container-{type_page}-buildings', 'children'),
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
def update_table_buildings_goal(
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
        group_mapping = {}
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT DISTINCT goal FROM data_loader_omsdata WHERE goal IS NOT NULL AND goal <> '-'"
            )).fetchall()
        goals = [r[0] for r in rows]
    goals = sorted(dict.fromkeys(goals), key=sort_key)

    statuses = (
        status_groups.get(status_grp, [])
        if status_mode == 'group' else (status_indiv or [])
    )

    months_ph, si, ei, st, et, period_err = _resolve_period(
        report_type, months_range, start_in, end_in, start_tr, end_tr
    )
    if period_err:
        return html.Div(dbc.Alert(period_err, color="warning", className="mt-3"))

    sql = sql_query_buildings_goal_stat(
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

    # Проверяем, пустая ли таблица
    if df.empty:
        return html.Div([
            dbc.Alert([
                html.H5("📊 Данные не найдены", className="alert-heading"),
                html.P("По выбранным условиям не найдено ни одной записи."),
                html.Hr(),
                html.H6("💡 Попробуйте изменить условия:"),
                html.Ul([
                    html.Li("Проверьте выбранный период (год, месяцы или даты)"),
                    html.Li("Измените фильтры по статусам"),
                    html.Li("Выберите другие цели или группы целей"),
                    html.Li("Проверьте фильтры по типу пациентов (местные/иногородние)"),
                    html.Li("Попробуйте другой тип отчёта")
                ]),
                html.P("Если проблема сохраняется, обратитесь к администратору.", className="mb-0")
            ], color="info", className="mt-3")
        ])

    return html.Div([
        dash_table.DataTable(
            id=f"table-{type_page}-buildings",
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


# 6c) Врачи из талонов, не заведённые в personnel
@app.callback(
    Output(f'result-table-container-{type_page}-unmatched', 'children'),
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
def update_table_unmatched_doctors(
        n, year, report_type, months_range,
        start_in, end_in, start_tr, end_tr,
        inogorod, sanction, amount_null,
        goal_mode, indiv_goals, grp_goals,
        status_mode, status_grp, status_indiv,
):
    if not n:
        raise exceptions.PreventUpdate

    if goal_mode == 'group' and grp_goals:
        goals = [item for g in grp_goals for item in GOAL_GROUPS.get(g, [])]
    elif goal_mode == 'individual' and indiv_goals:
        goals = indiv_goals
    else:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT DISTINCT goal FROM data_loader_omsdata WHERE goal IS NOT NULL AND goal <> '-'"
            )).fetchall()
        goals = [r[0] for r in rows]
    goals = sorted(dict.fromkeys(goals), key=sort_key)

    statuses = (
        status_groups.get(status_grp, [])
        if status_mode == 'group' else (status_indiv or [])
    )

    months_ph, si, ei, st, et, period_err = _resolve_period(
        report_type, months_range, start_in, end_in, start_tr, end_tr
    )
    if period_err:
        return html.Div(dbc.Alert(period_err, color="warning", className="mt-3"))

    sql = sql_query_unmatched_doctors(
        selected_year=year,
        months_placeholder=months_ph,
        inogorodniy=inogorod,
        sanction=sanction,
        amount_null=amount_null,
        goals=goals,
        status_list=statuses,
        input_start=si,
        input_end=ei,
        treatment_start=st,
        treatment_end=et,
    )
    cols, data = TableUpdater.query_to_df(engine, sql)
    df = pd.DataFrame(data)

    if df.empty:
        return html.Div([
            dbc.Alert(
                "Все врачи из выборки найдены в справочнике personnel — несопоставленных кодов нет.",
                color="success",
                className="mt-3",
            )
        ])

    total_talons = int(df["Талонов"].sum()) if "Талонов" in df.columns else 0
    return html.Div([
        dbc.Alert(
            f"Кодов без карточки: {len(df)}, талонов: {total_talons}. "
            "Заведите DoctorRecord с этим кодом в разделе персонала.",
            color="warning",
            className="mt-2 mb-2",
        ),
        dash_table.DataTable(
            id=f"table-{type_page}-unmatched",
            columns=[
                {
                    "name": c["name"] if isinstance(c, dict) else c,
                    "id": c["id"] if isinstance(c, dict) else c
                }
                for c in cols
            ],
            data=df.to_dict('records'),
            page_size=25,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            style_table={"overflowX": "auto"},
            style_cell={"whiteSpace": "normal", "minWidth": "80px"},
        )
    ])


_ROW_META_COLS = {"doctor", "specialty", "building", "department", "doctor_code"}


@app.callback(
    Output(f"details-button-{type_page}", "disabled"),
    Input(f"table-{type_page}-doctors", "active_cell"),
    prevent_initial_call=False,
)
def update_doctors_details_button_state(active_cell):
    if not active_cell:
        return True
    column_id = active_cell.get("column_id")
    if not column_id or column_id in _ROW_META_COLS:
        return True
    return False


@app.callback(
    Output(f"details-title-{type_page}", "children"),
    Output(f"details-table-container-{type_page}", "children"),
    Input(f"details-button-{type_page}", "n_clicks"),
    State(f"table-{type_page}-doctors", "derived_viewport_data"),
    State(f"table-{type_page}-doctors", "derived_virtual_data"),
    State(f"table-{type_page}-doctors", "data"),
    State(f"table-{type_page}-doctors", "active_cell"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"dropdown-report-type-{type_page}", "value"),
    State(f"range-slider-month-{type_page}", "value"),
    State(f"date-picker-range-input-{type_page}", "start_date"),
    State(f"date-picker-range-input-{type_page}", "end_date"),
    State(f"date-picker-range-treatment-{type_page}", "start_date"),
    State(f"date-picker-range-treatment-{type_page}", "end_date"),
    State(f"dropdown-inogorodniy-{type_page}", "value"),
    State(f"dropdown-sanction-{type_page}", "value"),
    State(f"dropdown-amount-null-{type_page}", "value"),
    State(f"goals-selection-mode-{type_page}", "value"),
    State(f"dropdown-goals-{type_page}", "value"),
    State(f"dropdown-goal-groups-{type_page}", "value"),
    State(f"status-selection-mode-{type_page}", "value"),
    State(f"status-group-radio-{type_page}", "value"),
    State(f"status-individual-dropdown-{type_page}", "value"),
    State(f"doctor-match-mode-{type_page}", "value"),
    prevent_initial_call=True,
)
def show_doctors_goal_details(
    n_clicks, viewport_data, virtual_data, table_data, active_cell,
    year, report_type, months_range,
    start_in, end_in, start_tr, end_tr,
    inogorod, sanction, amount_null,
    goal_mode, indiv_goals, grp_goals,
    status_mode, status_grp, status_indiv,
    match_mode,
):
    if not n_clicks or not active_cell:
        return "", []

    # active_cell.row — индекс в текущей странице (viewport) после фильтра/сортировки
    rows = viewport_data if viewport_data is not None else (
        virtual_data if virtual_data is not None else table_data
    )
    if not rows:
        return "", []

    row_idx = active_cell.get("row")
    column_id = active_cell.get("column_id")
    if row_idx is None or row_idx >= len(rows) or not column_id:
        return "Ошибка: не выбрана ячейка", []

    if column_id in {"doctor", "specialty", "building", "department", "doctor_code"}:
        return "Выберите колонку цели, группы целей или «Итого»", []

    row = rows[row_idx]
    doctor = row.get("doctor")
    specialty = row.get("specialty")
    building = row.get("building")
    department = row.get("department")
    doctor_code = row.get("doctor_code")

    # Цели для детализации
    if goal_mode == "group" and grp_goals:
        all_goals = [item for g in grp_goals for item in GOAL_GROUPS.get(g, [])]
        group_mapping = {g: GOAL_GROUPS.get(g, []) for g in grp_goals}
    elif goal_mode == "individual" and indiv_goals:
        all_goals = list(indiv_goals)
        group_mapping = {}
    else:
        group_mapping = {}
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT DISTINCT goal FROM data_loader_omsdata WHERE goal IS NOT NULL AND goal <> '-'"
            )).fetchall()
        all_goals = [r[0] for r in rows]
    all_goals = sorted(dict.fromkeys(all_goals), key=sort_key)

    if column_id == "Итого":
        detail_goals = all_goals
        detail_label = "Итого"
    elif column_id in group_mapping:
        detail_goals = group_mapping[column_id]
        detail_label = f"группа «{column_id}»"
    else:
        detail_goals = [column_id]
        detail_label = f"цель «{column_id}»"

    if not detail_goals:
        return "Нет целей для детализации", []

    statuses = (
        status_groups.get(status_grp, [])
        if status_mode == "group" else (status_indiv or [])
    )

    months_ph, si, ei, st, et, period_err = _resolve_period(
        report_type, months_range, start_in, end_in, start_tr, end_tr
    )
    if period_err:
        return period_err, []

    try:
        sql = sql_query_doctors_goal_details(
            selected_year=year,
            months_placeholder=months_ph,
            inogorodniy=inogorod,
            sanction=sanction,
            amount_null=amount_null,
            detail_goals=detail_goals,
            status_list=statuses,
            input_start=si,
            input_end=ei,
            treatment_start=st,
            treatment_end=et,
            match_mode=match_mode or "all",
            doctor=doctor,
            specialty=specialty,
            building=building,
            department=department,
            doctor_code=doctor_code,
        )
        cols, data = TableUpdater.query_to_df(engine, sql)
        df = pd.DataFrame(data)
    except Exception as e:
        return f"Ошибка детализации: {e}", []

    title = f"Детализация: {doctor or '—'} — {detail_label} ({len(df)} тал.)"
    if df.empty:
        return title, dbc.Alert("Талоны не найдены по выбранной ячейке.", color="info")

    return title, dash_table.DataTable(
        id=f"table-{type_page}-details",
        columns=[
            {
                "name": c["name"] if isinstance(c, dict) else c,
                "id": c["id"] if isinstance(c, dict) else c,
            }
            for c in cols
        ],
        data=df.to_dict("records"),
        page_size=20,
        sort_action="native",
        filter_action="native",
        export_format="xlsx",
        style_table={"overflowX": "auto"},
        style_cell={"whiteSpace": "normal", "minWidth": "70px", "maxWidth": "220px"},
    )
