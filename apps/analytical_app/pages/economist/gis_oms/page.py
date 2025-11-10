from dash import html, Output, Input, State, exceptions, dcc, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_months,
    filter_status,
    update_buttons,
    status_groups,
    months_sql_labels,
    months_labels,
)
from apps.analytical_app.pages.economist.gis_oms.query import (
    sql_query_gis_oms_research,
    sql_query_gis_oms_ambulatory,
    sql_query_gis_oms_stationary
)
from apps.analytical_app.query_executor import engine

type_page = "gis-oms"


def economist_gis_oms_def():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                dbc.CardHeader([
                    html.H5("Фильтры", className="mb-0 fw-bold")
                ], className="bg-primary text-white"),
                
                dbc.Row([
                    dbc.Col(
                        dcc.Loading(
                            id=f'loading-button-{type_page}',
                            type="circle",
                            children=html.Div(update_buttons(type_page))
                        ), width=1
                    ),
                    dbc.Col([
                        dbc.Label("Год:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id=f'dropdown-year-{type_page}',
                            options=[{'label': str(year), 'value': year} for year in range(2023, datetime.now().year + 1)],
                            value=datetime.now().year,
                            clearable=False,
                            style={"width": "100%"}
                        )
                    ], width=1),
                    dbc.Col(filter_status(type_page, default_status_group='Оплаченные (3)'), width=10),
                ], align="end", className="mb-3 mt-3"),
                
                dbc.Row([
                    dbc.Col(filter_months(type_page), width=12),
                ], className="mb-3"),
                html.Div(id=f'selected-period-{type_page}', className='filters-label', style={'display': 'none'}),
            ]),
            style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)", "border-radius": "10px"}
        ),
        
        dbc.Tabs([
            dbc.Tab(
                label="Исследования",
                tab_id="tab-research",
                children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.H6("Исследования", className="fw-bold mb-3"),
                            dcc.Loading(
                                id=f'loading-research-{type_page}',
                                type='default',
                                children=dash_table.DataTable(
                                    id=f'result-table-research-{type_page}',
                                    columns=[],
                                    data=[],
                                    export_format='xlsx',
                                    export_headers='display',
                                    page_size=20,
                                    filter_action='native',
                                    sort_action='native',
                                    sort_mode='multi',
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'minWidth': '0px',
                                        'maxWidth': '180px',
                                        'whiteSpace': 'normal'
                                    }
                                )
                            )
                        ]),
                        className="mt-0"
                    ),
                ]
            ),
            dbc.Tab(
                label="Амбулаторная помощь",
                tab_id="tab-ambulatory",
                children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.H6("Амбулаторная помощь", className="fw-bold mb-3"),
                            dcc.Loading(
                                id=f'loading-ambulatory-{type_page}',
                                type='default',
                                children=dash_table.DataTable(
                                    id=f'result-table-ambulatory-{type_page}',
                                    columns=[],
                                    data=[],
                                    export_format='xlsx',
                                    export_headers='display',
                                    page_size=20,
                                    filter_action='native',
                                    sort_action='native',
                                    sort_mode='multi',
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'minWidth': '0px',
                                        'maxWidth': '180px',
                                        'whiteSpace': 'normal'
                                    }
                                )
                            )
                        ]),
                        className="mt-0"
                    ),
                ]
            ),
            dbc.Tab(
                label="Стационары",
                tab_id="tab-stationary",
                children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.H6("Стационары", className="fw-bold mb-3"),
                            dcc.Loading(
                                id=f'loading-stationary-{type_page}',
                                type='default',
                                children=dash_table.DataTable(
                                    id=f'result-table-stationary-{type_page}',
                                    columns=[],
                                    data=[],
                                    export_format='xlsx',
                                    export_headers='display',
                                    page_size=20,
                                    filter_action='native',
                                    sort_action='native',
                                    sort_mode='multi',
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'minWidth': '0px',
                                        'maxWidth': '180px',
                                        'whiteSpace': 'normal'
                                    }
                                )
                            )
                        ]),
                        className="mt-0"
                    ),
                ]
            ),
        ], id=f'tabs-{type_page}', active_tab="tab-research", className="mt-3"),
    ], style={"padding": "0rem"})


# Callback для переключения режима выбора статусов
@app.callback(
    [
        Output(f'status-group-container-{type_page}', 'style'),
        Output(f'status-individual-container-{type_page}', 'style')
    ],
    [Input(f'status-selection-mode-{type_page}', 'value')]
)
def toggle_status_selection_mode(mode):
    if mode == 'group':
        return {'display': 'block', "margin-bottom": "1rem"}, {'display': 'none', "margin-bottom": "1rem"}
    else:  # mode == 'individual'
        return {'display': 'none', "margin-bottom": "1rem"}, {'display': 'block', "margin-bottom": "1rem"}


# Callback для исследований
@app.callback(
    [Output(f'result-table-research-{type_page}', 'columns'),
     Output(f'result-table-research-{type_page}', 'data')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     State(f'range-slider-month-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value')]
)
def update_table_research(n_clicks, selected_year, selected_months, status_mode, selected_status_group, selected_individual_statuses):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    
    if not selected_year:
        return [], []
    
    if not selected_months:
        return [], []
    
    try:
        # Получаем названия месяцев
        start_month, end_month = map(int, selected_months)
        month_names = []
        for m in range(start_month, end_month + 1):
            if m in months_sql_labels:
                month_names.append(f"{months_sql_labels[m]} {selected_year}")
            if m in months_labels:
                month_names.append(f"{months_labels[m]} {selected_year}")
        month_names = list(dict.fromkeys(month_names))
        if not month_names:
            month_names = [f"{label} {selected_year}" for label in months_sql_labels.values()]
        
        # Получаем список статусов в зависимости от выбранного режима
        status_list = None
        if status_mode == 'group':
            if selected_status_group and selected_status_group in status_groups:
                status_list = status_groups[selected_status_group]
        else:  # mode == 'individual'
            status_list = selected_individual_statuses if selected_individual_statuses else None
        
        # Формируем SQL-запрос
        sql_query = sql_query_gis_oms_research(month_names, selected_year, status_list)
        
        # Выполняем запрос
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        return columns, data
    except Exception as e:
        return [], []


# Callback для амбулаторной помощи
@app.callback(
    [Output(f'result-table-ambulatory-{type_page}', 'columns'),
     Output(f'result-table-ambulatory-{type_page}', 'data')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     State(f'range-slider-month-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value')]
)
def update_table_ambulatory(n_clicks, selected_year, selected_months, status_mode, selected_status_group, selected_individual_statuses):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    
    if not selected_year:
        return [], []
    
    if not selected_months:
        return [], []
    
    try:
        # Получаем названия месяцев
        start_month, end_month = map(int, selected_months)
        month_names = []
        for m in range(start_month, end_month + 1):
            if m in months_sql_labels:
                month_names.append(f"{months_sql_labels[m]} {selected_year}")
            if m in months_labels:
                month_names.append(f"{months_labels[m]} {selected_year}")
        month_names = list(dict.fromkeys(month_names))
        if not month_names:
            month_names = [f"{label} {selected_year}" for label in months_sql_labels.values()]
        
        # Получаем список статусов в зависимости от выбранного режима
        status_list = None
        if status_mode == 'group':
            if selected_status_group and selected_status_group in status_groups:
                status_list = status_groups[selected_status_group]
        else:  # mode == 'individual'
            status_list = selected_individual_statuses if selected_individual_statuses else None
        
        # Формируем SQL-запрос
        sql_query = sql_query_gis_oms_ambulatory(month_names, selected_year, status_list)
        
        # Выполняем запрос
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        return columns, data
    except Exception as e:
        return [], []


# Callback для стационаров
@app.callback(
    [Output(f'result-table-stationary-{type_page}', 'columns'),
     Output(f'result-table-stationary-{type_page}', 'data')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     State(f'range-slider-month-{type_page}', 'value'),
     State(f'status-selection-mode-{type_page}', 'value'),
     State(f'status-group-radio-{type_page}', 'value'),
     State(f'status-individual-dropdown-{type_page}', 'value')]
)
def update_table_stationary(n_clicks, selected_year, selected_months, status_mode, selected_status_group, selected_individual_statuses):
    if n_clicks is None:
        raise exceptions.PreventUpdate
    
    if not selected_year:
        return [], []
    
    if not selected_months:
        return [], []
    
    try:
        # Получаем названия месяцев
        start_month, end_month = map(int, selected_months)
        month_names = []
        for m in range(start_month, end_month + 1):
            if m in months_sql_labels:
                month_names.append(f"{months_sql_labels[m]} {selected_year}")
            if m in months_labels:
                month_names.append(f"{months_labels[m]} {selected_year}")
        month_names = list(dict.fromkeys(month_names))
        if not month_names:
            month_names = [f"{label} {selected_year}" for label in months_sql_labels.values()]
        
        # Получаем список статусов в зависимости от выбранного режима
        status_list = None
        if status_mode == 'group':
            if selected_status_group and selected_status_group in status_groups:
                status_list = status_groups[selected_status_group]
        else:  # mode == 'individual'
            status_list = selected_individual_statuses if selected_individual_statuses else None
        
        # Формируем SQL-запрос
        sql_query = sql_query_gis_oms_stationary(month_names, selected_year, status_list)
        
        # Выполняем запрос
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        return columns, data
    except Exception as e:
        return [], []


# Экспорт функции
economist_gis_oms = economist_gis_oms_def()

