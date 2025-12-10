from datetime import datetime

from dash import html, dcc, Output, Input, State, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    update_buttons,
    filter_years,
    filter_months,
    filter_status,
    status_groups,
    get_current_reporting_month,
)
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine
from sqlalchemy import text


# Уникальный идентификатор страницы: используйте в id элементов
type_page = "tab15-da"


adults_dv15 = html.Div(
    [
        # Блок фильтров
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=2),
                                    dbc.Col(filter_months(type_page), width=8),
                                ],
                                align="center",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div([
                                            html.Label("Наличие записи", style={"font-weight": "bold"}),
                                            dbc.RadioItems(
                                                id=f"appointment-filter-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Да", "value": "yes"},
                                                    {"label": "Нет", "value": "no"},
                                                ],
                                                value="all",
                                                inline=True,
                                                className="mt-1"
                                            )
                                        ]),
                                        width=6,
                                    ),
                                ]
                            ),
                            dbc.Card(
                                dbc.Row(
                                    [
                                        filter_status(type_page),
                                    ]
                                ),
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

                ),
                width=12,
            ),
            style={"margin": "0 auto", "padding": "0rem"},
        ),

        # Таблица с результатами
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dcc.Loading(id=f"loading-list-{type_page}", type="default"),
                            card_table(f"result-table-list-{type_page}", "Проверка карт", page_size=10)
                        ]
                    )
                ),
                width=12
            )
        )
    ],
    style={"padding": "0rem"},
)


# ——— Колбэки вспомогательные ———
@app.callback(
    [Output(f'status-group-container-{type_page}', 'style'),
     Output(f'status-individual-container-{type_page}', 'style')],
    [Input(f'status-selection-mode-{type_page}', 'value')]
)
def toggle_status_selection_mode(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}


@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval-main', 'n_intervals')
)
def update_current_month(_):
    _, name = get_current_reporting_month()
    return name


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [Input(f'range-slider-month-{type_page}', 'value'),
     Input(f'dropdown-year-{type_page}', 'value')]
)
def show_period(months, year):
    if not months or not year:
        return ""
    return f"Год: {year}, месяцы: {months}"


# ——— Основной колбэк: строим таблицу ———
@app.callback(
    [
        Output(f'result-table-list-{type_page}', 'columns'),
        Output(f'result-table-list-{type_page}', 'data'),
        Output(f'loading-list-{type_page}', 'children'),
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [
        State(f'range-slider-month-{type_page}', 'value'),
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'appointment-filter-{type_page}', 'value'),
        State(f'status-selection-mode-{type_page}', 'value'),
        State(f'status-group-radio-{type_page}', 'value'),
        State(f'status-individual-dropdown-{type_page}', 'value'),
    ]
)
def build_table(n_clicks, months_range, year, appointment_filter,
                status_mode, status_group, status_individual):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    # Параметры
    if not months_range:
        months_range = [1, 12]
    m1, m2 = int(months_range[0]), int(months_range[1])

    # Выбранные статусы
    if status_mode == 'group':
        statuses = status_groups.get(status_group, ['2', '3'])
    else:
        statuses = status_individual or ['2', '3']

    statuses_list = ", ".join(f"'{s}'" for s in statuses)

    # Базовые условия (общие для всех)
    where_common = f"""
        WHERE
            oms.report_year = {int(year)}
            AND oms.report_month BETWEEN {m1} AND {m2}
            AND oms.goal IN ('ДВ4','ДВ2','ОПВ','УД1','УД2')
            AND oms.status IN ({statuses_list})
    """

    # Условие для отправленного ЭМД
    emd_condition = """
        AND emd.sending_status = 'Документ успешно зарегистрирован'
    """

    # SQL запрос с JOIN к журналу обращений
    sql_list = f"""
        WITH appointments_with_dates AS (
            SELECT
                regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
                COALESCE(
                    CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' 
                         THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
                    CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}' 
                         THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI') END,
                    CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' 
                         THEN to_date(acceptance_date, 'DD.MM.YYYY')::timestamp END,
                    CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' 
                         THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
                    CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' 
                         THEN to_date(record_date, 'DD.MM.YYYY')::timestamp END
                ) AS appointment_ts
            FROM load_data_journal_appeals
            WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
        ),
        oms_with_parsed_dates AS (
            SELECT
                oms.talon,
                oms.source_id,
                oms.report_month,
                oms.report_year,
                oms.status,
                oms.goal,
                oms.patient,
                oms.birth_date,
                oms.treatment_start,
                oms.treatment_end,
                oms.enp,
                oms.building,
                oms.doctor_code,
                oms.doctor,
                regexp_replace(oms.enp, '\\D', '', 'g') AS enp_norm,
                CASE 
                    WHEN oms.treatment_end IS NOT NULL THEN
                        CASE 
                            WHEN oms.treatment_end::text ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' 
                                 THEN to_date(oms.treatment_end::text, 'YYYY-MM-DD')
                            WHEN oms.treatment_end::text ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' 
                                 THEN to_date(oms.treatment_end::text, 'DD.MM.YYYY')
                            WHEN oms.treatment_end::text ~ '^[0-9]{{8}}$' 
                                 THEN to_date(oms.treatment_end::text, 'YYYYMMDD')
                            ELSE NULL
                        END
                    ELSE NULL
                END AS treatment_end_date_parsed
            FROM load_data_oms_data oms
            {where_common}
        ),
        oms_with_emd AS (
            SELECT
                oms.talon,
                oms.source_id,
                oms.report_month,
                oms.report_year,
                oms.status,
                oms.goal,
                oms.patient,
                oms.birth_date,
                oms.treatment_start,
                oms.treatment_end,
                oms.enp,
                oms.building,
                oms.doctor_code,
                oms.doctor,
                oms.enp_norm,
                oms.treatment_end_date_parsed,
                emd.sending_status
            FROM oms_with_parsed_dates oms
            LEFT JOIN load_data_emd emd
                ON oms.source_id = emd.original_epmz_id
                AND emd.document_type = 'Эпикриз по результатам диспансеризации/профилактического медицинского осмотра'
            WHERE emd.sending_status = 'Документ успешно зарегистрирован'
        ),
        appointments_filtered_by_treatment_end AS (
            SELECT
                oms.enp_norm,
                oms.talon,
                oms.source_id,
                MAX(app.appointment_ts::date) AS last_appointment_date
            FROM oms_with_emd oms
            LEFT JOIN appointments_with_dates app
                ON oms.enp_norm = app.enp_norm
                AND app.appointment_ts IS NOT NULL
                AND EXTRACT(YEAR FROM app.appointment_ts) = {int(year)}
                AND (
                    oms.treatment_end_date_parsed IS NULL 
                    OR app.appointment_ts::date <= oms.treatment_end_date_parsed
                )
            GROUP BY oms.enp_norm, oms.talon, oms.source_id
        ),
        oms_data_with_appointments AS (
            SELECT
                oms.talon,
                oms.source_id,
                oms.report_month,
                oms.report_year,
                oms.status,
                oms.goal,
                oms.patient,
                oms.birth_date,
                oms.treatment_start,
                oms.treatment_end,
                oms.enp,
                oms.building,
                oms.doctor_code,
                oms.doctor,
                oms.sending_status,
                app.last_appointment_date,
                CASE 
                    WHEN app.last_appointment_date IS NOT NULL 
                    THEN 'Да'
                    ELSE 'Нет'
                END AS has_appointment
            FROM oms_with_emd oms
            LEFT JOIN appointments_filtered_by_treatment_end app
                ON oms.enp_norm = app.enp_norm
                AND oms.talon = app.talon
                AND oms.source_id = app.source_id
        )
        SELECT
            has_appointment AS "Запись",
            CASE 
                WHEN last_appointment_date IS NOT NULL 
                THEN to_char(last_appointment_date, 'DD.MM.YYYY')
                ELSE ''
            END AS "Дата последней",
            talon AS "Талон",
            source_id AS "ID источника",
            report_month AS "Месяц",
            report_year AS "Год",
            status AS "Статус",
            goal AS "Цель",
            patient AS "Пациент",
            birth_date AS "Дата рождения",
            treatment_start AS "Начало лечения",
            treatment_end AS "Окончание лечения",
            enp AS "ЕНП",
            building AS "Корпус",
            doctor_code AS "Код врача",
            doctor AS "Врач"
        FROM oms_data_with_appointments
        WHERE 1=1
    """

    # Применяем фильтр по наличию записи
    if appointment_filter == "yes":
        sql_list += " AND has_appointment = 'Да'"
    elif appointment_filter == "no":
        sql_list += " AND has_appointment = 'Нет'"

    sql_list += "\n        ORDER BY building, doctor, report_month, talon"

    columns_list, data_list = TableUpdater.query_to_df(engine, sql_list)

    loading_dummy = html.Div([dcc.Loading(type="default")])

    return columns_list, data_list, loading_dummy

