from dash import html, dcc, Input, Output, State, exceptions
import dash_bootstrap_components as dbc
from datetime import datetime
from sqlalchemy import text
from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, filter_inogorod, filter_sanction, filter_amount_null, \
    update_buttons, status_groups, filter_status
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms
from apps.analytical_app.pages.head.doctors.query import sql_query_doctors_goal
from apps.analytical_app.query_executor import engine

# Страница и SQL для отчёта по врачам (doctors_goal)
type_page = "doctors_goal"

# Получаем список уникальных целей для выпадающего списка
with engine.connect() as conn:
    result = conn.execute(text("SELECT DISTINCT goal FROM data_loader_omsdata ORDER BY goal"))
    _goal_rows = result.fetchall()
goal_options = [
    {'label': row[0], 'value': row[0]}
    for row in _goal_rows if row[0] is not None and row[0] != '-'
]
# Разметка страницы
layout_doctors_goal = html.Div([
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dbc.CardHeader("Фильтры"),
                    # Первая строка
                    dbc.Row([
                        dbc.Col(update_buttons(type_page), width=2),
                        dbc.Col(filter_years(type_page), width=2),
                        dbc.Col(filter_inogorod(type_page), width=2),
                        dbc.Col(filter_sanction(type_page), width=2),
                        dbc.Col(filter_amount_null(type_page), width=2),
                        dbc.Col(
                            dcc.Dropdown(
                                id=f'dropdown-goal-{type_page}',
                                options=goal_options,
                                multi=True,
                                placeholder="Цели"
                            ),
                            width=2
                        )
                    ], align="center", className="mb-3"),
                    # Статусы во второй строке
                    dbc.Row([
                        dbc.Col(filter_status(type_page), width=6)
                    ])
                ]),
                style={"padding": "1rem", "margin-bottom": "1rem"}
            ),
            width=12
        )
    ),
    dcc.Loading(id=f'loading-{type_page}', type='default'),
    card_table(f'result-table-{type_page}', "По врачам"),
], style={"padding": "0rem"})


# Callback переключения режима выбора статусов
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
    else:
        return {'display': 'none'}, {'display': 'block'}

# Callback обновления отчёта по врачам
@app.callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'loading-{type_page}', 'children')
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'dropdown-inogorodniy-{type_page}', 'value'),
        State(f'dropdown-sanction-{type_page}', 'value'),
        State(f'dropdown-amount-null-{type_page}', 'value'),
        State(f'dropdown-goal-{type_page}', 'value'),
        State(f'status-selection-mode-{type_page}', 'value'),
        State(f'status-group-radio-{type_page}', 'value'),
        State(f'status-individual-dropdown-{type_page}', 'value')
    ]
)
def update_table_doctors_goal(
    n_clicks, selected_year, inogorodniy, sanction, amount_null,
    goals, status_mode, status_group, individual_statuses
):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    # Определяем список статусов
    if status_mode == 'group':
        status_list = status_groups.get(status_group, [])
    else:
        status_list = individual_statuses or []

    # Все месяцы
    months_placeholder = ', '.join(str(m) for m in range(1, 13))

    # Запрос и обновление таблицы
    columns, data = TableUpdater.query_to_df(
        engine,
        sql_query_doctors_goal(
            selected_year,
            months_placeholder,
            inogorodniy,
            sanction,
            amount_null,
            goals,
            status_list
        )
    )

    return columns, data, None
