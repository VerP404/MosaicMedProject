from dash import html, dcc, Output, Input, dash_table, exceptions, State
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater

from apps.analytical_app.components.filters import filter_status, filter_years, filter_months, \
    get_current_reporting_month, months_labels, status_groups
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.query_executor import engine, get_active_targets

type_page = "tab1-doctor-talon-list"


def sql_query_by_doc(sql_cond, selected_year):
    # Получаем список активных целей
    active_targets = get_active_targets()

    # Формируем динамическую часть с COUNT для каждой цели
    dynamic_columns = ',\n    '.join(
        [f"COUNT(CASE WHEN dlo.goal = '{target}' THEN 1 END) AS \"{target}\"" for target in active_targets]
    )

    # Формируем динамический подсчет для total_talons, как сумма всех целей
    total_talons_sum = ' + '.join(
        [f"COUNT(CASE WHEN dlo.goal = '{target}' THEN 1 END)" for target in active_targets]
    )

    # Полный запрос с фильтрацией по году
    query = f"""
           SELECT
               CONCAT(pp.last_name, ' ', SUBSTR(pp.first_name, 1, 1), '.', SUBSTR(pp.patronymic, 1, 1), '.') AS doctor,
               ob.name AS building,   
               od.name AS department,  
               prof.description AS profile,  
               {total_talons_sum} AS total_talons,
               {dynamic_columns}
           FROM
               data_loader_omsdata dlo
           JOIN
               personnel_doctorrecord pd
               ON SUBSTRING(dlo.doctor, 1, POSITION(' ' IN dlo.doctor) - 1) = pd.doctor_code
           JOIN
               personnel_person pp
               ON pd.person_id = pp.id
           JOIN
               organization_department od
               ON pd.department_id = od.id
           JOIN
               organization_building ob
               ON od.building_id = ob.id
           JOIN
               personnel_profile prof
               ON pd.profile_id = prof.id
           WHERE 
               report_period IN ({sql_cond})
             AND status IN :status_list 
             AND tariff != '0'
             AND dlo.treatment_end LIKE '%{selected_year}%'
           GROUP BY
               pp.last_name, pp.first_name, pp.patronymic, od.name, ob.name, prof.description
           HAVING {total_talons_sum} > 0;
           """
    return query


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
        card_table(f'result-table-{type_page}', "Талоны по врачам", 15),
        dbc.Modal(
            [
                dbc.ModalBody("Данные не найдены. Измените фильтры."),
            ],
            id="no-data-modal",
            is_open=False,  # По умолчанию модальное окно закрыто
        )
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
     Output(f'loading-output-{type_page}', 'children'),
     Output('no-data-modal', 'is_open')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')],
    [State(f'selected-period-{type_page}', 'children'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'dropdown-year-{type_page}', 'value')]
)
def update_table(n_clicks, selected_period, selected_status, selected_year):
    if n_clicks is None or not selected_period or not selected_status or not selected_year:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    selected_status_values = status_groups[selected_status]
    selected_status_tuple = tuple(selected_status_values)

    sql_cond = ', '.join([f"'{period}'" for period in selected_period])

    # Подставляем выбранный год в SQL-запрос
    sql_query = sql_query_by_doc(sql_cond, selected_year)

    bind_params = {
        'status_list': selected_status_tuple
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query, bind_params)
    # Проверяем, есть ли данные
    if len(data) == 0:
        return columns, data, loading_output, True  # Открываем модальное окно
    else:
        return columns, data, loading_output, False  # Модальное окно закрыто
