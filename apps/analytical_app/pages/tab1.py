from dash import html, dcc, Output, Input, dash_table, exceptions, State
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater

from apps.analytical_app.components.filters import filter_status, filter_years, filter_months, \
    get_current_reporting_month, months_labels, status_groups
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.query_executor import engine

type_page = "tab1-doctor-talon-list"


def sql_query_by_doc(sql_cond):
    return f"""
    select distinct "Корпус Врач"                                                                  as "ФИО Врача",
                "Подразделение"                                                                as "Корпус",
                CASE
                    WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                        substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                    ELSE
                        "Врач (Профиль МП)"
                    END                                                                        AS "Профиль",
                count(*)                                                                       as "Всего",
                SUM(CASE WHEN "Цель" in ('1') THEN 1 ELSE 0 END)                              AS "1",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "3",
                SUM(CASE WHEN "Цель" in ('5') THEN 1 ELSE 0 END)                              AS "5",
                SUM(CASE WHEN "Цель" in ('7') THEN 1 ELSE 0 END)                              AS "7",
                SUM(CASE WHEN "Цель" in ('9') THEN 1 ELSE 0 END)                              AS "9",
                SUM(CASE WHEN "Цель" in ('10') THEN 1 ELSE 0 END)                              AS "10",
                SUM(CASE WHEN "Цель" in ('13') THEN 1 ELSE 0 END)                              AS "13",
                SUM(CASE WHEN "Цель" in ('14') THEN 1 ELSE 0 END)                              AS "14",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "22",
                SUM(CASE WHEN "Цель" in ('30') THEN 1 ELSE 0 END)                              AS "30",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32",
                SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)                              AS "64",
                SUM(CASE WHEN "Цель" in ('140') THEN 1 ELSE 0 END)                              AS "140",
                SUM(CASE WHEN "Цель" in ('301') THEN 1 ELSE 0 END)                             AS "301",
                SUM(CASE WHEN "Цель" in ('305') THEN 1 ELSE 0 END)                              AS "305",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                              AS "307",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                              AS "541",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                              AS "561",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре') THEN 1 ELSE 0 END)              AS "В дс",
                SUM(CASE WHEN "Цель" in ('На дому') THEN 1 ELSE 0 END)                              AS "На дому",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """


def sql_query_by_doc_end_treatment(sql_cond=None):
    return f"""
    select distinct "Корпус Врач"                                                                  as "ФИО Врача",
                "Подразделение"                                                                as "Корпус",
                CASE
                    WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                        substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                    ELSE
                        "Врач (Профиль МП)"
                    END                                                                        AS "Профиль",
                count(*)                                                                       as "Всего",
                SUM(CASE WHEN "Цель" in ('1') THEN 1 ELSE 0 END)                              AS "1",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "3",
                SUM(CASE WHEN "Цель" in ('5') THEN 1 ELSE 0 END)                              AS "5",
                SUM(CASE WHEN "Цель" in ('7') THEN 1 ELSE 0 END)                              AS "7",
                SUM(CASE WHEN "Цель" in ('9') THEN 1 ELSE 0 END)                              AS "9",
                SUM(CASE WHEN "Цель" in ('10') THEN 1 ELSE 0 END)                              AS "10",
                SUM(CASE WHEN "Цель" in ('13') THEN 1 ELSE 0 END)                              AS "13",
                SUM(CASE WHEN "Цель" in ('14') THEN 1 ELSE 0 END)                              AS "14",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "22",
                SUM(CASE WHEN "Цель" in ('30') THEN 1 ELSE 0 END)                              AS "30",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32",
                SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)                              AS "64",
                SUM(CASE WHEN "Цель" in ('140') THEN 1 ELSE 0 END)                              AS "140",
                SUM(CASE WHEN "Цель" in ('301') THEN 1 ELSE 0 END)                             AS "301",
                SUM(CASE WHEN "Цель" in ('305') THEN 1 ELSE 0 END)                              AS "305",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                              AS "307",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                              AS "541",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                              AS "561",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре') THEN 1 ELSE 0 END)              AS "В дс",
                SUM(CASE WHEN "Цель" in ('На дому') THEN 1 ELSE 0 END)                              AS "На дому",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
  AND "Тариф" != '0'
  AND "Статус" IN :status_list
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """


def sql_query_by_doc_end_form(sql_cond=None):
    return f"""
    select distinct "Корпус Врач"                                                                  as "ФИО Врача",
                "Подразделение"                                                                as "Корпус",
                CASE
                    WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                        substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                    ELSE
                        "Врач (Профиль МП)"
                    END                                                                        AS "Профиль",
                count(*)                                                                       as "Всего",
                SUM(CASE WHEN "Цель" in ('1') THEN 1 ELSE 0 END)                              AS "1",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "3",
                SUM(CASE WHEN "Цель" in ('5') THEN 1 ELSE 0 END)                              AS "5",
                SUM(CASE WHEN "Цель" in ('7') THEN 1 ELSE 0 END)                              AS "7",
                SUM(CASE WHEN "Цель" in ('9') THEN 1 ELSE 0 END)                              AS "9",
                SUM(CASE WHEN "Цель" in ('10') THEN 1 ELSE 0 END)                              AS "10",
                SUM(CASE WHEN "Цель" in ('13') THEN 1 ELSE 0 END)                              AS "13",
                SUM(CASE WHEN "Цель" in ('14') THEN 1 ELSE 0 END)                              AS "14",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "22",
                SUM(CASE WHEN "Цель" in ('30') THEN 1 ELSE 0 END)                              AS "30",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32",
                SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)                              AS "64",
                SUM(CASE WHEN "Цель" in ('140') THEN 1 ELSE 0 END)                              AS "140",
                SUM(CASE WHEN "Цель" in ('301') THEN 1 ELSE 0 END)                             AS "301",
                SUM(CASE WHEN "Цель" in ('305') THEN 1 ELSE 0 END)                              AS "305",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                              AS "307",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                              AS "541",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                              AS "561",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре') THEN 1 ELSE 0 END)              AS "В дс",
                SUM(CASE WHEN "Цель" in ('На дому') THEN 1 ELSE 0 END)                              AS "На дому",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
  AND "Тариф" != '0'
  AND "Статус" IN :status_list
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """

tab1_doctor_talon_list = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    filter_status(type_page),  # фильтр по статусам
                                    filter_years(type_page)  # фильтр по годам
                                ]
                            ),
                            dbc.Row(
                                [
                                    filter_months(type_page)  # фильтр по месяцам
                                ]
                            ),
                            html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                            html.Div(id=f'selected-month-{type_page}', className='filters-label'),
                            html.Button('Получить данные', id=f'get-data-button-{type_page}'),
                            dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        card_table(f'result-table-{type_page}', "Талоны по врачам", 15)
    ],
    style={"padding": "0rem"}
)


# Определяем отчетный месяц и выводим его на страницу и в переменную dcc Store
@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


@app.callback(
    Output(f'selected-month-{type_page}', 'children'),
    Input(f'range-slider-month-{type_page}', 'value')
)
def update_selected_month(selected_months):
    if selected_months is None:
        return "Выбранный месяц: Не выбран"

    start_month, end_month = selected_months
    start_month_name = months_labels.get(start_month, 'Неизвестно')
    end_month_name = months_labels.get(end_month, 'Неизвестно')
    if start_month_name == end_month_name:
        return f'Выбранный месяц: {start_month_name}'
    else:
        return f'Выбранный месяц: с {start_month_name} по {end_month_name}'


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [Input(f'range-slider-month-{type_page}', 'value'),
     Input(f'dropdown-year-{type_page}', 'value'),
     Input(f'current-month-name-{type_page}', 'children')]
)
def update_selected_period_list(selected_months_range, selected_year, current_month_name):
    return get_selected_period(selected_months_range, selected_year, current_month_name)


@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'get-data-button-{type_page}', 'n_clicks'),
     State(f'selected-period-{type_page}', 'children'),
     State(f'status-group-radio-{type_page}', 'value')]
)
def update_table(n_clicks, selected_period, selected_status):
    if n_clicks is None or not selected_period or not selected_status:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    selected_status_values = status_groups[selected_status]
    selected_status_tuple = tuple(selected_status_values)

    sql_cond = ', '.join([f"'{period}'" for period in selected_period])
    sql_query = sql_query_by_doc(sql_cond)

    bind_params = {
        'status_list': selected_status_tuple
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query, bind_params)
    return columns, data, loading_output
