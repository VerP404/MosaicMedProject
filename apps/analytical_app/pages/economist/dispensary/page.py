from datetime import datetime
from dash import html, dcc, Input, Output, State, exceptions, dash_table
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_years, filter_status, status_groups, update_buttons, filter_months
)
from apps.analytical_app.pages.economist.dispensary.query import (
    sql_query_oms_dispensary, sql_query_detailed_dispensary
)
from apps.analytical_app.query_executor import engine

type_page = "econ-dispensary-analysis"


def economist_dispensary_analysis():
    return html.Div([
        # Фильтры
        dbc.Card(
            dbc.CardBody([
                dbc.CardHeader("Фильтры"),
                dbc.Row([
                    dbc.Col(update_buttons(type_page), width=2),
                    dbc.Col(filter_years(type_page), width=2),
                    dbc.Col([
                        html.Label("Отчетный месяц:"),
                        filter_months(type_page)
                    ], width=4),
                    dbc.Col([
                        html.Label("Статусы:"),
                        filter_status(type_page)
                    ], width=6),
                ], align="center"),
            ]),
            className="mb-3 shadow-sm"
        ),
        
        # Результаты в вкладках
        dbc.Tabs([
            dbc.Tab(
                label="ОМС",
                tab_id=f"tab-oms-{type_page}",
                children=[
                    dcc.Loading(
                        id=f'loading-oms-{type_page}',
                        type="default",
                        children=html.Div(id=f'result-oms-{type_page}')
                    )
                ]
            ),
            dbc.Tab(
                label="Детализация",
                tab_id=f"tab-detailed-{type_page}",
                children=[
                    dcc.Loading(
                        id=f'loading-detailed-{type_page}',
                        type="default",
                        children=html.Div(id=f'result-detailed-{type_page}')
                    )
                ]
            )
        ], active_tab=f"tab-oms-{type_page}")
    ])


# Callback для переключения между групповым и индивидуальным выбором статусов
@app.callback(
    Output(f'status-group-container-{type_page}', 'style'),
    Output(f'status-individual-container-{type_page}', 'style'),
    Input(f'status-selection-mode-{type_page}', 'value')
)
def toggle_status_selection(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}


# Callback для ОМС таблицы
@app.callback(
    Output(f'result-oms-{type_page}', 'children'),
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     State(f'range-slider-month-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value')]
)
def update_oms_table(n_clicks, year, month_range, status_mode, status_group, status_individual):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    
    if not year or not month_range:
        return html.Div("Выберите год и месяц", className="text-muted")
    
    # Берем первый месяц из диапазона
    month = month_range[0] if isinstance(month_range, list) else month_range
    
    # Определяем статусы
    statuses = (
        status_groups.get(status_group, [])
        if status_mode == 'group' else (status_individual or [])
    )
    
    # Выполняем запрос
    query = sql_query_oms_dispensary(year, month, statuses)
    columns, data = TableUpdater.query_to_df(engine, query)
    
    if not data:
        return html.Div([
            dbc.Alert([
                html.H5("Данные не найдены", className="alert-heading"),
                html.P("По выбранным условиям не найдено ни одной записи.")
            ], color="info")
        ])
    
    return html.Div([
        dash_table.DataTable(
            id=f"table-oms-{type_page}",
            columns=[
                {
                    "name": c["name"] if isinstance(c, dict) else c,
                    "id": c["id"] if isinstance(c, dict) else c
                }
                for c in columns
            ],
            data=data,
            page_size=20,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            style_table={"overflowX": "auto"},
        )
    ])


# Callback для Детализации таблицы
@app.callback(
    Output(f'result-detailed-{type_page}', 'children'),
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     State(f'range-slider-month-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value')]
)
def update_detailed_table(n_clicks, year, month_range, status_mode, status_group, status_individual):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    
    if not year or not month_range:
        return html.Div("Выберите год и месяц", className="text-muted")
    
    # Берем первый месяц из диапазона
    month = month_range[0] if isinstance(month_range, list) else month_range
    
    # Определяем статусы
    statuses = (
        status_groups.get(status_group, [])
        if status_mode == 'group' else (status_individual or [])
    )
    
    # Выполняем запрос
    query = sql_query_detailed_dispensary(year, month, statuses)
    columns, data = TableUpdater.query_to_df(engine, query)
    
    if not data:
        return html.Div([
            dbc.Alert([
                html.H5("Данные не найдены", className="alert-heading"),
                html.P("По выбранным условиям не найдено ни одной записи.")
            ], color="info")
        ])
    
    return html.Div([
        dash_table.DataTable(
            id=f"table-detailed-{type_page}",
            columns=[
                {
                    "name": c["name"] if isinstance(c, dict) else c,
                    "id": c["id"] if isinstance(c, dict) else c
                }
                for c in columns
            ],
            data=data,
            page_size=20,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            style_table={"overflowX": "auto"},
        )
    ])
