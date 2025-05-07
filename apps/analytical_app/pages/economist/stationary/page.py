from dash import Output, Input, exceptions, State
from sqlalchemy import text

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import *
from apps.analytical_app.components.toast import toast
from apps.analytical_app.elements import card_table, get_selected_period
from apps.analytical_app.app import app
from apps.analytical_app.pages.economist.stationary.query import sql_query_stac
from apps.analytical_app.query_executor import engine

type_page = "econ-stac"

cel_groups = {
    'В дневном стационаре': ['В дневном стационаре'],
    'На дому': ['На дому'],
    'Стационарно': ['Стационарно'],
}

economist_stationary = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            html.Button(id=f'page-load-{type_page}', style={'display': 'none'}),
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
                            html.Div(
                                [
                                    dbc.Label("Выберите корпус:"),
                                    dbc.Checklist(
                                        id=f"building-checklist-{type_page}",
                                        inline=True,
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    dbc.Label("Выберите тип стационара:"),
                                    dbc.Checklist(
                                        options=[{'label': group, 'value': group} for group in cel_groups.keys()],
                                        value=['Дневные'],
                                        id=f"checklist-input-{type_page}",
                                        inline=True,
                                    ),
                                ]
                            ),
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
        card_table(f'result-table-{type_page}', "Отчет по КСГ и суммам в стационарах", 15),
        toast(type_page)  # уведомление, если данные не найдены

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


@app.callback(
    [
        Output(f'building-checklist-{type_page}', 'options'),
        Output(f'building-checklist-{type_page}', 'value')
    ],
    [Input(f'page-load-{type_page}', 'n_clicks')]
)
def update_building_options_and_values(n_clicks):
    with engine.connect() as connection:
        building_query = connection.execute(text("SELECT DISTINCT name_kvazar FROM organization_building"))
        building_names = [row[0] for row in building_query.fetchall()]

    building_options = [{"label": building, "value": building} for building in building_names]

    # Возвращаем все корпуса в value по умолчанию
    return building_options, [building['value'] for building in building_options]


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
     Output(f'no-data-toast-{type_page}', 'is_open')],
    [Input(f'get-data-button-{type_page}', 'n_clicks')],
    [State(f'selected-period-{type_page}', 'children'),

     State(f'checklist-input-{type_page}', 'value'),
     State(f'dropdown-year-{type_page}', 'value'),
     State(f'building-checklist-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value'),
     ]  # Добавляем состояние для выбранных корпусов
)
def update_table(n_clicks, selected_period, selected_type_dv, selected_year, selected_buildings, status_mode, selected_status_group, selected_individual_statuses):
    if n_clicks is None or not selected_period or not selected_type_dv:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    # Определяем список статусов в зависимости от выбранного режима
    if status_mode == 'group':
        selected_status_values = status_groups[selected_status_group]
    else:  # status_mode == 'individual'
        selected_status_values = selected_individual_statuses if selected_individual_statuses else []
    selected_status_tuple = tuple(selected_status_values)
    selected_type_dv_tuple = tuple(selected_type_dv)

    # Передаем также selected_buildings в функцию sql_query_disp_dv4
    sql_cond = ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)])
    sql_query = sql_query_stac(sql_cond, selected_year, selected_buildings)

    bind_params = {
        'status_list': selected_status_tuple,
        'dv': selected_type_dv_tuple,
        'building_list': tuple(selected_buildings)
    }

    columns, data = TableUpdater.query_to_df(engine, sql_query, bind_params)
    if len(data) == 0:
        return columns, data, loading_output, True
    return columns, data, loading_output, False
