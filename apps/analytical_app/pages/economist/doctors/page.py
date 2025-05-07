from dash import html, dcc, Output, Input, exceptions, State
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater

from apps.analytical_app.components.filters import filter_status, filter_years, filter_months, \
    get_current_reporting_month, months_labels, status_groups
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.query_executor import engine, get_active_targets

type_page = "econ-doctors-talon-list"


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


economist_doctors_talon_list = html.Div(
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

        # Обновленный Placeholder без аргумента type
        dbc.Placeholder(id=f'placeholder-{type_page}', style={"height": "300px", "marginTop": "20px"}),

        # Toast для уведомления, если данные не найдены
        dbc.Toast(
            "Данные не найдены. Измените фильтры.",
            id="no-data-toast",
            header="Внимание",
            icon="danger",
            duration=4000,  # 4 секунды
            is_open=False,
            dismissable=True,  # Позволяет пользователю закрыть
            style={"position": "fixed", "top": 60, "right": 50, "width": 350},
        )
    ],
    style={"padding": "0rem"}
)


@app.callback(
    [
        Output(f'status-group-container-{type_page}', 'style'),
        Output(f'status-individual-container-{type_page}', 'style')
    ],
    [Input(f'status-selection-mode-{type_page}', 'value')]
)
def toggle_status_selection_mode(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:  # mode == 'individual'
        return {'display': 'none'}, {'display': 'block'}


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


# Коллбэк для получения данных и управления Placeholder и Toast
@app.callback(
    [Output(f'result-table-{type_page}', 'columns'),
     Output(f'result-table-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children'),
     Output(f'placeholder-{type_page}', 'style'),  # Управляем отображением Placeholder
     Output('no-data-toast', 'is_open')],  # Управляем отображением Toast
    [Input(f'get-data-button-{type_page}', 'n_clicks')],
    [State(f'selected-period-{type_page}', 'children'),
     State(f'dropdown-year-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value'),
     ]
)
def update_table(n_clicks, selected_period, selected_year, status_mode, selected_status_group,
                 selected_individual_statuses):
    if n_clicks is None or not selected_period or not selected_year:
        raise exceptions.PreventUpdate

    # Показываем Placeholder во время загрузки данных
    placeholder_style = {"height": "300px", "marginTop": "20px"}
    loading_output = html.Div([dcc.Loading(type="default")])

    # Определяем список статусов в зависимости от выбранного режима
    if status_mode == 'group':
        selected_status_values = status_groups[selected_status_group]
    else:  # status_mode == 'individual'
        selected_status_values = selected_individual_statuses if selected_individual_statuses else []
    selected_status_tuple = tuple(selected_status_values)

    sql_cond = ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)])

    sql_query = sql_query_by_doc(sql_cond, selected_year)

    bind_params = {
        'status_list': selected_status_tuple
    }
    columns, data = TableUpdater.query_to_df(engine, sql_query, bind_params)

    # Если данные не найдены, открываем Toast и сохраняем Placeholder
    if len(data) == 0:
        return columns, data, loading_output, placeholder_style, True

    # Если данные найдены, скрываем Placeholder и Toast
    placeholder_style = {"display": "none"}
    return columns, data, loading_output, placeholder_style, False
