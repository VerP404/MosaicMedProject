from datetime import datetime
from dash import html, Output, Input, State, dcc, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_years, filter_report_type, filter_sanction,
    filter_amount_null, filter_months, date_picker, get_current_reporting_month,
    update_buttons, filter_status, status_groups, filter_inogorod
)
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.economist.doctor_stac.query import (
    sql_query_doc_stac_v_ds, sql_query_doc_stac, sql_query_doc_stac_na_d
)
from apps.analytical_app.query_executor import engine

type_page = "economist-doctor-stac"

economist_doctor_stac = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                    dbc.Col(filter_report_type(type_page), width=2),
                                    dbc.Col(filter_inogorod(type_page), width=2),
                                    dbc.Col(filter_sanction(type_page), width=2),
                                    dbc.Col(filter_amount_null(type_page), width=2),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(filter_months(type_page), width=12),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Label("Выберите дату", id=f'label-date-{type_page}',
                                                                   style={'font-weight': 'bold', 'display': 'none'}),
                                                        width="auto"
                                                    ),
                                                    dbc.Col(date_picker(f'input-{type_page}'), width=4,
                                                            id=f'col-input-{type_page}', style={'display': 'none'}),
                                                    dbc.Col(date_picker(f'treatment-{type_page}'), width=4,
                                                            id=f'col-treatment-{type_page}', style={'display': 'none'}),
                                                ],
                                                align="center",
                                                style={"display": "flex", "align-items": "center",
                                                       "margin-bottom": "10px"}
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            # Добавляем фильтр по статусу
                            dbc.Row(
                                [
                                    dbc.Col(filter_status(type_page), width=6)
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=9),
                                    dbc.Col(html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                                     style={'display': 'none'}), width=3)
                                ]
                            ),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "В дневном стационаре"),
        card_table(f'result-table2-{type_page}', "На дому"),
        card_table(f'result-table3-{type_page}', "Стационарно"),
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


# Остальной callback для переключения режима фильтрации по статусу уже определён в filter_status
@app.callback(
    [
        Output(f'range-slider-month-{type_page}', 'style'),
        Output(f'date-picker-range-input-{type_page}', 'style'),
        Output(f'date-picker-range-treatment-{type_page}', 'style')
    ],
    [Input(f'dropdown-report-type-{type_page}', 'value')]
)
def toggle_filters(report_type):
    if report_type == 'month':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    elif report_type == 'initial_input':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}


@app.callback(
    [
        Output(f'col-input-{type_page}', 'style'),
        Output(f'col-treatment-{type_page}', 'style'),
    ],
    [Input(f'dropdown-report-type-{type_page}', 'value')]
)
def toggle_datepickers(report_type):
    if report_type == 'initial_input':
        return {'display': 'block'}, {'display': 'none'}
    elif report_type == 'treatment':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


@app.callback(
    Output(f'label-date-{type_page}', 'style'),
    [
        Input(f'dropdown-report-type-{type_page}', 'value'),
        Input(f'date-picker-range-input-{type_page}', 'start_date'),
        Input(f'date-picker-range-input-{type_page}', 'end_date'),
        Input(f'date-picker-range-treatment-{type_page}', 'start_date'),
        Input(f'date-picker-range-treatment-{type_page}', 'end_date')
    ]
)
def toggle_label_visibility(report_type, start_date_input, end_date_input, start_date_treatment, end_date_treatment):
    if report_type in ['initial_input', 'treatment'] and (
            start_date_input or end_date_input or start_date_treatment or end_date_treatment):
        return {'display': 'block'}
    return {'display': 'none'}


@app.callback(
    Output(f'current-month-name-{type_page}', 'children'),
    Input('date-interval', 'n_intervals')
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_name


@app.callback(
    Output(f'selected-period-{type_page}', 'children'),
    [Input(f'range-slider-month-{type_page}', 'value'),
     Input(f'dropdown-year-{type_page}', 'value'),
     Input(f'current-month-name-{type_page}', 'children')]
)
def update_selected_period_list(selected_months_range, selected_year, current_month_name):
    return selected_months_range


# Основной callback обновления таблиц
@app.callback(
    [
        Output(f'result-table1-{type_page}', 'columns'),
        Output(f'result-table1-{type_page}', 'data'),
        Output(f'result-table2-{type_page}', 'columns'),
        Output(f'result-table2-{type_page}', 'data'),
        Output(f'result-table3-{type_page}', 'columns'),
        Output(f'result-table3-{type_page}', 'data'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [
        State(f'range-slider-month-{type_page}', 'value'),
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'dropdown-inogorodniy-{type_page}', 'value'),
        State(f'dropdown-sanction-{type_page}', 'value'),
        State(f'dropdown-amount-null-{type_page}', 'value'),
        State(f'date-picker-range-input-{type_page}', 'start_date'),
        State(f'date-picker-range-input-{type_page}', 'end_date'),
        State(f'date-picker-range-treatment-{type_page}', 'start_date'),
        State(f'date-picker-range-treatment-{type_page}', 'end_date'),
        State(f'dropdown-report-type-{type_page}', 'value'),
        # Добавляем состояния фильтра по статусу:
        State(f'status-selection-mode-{type_page}', 'value'),
        State(f'status-group-radio-{type_page}', 'value'),
        State(f'status-individual-dropdown-{type_page}', 'value'),
    ]
)
def update_table(n_clicks, selected_period, selected_year, inogorodniy, sanction,
                 amount_null, start_date_input, end_date_input,
                 start_date_treatment, end_date_treatment, report_type,
                 status_mode, selected_status_group, selected_individual_statuses):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])

    # Определяем список статусов в зависимости от выбранного режима
    if status_mode == 'group':
        selected_status_values = status_groups[selected_status_group]
    else:
        selected_status_values = selected_individual_statuses if selected_individual_statuses else []
    selected_status_tuple = tuple(selected_status_values)

    # Определяем используемый период
    start_date_input_formatted, end_date_input_formatted = None, None
    start_date_treatment_formatted, end_date_treatment_formatted = None, None

    if report_type == 'month':
        pass
    elif report_type == 'initial_input':
        selected_period = (1, 12)
        start_date_input_formatted = datetime.strptime(start_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date_input_formatted = datetime.strptime(end_date_input.split('T')[0], '%Y-%m-%d').strftime('%d-%m-%Y')
    elif report_type == 'treatment':
        selected_period = (1, 12)
        start_date_treatment_formatted = datetime.strptime(start_date_treatment.split('T')[0], '%Y-%m-%d').strftime(
            '%d-%m-%Y')
        end_date_treatment_formatted = datetime.strptime(end_date_treatment.split('T')[0], '%Y-%m-%d').strftime(
            '%d-%m-%Y')
    # Формируем строку для фильтрации по месяцам
    sql_cond = ', '.join([str(month) for month in range(selected_period[0], selected_period[1] + 1)])
    # Подготавливаем параметры для bind-переменных, включая status_list
    bind_params = {
        'status_list': selected_status_tuple
    }

    # Выполняем запросы для трёх таблиц
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_doc_stac_v_ds(
            selected_year,
            sql_cond,
            inogorodniy,
            sanction,
            amount_null,
            building=None,
            profile=None,
            doctor=None,
            input_start=start_date_input_formatted,
            input_end=end_date_input_formatted,
            treatment_start=start_date_treatment_formatted,
            treatment_end=end_date_treatment_formatted
        ),
        bind_params
    )

    columns2, data2 = TableUpdater.query_to_df(
        engine,
        sql_query_doc_stac_na_d(
            selected_year,
            sql_cond,
            inogorodniy,
            sanction,
            amount_null,
            building=None,
            profile=None,
            doctor=None,
            input_start=start_date_input_formatted,
            input_end=end_date_input_formatted,
            treatment_start=start_date_treatment_formatted,
            treatment_end=end_date_treatment_formatted
        ),
        bind_params
    )
    columns3, data3 = TableUpdater.query_to_df(
        engine,
        sql_query_doc_stac(
            selected_year,
            sql_cond,
            inogorodniy,
            sanction,
            amount_null,
            building=None,
            profile=None,
            doctor=None,
            input_start=start_date_input_formatted,
            input_end=end_date_input_formatted,
            treatment_start=start_date_treatment_formatted,
            treatment_end=end_date_treatment_formatted
        ),
        bind_params
    )
    return columns1, data1, columns2, data2, columns3, data3, loading_output
