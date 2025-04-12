from datetime import datetime
from dash import dcc, html, dash_table, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine
from apps.analytical_app.components.filters import get_available_buildings, get_available_departments, \
    get_available_doctors, get_departments_by_doctor, parse_doctor_ids, get_available_profiles, get_doctor_details

type_page = "error_log"

# Форма фильтров с обновленными компонентами
filters = html.Div([
    dbc.Row([
        dbc.Col(html.Div("Выберите год:"), width=2),
        dbc.Col(
            dcc.Dropdown(
                id=f"dropdown-year-{type_page}",
                options=[{"label": str(y), "value": str(y)} for y in range(2023, datetime.now().year + 1)],
                value=str(datetime.now().year)
            ),
            width=2
        ),
        dbc.Col(
            dbc.Button("Применить фильтр", id=f"update-button-{type_page}", color="primary"),
            width=2
        )
    ], className="mb-2"),
    dbc.Row([
        dbc.Col(html.Div("Корпус:"), width=2),
        dbc.Col(
            dcc.Dropdown(
                id=f"dropdown-building-{type_page}",
                options=get_available_buildings(),
                multi=True,
                placeholder="Все корпуса"
            ),
            width=3
        ),
        dbc.Col(html.Div("Отделение:"), width=2),
        dbc.Col(
            dcc.Dropdown(
                id=f"dropdown-department-{type_page}",
                options=[],
                multi=True,
                placeholder="Все отделения"
            ),
            width=3
        )
    ], className="mb-2"),
    dbc.Row([
        dbc.Col(html.Div("Профиль:"), width=2),
        dbc.Col(
            dcc.Dropdown(
                id=f"dropdown-profile-{type_page}",
                options=[],
                multi=True,
                placeholder="Все профили"
            ),
            width=3
        ),
        dbc.Col(html.Div("Врач:"), width=2),
        dbc.Col(
            dcc.Dropdown(
                id=f"dropdown-doctor-{type_page}",
                options=[],
                multi=True,
                placeholder="Все врачи"
            ),
            width=3
        )
    ], className="mb-2"),
    html.Div(id=f"selected-filters-{type_page}", style={"margin": "10px"})
], style={"padding": "15px"})

# Основной layout страницы error_log
layout_error_log = html.Div([
    filters,
    dcc.Loading(id=f"loading-output-{type_page}", type="default"),
    dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row([
                    dbc.Col(html.H5("Отчёт по ошибкам", className="mb-0"), width="auto"),
                    dbc.Col(
                        html.Div(
                            id=f"last-updated-error_log-{type_page}",
                            style={"textAlign": "right", "fontWeight": "normal"}
                        ),
                        width=True
                    )
                ], align="center", justify="between")
            ),
            dbc.CardBody(
                dbc.Tabs([
                    dbc.Tab(
                        dash_table.DataTable(
                            id=f"summary-table-{type_page}",
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'},
                            export_format="xlsx",
                            page_size=15,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            style_header={'fontWeight': 'bold'}
                        ),
                        label="Сводный"
                    ),
                    dbc.Tab(
                        dash_table.DataTable(
                            id=f"detailed-table-{type_page}",
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'},
                            export_format="xlsx",
                            page_size=15,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            style_header={'fontWeight': 'bold'}
                        ),
                        label="Детальный"
                    )
                ])
            )
        ],
        className="mb-3"
    ),
    html.Div(id=f"report-status-{type_page}", style={"color": "red", "padding": "15px"})
])

# Callback для обновления фильтров врачей и отделений
@app.callback(
    [
        Output(f"dropdown-department-{type_page}", "options"),
        Output(f"dropdown-profile-{type_page}", "options"),
        Output(f"dropdown-doctor-{type_page}", "options"),
        Output(f"selected-filters-{type_page}", "children")
    ],
    [
        Input(f"dropdown-building-{type_page}", "value"),
        Input(f"dropdown-department-{type_page}", "value"),
        Input(f"dropdown-profile-{type_page}", "value"),
        Input(f"dropdown-doctor-{type_page}", "value"),
        Input(f"dropdown-year-{type_page}", "value")
    ]
)
def update_filters(building_ids, department_ids, profile_ids, doctor_ids, selected_year):
    # Получаем отделения в зависимости от выбранных корпусов или врачей
    if doctor_ids:
        departments = get_departments_by_doctor(doctor_ids)
    elif building_ids:
        departments = get_available_departments(building_ids)
    else:
        departments = get_available_departments()

    # Получаем профили в зависимости от выбранных корпусов или отделений
    profiles = get_available_profiles(building_ids, department_ids)

    # Получаем врачей в зависимости от выбранных фильтров
    doctors = get_available_doctors(building_ids, department_ids, profile_ids, selected_year)

    # Отображаем выбранных врачей
    selected_doctors_info = []
    if doctor_ids:
        parsed_ids = parse_doctor_ids(doctor_ids)
        if parsed_ids:
            doctor_details = get_doctor_details(parsed_ids)
            selected_doctors_info = [
                html.Div([
                    html.Ul([
                        html.Li([html.Strong("Код: "), details['code']]),
                        html.Li([html.Strong("Врач: "), details['doctor_name']]),
                        html.Li([html.Strong("Специальность: "), details['specialty']]),
                        html.Li([html.Strong("Отделение: "), details['department']]),
                        html.Li([html.Strong("Корпус: "), details['building']]),
                    ], style={"list-style-type": "none", "margin": 0, "padding": 0})
                ], style={"border": "1px solid #ccc", "padding": "10px", "margin": "10px", "border-radius": "5px"})
                for details in doctor_details
            ]

    return departments, profiles, doctors, selected_doctors_info

# Callback для обновления таблиц и даты последнего обновления
@app.callback(
    [
        Output(f"summary-table-{type_page}", "data"),
        Output(f"summary-table-{type_page}", "columns"),
        Output(f"detailed-table-{type_page}", "data"),
        Output(f"detailed-table-{type_page}", "columns"),
        Output(f"last-updated-error_log-{type_page}", "children"),
        Output(f"report-status-{type_page}", "children")
    ],
    Input(f"update-button-{type_page}", "n_clicks"),
    [
        State(f"dropdown-year-{type_page}", "value"),
        State(f"dropdown-doctor-{type_page}", "value"),
        State(f"dropdown-building-{type_page}", "value"),
        State(f"dropdown-department-{type_page}", "value"),
        State(f"dropdown-profile-{type_page}", "value")
    ]
)
def update_error_log(n_clicks, selected_year, selected_doctor, selected_building, selected_department, selected_profile):
    if not n_clicks:
        raise exceptions.PreventUpdate

    # Приведение значений фильтров к нужному виду
    selected_doctor_ids = parse_doctor_ids(selected_doctor) if selected_doctor else []
    building_ids = selected_building if selected_building else []
    department_ids = selected_department if selected_department else []
    profile_ids = selected_profile if selected_profile else []

    try:
        # --- Сводный запрос ---
        summary_sql = f"""
        SELECT 
            err.doctor AS "Врач",
            err.goal AS "Цель",
            COUNT(DISTINCT err.talon) AS "Количество талонов",
            SUM(CASE WHEN err.is_fixed THEN 1 ELSE 0 END) AS "Исправлено",
            SUM(CASE WHEN NOT err.is_fixed THEN 1 ELSE 0 END) AS "Не исправлено"
        FROM load_data_error_log_talon err
        LEFT JOIN personnel_doctorrecord d ON substring(err.doctor from 1 for position(' ' in err.doctor) - 1) = d.doctor_code
        LEFT JOIN organization_department dept ON dept.id = d.department_id
        LEFT JOIN organization_building bld ON bld.id = dept.building_id
        LEFT JOIN personnel_profile profile ON profile.id = d.profile_id
        WHERE SUBSTRING(err.treatment_end FROM 7 FOR 4) = :selected_year
            {"AND d.id IN (" + ",".join(map(str, selected_doctor_ids)) + ")" if selected_doctor_ids else ""}
            {"AND bld.id IN (" + ",".join(map(str, building_ids)) + ")" if building_ids else ""}
            {"AND dept.id IN (" + ",".join(map(str, department_ids)) + ")" if department_ids else ""}
            {"AND profile.id IN (" + ",".join(map(str, profile_ids)) + ")" if profile_ids else ""}
        GROUP BY err.doctor, err.goal
        """
        with engine.connect() as conn:
            df_summary = pd.read_sql(text(summary_sql), conn, params={"selected_year": selected_year})

        summary_data = df_summary.to_dict('records')
        summary_columns = [{"name": col, "id": col} for col in df_summary.columns]

        # --- Детальный запрос ---
        detailed_sql = f"""
        SELECT 
            err.doctor AS "Врач",
            CASE WHEN err.is_fixed IS TRUE THEN 'Да' ELSE 'Нет' END AS "Исправлено",
            err.patient AS "Пациент",
            err.birth_date AS "Дата рождения",
            err.enp AS "ЕНП",
            err.treatment_start AS "Начало лечения",
            err.treatment_end AS "Окончание лечения",
            err.goal AS "Цель",
            err.talon_status AS "Статус",
            err.tfoms_error_text AS "Текст ошибки ТФОМС",
            bld.name AS "Корпус",
            dept.name AS "Отделение",
            profile.description AS "Профиль"
        FROM load_data_error_log_talon err
        LEFT JOIN personnel_doctorrecord d ON substring(err.doctor from 1 for position(' ' in err.doctor) - 1) = d.doctor_code
        LEFT JOIN organization_department dept ON dept.id = d.department_id
        LEFT JOIN organization_building bld ON bld.id = dept.building_id
        LEFT JOIN personnel_profile profile ON profile.id = d.profile_id
        WHERE SUBSTRING(err.treatment_end FROM 7 FOR 4) = :selected_year
            {"AND d.id IN (" + ",".join(map(str, selected_doctor_ids)) + ")" if selected_doctor_ids else ""}
            {"AND bld.id IN (" + ",".join(map(str, building_ids)) + ")" if building_ids else ""}
            {"AND dept.id IN (" + ",".join(map(str, department_ids)) + ")" if department_ids else ""}
            {"AND profile.id IN (" + ",".join(map(str, profile_ids)) + ")" if profile_ids else ""}
        ORDER BY err.doctor, err.treatment_end
        """
        with engine.connect() as conn:
            df_detailed = pd.read_sql(text(detailed_sql), conn, params={"selected_year": selected_year})
        detailed_data = df_detailed.to_dict('records')
        detailed_columns = [{"name": col, "id": col} for col in df_detailed.columns]

        # --- Получаем дату последнего обновления из load_data_error_log_talon ---
        with engine.connect() as conn:
            row = conn.execute(text("SELECT MAX(updated_at) FROM load_data_error_log_talon")).fetchone()
        last_updated = row[0].strftime('%d.%m.%Y %H:%M') if row and row[0] else "Нет данных"

        return summary_data, summary_columns, detailed_data, detailed_columns, last_updated, ""
    except Exception as e:
        error_msg = f"Ошибка при выполнении запроса: {str(e)}"
        return [], [], [], [], "", error_msg