import io
from datetime import datetime

from dash import html, dcc, Input, Output, State, exceptions, dash_table
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import (
    update_buttons,
    filter_years,
    filter_report_type,
    filter_inogorod,
    filter_sanction,
    filter_amount_null,
    filter_months,
    date_picker,
    get_current_reporting_month,
    filter_status,
    status_groups, filter_health_group,
    filter_icd_codes
)
from apps.analytical_app.query_executor import execute_query

type_page = "tab7-wo"

# Функция для создания мультидропдауна с выбором целей
def filter_goals(type_page):
    query = '''
        SELECT DISTINCT goal
        FROM load_data_oms_data
        WHERE goal IS NOT NULL
        ORDER BY goal
    '''
    goals = [row[0] for row in execute_query(query)]
    options = [{'label': g, 'value': g} for g in goals]
    return html.Div([
        html.Label("Цели", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id=f"dropdown-goals-{type_page}",
            options=options,
            value=[],
            multi=True,
            clearable=True,
            placeholder="Выберите цель...",
            style={"whiteSpace": "normal"},
            optionHeight=70,
            searchable=True
        )
    ])

# Функция для создания мультидропдауна с выбором корпусов
def filter_buildings(type_page):
    query = '''
        SELECT DISTINCT building
        FROM load_data_oms_data
        WHERE building IS NOT NULL
        ORDER BY building
    '''
    buildings = [row[0] for row in execute_query(query)]
    options = [{'label': b, 'value': b} for b in buildings]
    return html.Div([
        html.Label("Корпуса", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id=f"dropdown-buildings-{type_page}",
            options=options,
            value=[],
            multi=True,
            clearable=True,
            placeholder="Выберите корпус...",
            style={"whiteSpace": "normal"},
            optionHeight=70,
            searchable=True
        )
    ])

# Функция для создания мультидропдауна с выбором профилей
def filter_profiles(type_page):
    query = '''
        SELECT DISTINCT profile
        FROM load_data_oms_data
        WHERE profile IS NOT NULL
        ORDER BY profile
    '''
    profiles = [row[0] for row in execute_query(query)]
    options = [{'label': p, 'value': p} for p in profiles]
    return html.Div([
        html.Label("Профили", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id=f"dropdown-profiles-{type_page}",
            options=options,
            value=[],
            multi=True,
            clearable=True,
            placeholder="Выберите профиль...",
            style={"whiteSpace": "normal"},
            optionHeight=70,
            searchable=True
        )
    ])

# Функция для создания мультидропдауна с выбором групп здоровья
def filter_health_group(type_page):
    query = '''
        SELECT DISTINCT health_group
        FROM load_data_oms_data
        WHERE health_group IS NOT NULL
        ORDER BY health_group
    '''
    groups = [row[0] for row in execute_query(query)]
    options = [{'label': g, 'value': g} for g in groups]
    return html.Div([
        html.Label("Группы здоровья", style={"font-weight": "bold"}),
        dcc.Dropdown(
            id=f"dropdown-health-group-{type_page}",
            options=options,
            value=[],
            multi=True,
            clearable=True,
            placeholder="Выберите группу...",
            style={"whiteSpace": "normal"},
            optionHeight=70,
            searchable=True
        )
    ])

adults_dv10 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader(
                                dbc.Row(
                                    [
                                        dbc.Col(html.H5("Фильтры", className="mb-0"), width="auto"),
                                        dbc.Col(
                                            html.Div(
                                                id=f"last-updated-main-{type_page}",
                                                style={
                                                    "textAlign": "right",
                                                    "fontSize": "0.8rem",
                                                    "color": "#666"
                                                },
                                            ),
                                            width=True
                                        ),
                                    ],
                                    align="center",
                                    justify="between",
                                )
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                    dbc.Col(filter_report_type(type_page), width=2),
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                    dbc.Col(html.Button("Выгрузить в Excel", id=f"btn-export-{type_page}", n_clicks=0,
                                                        className="btn btn-outline-primary"), width="auto"),
                                    dcc.Download(id=f"download-{type_page}")
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_months(type_page), width=6),
                                    dbc.Col(filter_health_group(type_page), width=6),
                                    dbc.Col(
                                        html.Label(
                                            "Выберите дату",
                                            id=f"label-date-{type_page}",
                                            style={"font-weight": "bold", "display": "none"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        date_picker(f"input-{type_page}"),
                                        width=4,
                                        id=f"col-input-{type_page}",
                                        style={"display": "none"},
                                    ),
                                    dbc.Col(
                                        date_picker(f"treatment-{type_page}"),
                                        width=4,
                                        id=f"col-treatment-{type_page}",
                                        style={"display": "none"},
                                    ),
                                ],
                                align="center",
                                style={"marginTop": "10px"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_status(type_page), width=6),
                                    dbc.Col(filter_icd_codes(type_page), width=6),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(filter_goals(type_page), width=4),
                                    dbc.Col(filter_buildings(type_page), width=4),
                                    dbc.Col(filter_profiles(type_page), width=4),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(id=f"selected-period-{type_page}", className="filters-label"),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        html.Div(id=f"current-month-name-{type_page}", className="filters-label"),
                                        width=6,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px rgba(0,0,0,0.1)",
                        "border-radius": "10px",
                    },
                ),
                width=12,
            ),
            style={"marginBottom": "1rem"},
        ),
        dcc.Loading(id=f"loading-output-{type_page}", type="default"),
        dcc.Loading(
            id=f"loading-table-{type_page}",
            type="default",
            children=dbc.Card([
                                dbc.CardHeader("Уникальные пациенты и их талоны по диагнозам"),
                                dbc.CardBody(
                                    html.Div(id=f"table-container-{type_page}")
                                )
                            ], className="mb-3")
        ),
        dbc.Card([
            dbc.CardHeader("Детализация по выбранному диагнозу"),
            dbc.CardBody([
                dash_table.DataTable(
                    id=f"datatable-details-{type_page}",
                    columns=[],  # будут заполнены динамически
                    data=[],  # будут заполнены динамически
                    filter_action="native",  # включает нативные фильтры сверху
                    sort_action="native",  # включает сортировку по столбцам
                    page_size=20,
                    editable=False,  # запрещает редактирование
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "minWidth": "120px",
                        "maxWidth": "400px",
                        "whiteSpace": "normal"
                    },
                    style_header={"fontWeight": "bold"},
                    export_format="xlsx",  # позволяет экспортировать в Excel (кнопка появляется при наведении)
                ),
            ])
        ])
    ],
    style={"padding": "0rem"},
)


# Callback для загрузки списка целей
@app.callback(
    Output(f"dropdown-goals-{type_page}", "options"),
    Input("date-interval", "n_intervals"),
    prevent_initial_call=False
)
def load_goals(n):
    sql = text("""
        SELECT DISTINCT goal 
        FROM load_data_oms_data 
        WHERE goal IS NOT NULL 
        ORDER BY goal
    """)
    with engine.connect() as conn:
        goals = [row[0] for row in conn.execute(sql).fetchall()]
    
    options = [{"label": g, "value": g} for g in goals]
    return options


# Для целей
def get_all_goals():
    query = '''
        SELECT DISTINCT goal
        FROM load_data_oms_data
        WHERE goal IS NOT NULL
        ORDER BY goal
    '''
    return [row[0] for row in execute_query(query)]

@app.callback(
    Output(f"dropdown-goals-{type_page}", "value"),
    Input(f"dropdown-goals-{type_page}", "value"),
    prevent_initial_call=True
)
def update_goals_selection(selected_values):
    return selected_values


# Для корпусов
def get_all_buildings():
    query = '''
        SELECT DISTINCT building
        FROM load_data_oms_data
        WHERE building IS NOT NULL
        ORDER BY building
    '''
    return [row[0] for row in execute_query(query)]

@app.callback(
    Output(f"dropdown-buildings-{type_page}", "value"),
    Input(f"dropdown-buildings-{type_page}", "value"),
    prevent_initial_call=True
)
def update_buildings_selection(selected_values):
    return selected_values


# Для профилей
def get_all_profiles():
    query = '''
        SELECT DISTINCT profile
        FROM load_data_oms_data
        WHERE profile IS NOT NULL
        ORDER BY profile
    '''
    return [row[0] for row in execute_query(query)]

@app.callback(
    Output(f"dropdown-profiles-{type_page}", "value"),
    Input(f"dropdown-profiles-{type_page}", "value"),
    prevent_initial_call=True
)
def update_profiles_selection(selected_values):
    return selected_values


# Для групп здоровья
def get_all_health_groups():
    query = '''
        SELECT DISTINCT health_group
        FROM load_data_oms_data
        WHERE health_group IS NOT NULL
        ORDER BY health_group
    '''
    return [row[0] for row in execute_query(query)]

@app.callback(
    Output(f"dropdown-health-group-{type_page}", "value"),
    Input(f"dropdown-health-group-{type_page}", "value"),
    prevent_initial_call=True
)
def update_health_groups_selection(selected_values):
    return selected_values


@app.callback(
    Output(f"last-updated-main-{type_page}", "children"),
    Input(f"update-button-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def _update_last_updated(n):
    sql = text("SELECT MAX(updated_at) FROM load_data_oms_data")
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
    if row and row[0]:
        return "Талоны ОМС обновлены: " + row[0].strftime("%d.%m.%Y %H:%M")
    return ""


@app.callback(
    [Output(f"label-date-{type_page}", "style"),
     Output(f"col-input-{type_page}", "style"),
     Output(f"col-treatment-{type_page}", "style")],
    [Input(f"dropdown-report-type-{type_page}", "value")],
)
def _toggle_date_filters(report_type):
    if report_type == "initial_input":
        return {"display": "block"}, {"display": "block"}, {"display": "none"}
    if report_type == "treatment":
        return {"display": "block"}, {"display": "none"}, {"display": "block"}
    return {"display": "none"}, {"display": "none"}, {"display": "none"}


@app.callback(
    Output(f"current-month-name-{type_page}", "children"),
    Input("date-interval", "n_intervals"),
)
def _update_current_month(n):
    _, name = get_current_reporting_month()
    return name


@app.callback(
    Output(f"selected-period-{type_page}", "children"),
    [Input(f"range-slider-month-{type_page}", "value"),
     Input(f"dropdown-year-{type_page}", "value")],
)
def _show_period(months, year):
    return f"Год: {year}, месяцы: {months}"


from dash import no_update, callback_context
from dash.dcc import send_data_frame, send_bytes
from dash.exceptions import PreventUpdate
import pandas as pd
import datetime
from sqlalchemy import text
from apps.analytical_app.query_executor import engine


@app.callback(
    [
        Output(f"table-container-{type_page}", "children"),
        Output(f"download-{type_page}", "data"),
    ],
    [
        Input(f"update-button-{type_page}", "n_clicks"),
        Input(f"btn-export-{type_page}", "n_clicks"),
    ],
    [
        State(f"range-slider-month-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        State(f"dropdown-inogorodniy-{type_page}", "value"),
        State(f"dropdown-sanction-{type_page}", "value"),
        State(f"dropdown-amount-null-{type_page}", "value"),
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"dropdown-health-group-{type_page}", "value"),
        State(f"dropdown-icd-{type_page}", "value"),
        State(f"dropdown-goals-{type_page}", "value"),
        State(f"dropdown-buildings-{type_page}", "value"),
        State(f"dropdown-profiles-{type_page}", "value"),
    ],
    prevent_initial_call=True
)
def render_tab7_table_and_export(
        n_clicks_update, n_clicks_export,
        selected_months, year, inog, sanc, amt_null,
        start_input, end_input, start_treat, end_treat,
        report_type, status_mode, status_group, status_indiv,
        health_groups, icd_codes, goals, buildings, profiles
):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # --- собираем WHERE-условия ---
    conds = [f"report_year = {int(year)}"]

    # Добавляем условие для кодов МКБ
    if icd_codes:
        icd_conditions = []
        for code in icd_codes:
            icd_conditions.append(f"main_diagnosis_code = '{code}'")
        if icd_conditions:
            conds.append(f"({' OR '.join(icd_conditions)})")

    if report_type == "month" and selected_months:
        start, end = selected_months
        conds.append(f"report_month BETWEEN {start} AND {end}")
    if report_type == "initial_input" and start_input and end_input:
        conds.append(
            f"initial_input_date BETWEEN '{start_input[:10]}' AND '{end_input[:10]}'"
        )
    if report_type == "treatment" and start_treat and end_treat:
        conds.append(
            f"treatment_end BETWEEN '{start_treat[:10]}' AND '{end_treat[:10]}'"
        )

    if inog == '1':
        conds.append("inogorodniy = FALSE")
    elif inog == '2':
        conds.append("inogorodniy = TRUE")

    if sanc == '1':
        conds.append("(sanctions = '-' OR sanctions IS NULL)")
    elif sanc == '2':
        conds.append("sanctions <> '-'")

    if amt_null == '1':
        conds.append("amount_numeric IS NOT NULL")
    elif amt_null == '2':
        conds.append("amount_numeric IS NULL")

    # статусы
    if status_mode == "group":
        sts = status_groups.get(status_group, [])
    else:
        sts = status_indiv or []
    if sts:
        q = ",".join(f"'{s}'" for s in sts)
        conds.append(f"status IN ({q})")

    # health_group
    if health_groups:
        if "all" in health_groups:
            pass
        elif health_groups == ["with"]:
            conds.append("health_group <> '-'")
        else:
            values = ", ".join(f"'{hg}'" for hg in health_groups)
            conds.append(f"health_group IN ({values})")

    # goals
    if goals and "all" not in goals:
        values = ", ".join(f"'{g}'" for g in goals)
        conds.append(f"goal IN ({values})")

    # buildings
    if buildings and "all" not in buildings:
        values = ", ".join(f"'{b}'" for b in buildings)
        conds.append(f"building IN ({values})")

    # profiles
    if profiles and "all" not in profiles:
        values = ", ".join(f"'{p}'" for p in profiles)
        conds.append(f"profile IN ({values})")

    where = " AND ".join(conds)

    # --- основной SQL для подсчета уникальных талонов ---
    sql = f"""
    WITH filtered_data AS (
        SELECT DISTINCT enp, main_diagnosis_code
        FROM load_data_oms_data
        WHERE {where}
    )
    SELECT 
        main_diagnosis_code,
        COUNT(DISTINCT enp) as unique_patients,
        (SELECT COUNT(*) FROM load_data_oms_data WHERE {where} AND main_diagnosis_code = fd.main_diagnosis_code) as total_talons
    FROM filtered_data fd
    GROUP BY main_diagnosis_code
    ORDER BY unique_patients DESC;
    """
    
    df = pd.read_sql_query(text(sql), engine)

    # Добавляем строку "Всего"
    if not df.empty:
        total_row = pd.DataFrame({
            'main_diagnosis_code': ['Всего'],
            'unique_patients': [df['unique_patients'].sum()],
            'total_talons': [df['total_talons'].sum()]
        })
        df = pd.concat([total_row, df], ignore_index=True)

    # --- возвращаем результат в зависимости от кнопки ---
    if trigger == f"update-button-{type_page}":
        table = dash_table.DataTable(
            id=f"datatable-{type_page}",
                columns=[
                {"name": "Основной диагноз", "id": "main_diagnosis_code"},
                {"name": "Уникальные пациенты", "id": "unique_patients"},
                {"name": "Всего талонов", "id": "total_talons"},
            ],
            data=df.to_dict("records"),
            page_size=20,
            filter_action="native",
            sort_action="native",
            editable=False,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "minWidth": "120px", "maxWidth": "400px", "whiteSpace": "normal"},
            style_header={"fontWeight": "bold"},
        )
        return table, no_update

    elif trigger == f"btn-export-{type_page}":
        # подготавливаем табличные данные
        df.index.name = "Код МКБ"
        # собираем параметры
        start, end = selected_months or (None, None)
        params = {
            "Год": year,
            "Период (месяцы)": f"{start}–{end}" if start and end else "",
            "Тип отчёта": report_type,
            "Иногородние": inog,
            "Санкции": sanc,
            "Сумма null": amt_null,
            "Статус (режим)": status_mode,
            "Статус (группа)": status_group,
            "Статус (индив)": status_indiv,
            "Группы здоровья": ", ".join(health_groups) if health_groups else "Все",
            "Цели": ", ".join(goals) if goals and "all" not in goals else "Все",
            "Корпуса": ", ".join(buildings) if buildings and "all" not in buildings else "Все",
            "Профили": ", ".join(profiles) if profiles and "all" not in profiles else "Все",
        }

        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Данные", index=False)
                pd.DataFrame({
                    "Параметр": list(params.keys()),
                    "Значение": list(params.values())
                }).to_excel(writer, sheet_name="Параметры", index=False)
            buffer.seek(0)

        filename = f"unique_talons_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx"
        return no_update, send_bytes(to_excel, filename)
    else:
        raise PreventUpdate


@app.callback(
    Output(f"dropdown-icd-{type_page}", "value"),
    [
        Input(f"btn-apply-icd-pattern-{type_page}", "n_clicks"),
    ],
    [
        State(f"input-icd-pattern-{type_page}", "value"),
        State(f"dropdown-icd-{type_page}", "options"),
        State(f"dropdown-icd-{type_page}", "value"),
    ],
    prevent_initial_call=True
)
def add_icd_by_pattern(n_clicks, pattern, options, current_values):
    from dash import no_update
    if not pattern:
        return no_update
    pattern = pattern.upper()
    matched = [opt['value'] for opt in options if opt['value'].startswith(pattern)]
    # Объединяем с уже выбранными, убираем дубли
    result = list(sorted(set(current_values or []) | set(matched)))
    return result


# Callback для загрузки списка групп здоровья
@app.callback(
    Output(f"dropdown-health-group-{type_page}", "options"),
    Input("date-interval", "n_intervals"),
    prevent_initial_call=False
)
def load_health_groups(n):
    sql = text("""
        SELECT DISTINCT health_group 
        FROM load_data_oms_data 
        WHERE health_group IS NOT NULL 
        ORDER BY health_group
    """)
    with engine.connect() as conn:
        health_groups = [row[0] for row in conn.execute(sql).fetchall()]
    
    options = [{"label": hg, "value": hg} for hg in health_groups]
    return options


@app.callback(
    [
        Output(f"datatable-details-{type_page}", "columns"),
        Output(f"datatable-details-{type_page}", "data"),
        Output(f"datatable-details-{type_page}", "selected_rows"),
        Output(f"datatable-details-{type_page}", "active_cell"),
    ],
    [
        Input(f"datatable-{type_page}", "active_cell"),
        State(f"datatable-{type_page}", "data"),
        State(f"range-slider-month-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        State(f"dropdown-inogorodniy-{type_page}", "value"),
        State(f"dropdown-sanction-{type_page}", "value"),
        State(f"dropdown-amount-null-{type_page}", "value"),
        State(f"date-picker-range-input-{type_page}", "start_date"),
        State(f"date-picker-range-input-{type_page}", "end_date"),
        State(f"date-picker-range-treatment-{type_page}", "start_date"),
        State(f"date-picker-range-treatment-{type_page}", "end_date"),
        State(f"dropdown-report-type-{type_page}", "value"),
        State(f"status-selection-mode-{type_page}", "value"),
        State(f"status-group-radio-{type_page}", "value"),
        State(f"status-individual-dropdown-{type_page}", "value"),
        State(f"dropdown-health-group-{type_page}", "value"),
        State(f"dropdown-goals-{type_page}", "value"),
        State(f"dropdown-buildings-{type_page}", "value"),
        State(f"dropdown-profiles-{type_page}", "value"),
    ],
    prevent_initial_call=True
)
def show_details_tab7(active_cell, table_data, selected_months, year, inog, sanc, amt_null,
                     start_input, end_input, start_treat, end_treat, report_type, status_mode, status_group, status_indiv,
                     health_groups, goals, buildings, profiles):
    if not active_cell or not table_data:
        return [], [], [], None
    row = table_data[active_cell["row"]]
    main_diag = row["main_diagnosis_code"]
    # Теперь разрешаем детализацию и по строке "Всего"
    conds = [f"report_year = {int(year)}"]
    if main_diag == "Всего":
        # Собрать все диагнозы из основной таблицы, кроме "Всего"
        diag_list = [row["main_diagnosis_code"] for row in table_data if row["main_diagnosis_code"] != "Всего"]
        if not diag_list:
            return columns, [], [], None
        diag_values = ", ".join(f"'{d}'" for d in diag_list)
        conds.append(f"main_diagnosis_code IN ({diag_values})")
    else:
        conds.append(f"main_diagnosis_code = '{main_diag}'")
    if report_type == "month" and selected_months:
        start, end = selected_months
        conds.append(f"report_month BETWEEN {start} AND {end}")
    if report_type == "initial_input" and start_input and end_input:
        conds.append(f"initial_input_date BETWEEN '{start_input[:10]}' AND '{end_input[:10]}'")
    if report_type == "treatment" and start_treat and end_treat:
        conds.append(f"treatment_end BETWEEN '{start_treat[:10]}' AND '{end_treat[:10]}'")
    if inog == '1':
        conds.append("inogorodniy = FALSE")
    elif inog == '2':
        conds.append("inogorodniy = TRUE")
    if sanc == '1':
        conds.append("(sanctions = '-' OR sanctions IS NULL)")
    elif sanc == '2':
        conds.append("sanctions <> '-'")
    if amt_null == '1':
        conds.append("amount_numeric IS NOT NULL")
    elif amt_null == '2':
        conds.append("amount_numeric IS NULL")
    if status_mode == "group":
        sts = status_groups.get(status_group, [])
    else:
        sts = status_indiv or []
    if sts:
        q = ",".join(f"'{s}'" for s in sts)
        conds.append(f"status IN ({q})")
    if health_groups:
        if "all" in health_groups:
            pass
        elif health_groups == ["with"]:
            conds.append("health_group <> '-'")
        else:
            values = ", ".join(f"'{hg}'" for hg in health_groups)
            conds.append(f"health_group IN ({values})")
    if goals and "all" not in goals:
        values = ", ".join(f"'{g}'" for g in goals)
        conds.append(f"goal IN ({values})")
    if buildings and "all" not in buildings:
        values = ", ".join(f"'{b}'" for b in buildings)
        conds.append(f"building IN ({values})")
    if profiles and "all" not in profiles:
        values = ", ".join(f"'{p}'" for p in profiles)
        conds.append(f"profile IN ({values})")
    where = " AND ".join(conds)
    sql = f'''
        SELECT talon, enp, report_month, report_year, status, goal, patient, birth_date, treatment_start, treatment_end, main_diagnosis_code, additional_diagnosis_codes
        FROM load_data_oms_data
        WHERE {where}
    '''
    df = pd.read_sql_query(text(sql), engine)
    columns = [
        {"name": "Талон", "id": "talon"},
        {"name": "ЕНП", "id": "enp"},
        {"name": "Месяц", "id": "report_month"},
        {"name": "Год", "id": "report_year"},
        {"name": "Статус", "id": "status"},
        {"name": "Цель", "id": "goal"},
        {"name": "Пациент", "id": "patient"},
        {"name": "Дата рождения", "id": "birth_date"},
        {"name": "Начало лечения", "id": "treatment_start"},
        {"name": "Окончание лечения", "id": "treatment_end"},
        {"name": "Основной диагноз", "id": "main_diagnosis_code"},
        {"name": "Доп. диагнозы", "id": "additional_diagnosis_codes"},
    ]
    return columns, df.to_dict("records"), [], None


