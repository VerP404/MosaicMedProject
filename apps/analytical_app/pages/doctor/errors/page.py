from datetime import datetime
from dash import dcc, html, dash_table, Output, Input, State, exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine

# При необходимости можно импортировать функции для формирования списка докторов, корпусов и отделений,
# например, из apps.analytical_app.components.filters

type_page = "error_log"

# Форма фильтров
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
        dbc.Col(html.Div("Врач:"), width=2),
        dbc.Col(
            dcc.Dropdown(id=f"dropdown-doctor-{type_page}", multi=True, placeholder="Все врачи"),
            width=3
        ),
        dbc.Col(
            dbc.Button("Применить фильтр", id=f"update-button-{type_page}", color="primary"),
            width=3
        )
    ], className="mb-2"),
    dbc.Row([
        dbc.Col(html.Div("Корпус:"), width=2),
        dbc.Col(
            dcc.Dropdown(id=f"dropdown-building-{type_page}", multi=True, placeholder="Все корпуса"),
            width=3
        ),
        dbc.Col(html.Div("Отделение:"), width=2),
        dbc.Col(
            dcc.Dropdown(id=f"dropdown-department-{type_page}", multi=True, placeholder="Все отделения"),
            width=3
        )
    ], className="mb-2")
], style={"padding": "15px"})

# Таблица с результатами – два таба: "Сводный" и "Детальный"
tabs = dbc.Card(
    [
        dbc.CardHeader("Отчёт по ошибкам"),
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
)

layout_error_log = html.Div([
    filters,
    dcc.Loading(id=f"loading-output-{type_page}", type="default"),
    tabs,
    html.Div(id=f"report-status-{type_page}", style={"color": "red", "padding": "15px"})
])


@app.callback(
    [
        Output(f"summary-table-{type_page}", "data"),
        Output(f"summary-table-{type_page}", "columns"),
        Output(f"detailed-table-{type_page}", "data"),
        Output(f"detailed-table-{type_page}", "columns"),
        Output(f"report-status-{type_page}", "children")
    ],
    Input(f"update-button-{type_page}", "n_clicks"),
    [
        State(f"dropdown-year-{type_page}", "value"),
        State(f"dropdown-doctor-{type_page}", "value"),
        State(f"dropdown-building-{type_page}", "value"),
        State(f"dropdown-department-{type_page}", "value")
    ]
)
def update_error_log(n_clicks, selected_year, selected_doctor, selected_building, selected_department):
    if not n_clicks:
        raise exceptions.PreventUpdate

    # Приведение значений фильтров к нужному виду
    # Например, преобразуем списки в корректное представление для SQL
    selected_doctor_ids = selected_doctor if selected_doctor else []
    building_ids = selected_building if selected_building else []
    department_ids = selected_department if selected_department else []

    try:
        # --- Сводный запрос ---
        # Группировка по врачу и цели, подсчёт количества талонов (у талона может быть несколько ошибок)
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
        WHERE SUBSTRING(err.treatment_end FROM 7 FOR 4) = :selected_year
            {"AND err.doctor IN (" + ",".join(f"'{doc}'" for doc in selected_doctor_ids) + ")" if selected_doctor_ids else ""}
            {"AND bld.id IN (" + ",".join(map(str, building_ids)) + ")" if building_ids else ""}
            {"AND dept.id IN (" + ",".join(map(str, department_ids)) + ")" if department_ids else ""}
        GROUP BY err.doctor, err.goal
        """
        with engine.connect() as conn:
            df_summary = pd.read_sql(text(summary_sql), conn, params={"selected_year": selected_year})

        summary_data = df_summary.to_dict('records')
        summary_columns = [{"name": col, "id": col} for col in df_summary.columns]

        # --- Детальный запрос ---
        # Выборка всех ошибок с дополнительными данными по корпусу и отделению
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
            dept.name AS "Отделение"
        FROM load_data_error_log_talon err
        LEFT JOIN personnel_doctorrecord d ON substring(err.doctor from 1 for position(' ' in err.doctor) - 1) = d.doctor_code
        LEFT JOIN organization_department dept ON dept.id = d.department_id
        LEFT JOIN organization_building bld ON bld.id = dept.building_id
        WHERE SUBSTRING(err.treatment_end FROM 7 FOR 4) = :selected_year
            {"AND err.doctor IN (" + ",".join(f"'{doc}'" for doc in selected_doctor_ids) + ")" if selected_doctor_ids else ""}
            {"AND bld.id IN (" + ",".join(map(str, building_ids)) + ")" if building_ids else ""}
            {"AND dept.id IN (" + ",".join(map(str, department_ids)) + ")" if department_ids else ""}
        ORDER BY err.doctor, err.treatment_end
        """
        with engine.connect() as conn:
            df_detailed = pd.read_sql(text(detailed_sql), conn, params={"selected_year": selected_year})

        detailed_data = df_detailed.to_dict('records')
        detailed_columns = [{"name": col, "id": col} for col in df_detailed.columns]

        return summary_data, summary_columns, detailed_data, detailed_columns, ""
    except Exception as e:
        error_msg = f"Ошибка при выполнении запроса: {str(e)}"
        return [], [], [], [], error_msg
