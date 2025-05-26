from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# "Репродуктивное здоровье"
type_page = 'reproductive'
main_link = 'head/reproductive'
label = 'Репродуктивное здоровье'

# Bootstrap-сетка: 4 колонки на MD+, единый gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(
            create_card(1, type_page,
                        "Отчет по видам диспансеризации",
                        "Все виды диспансеризации репродуктивного здоровья с разбивкой по целям, корпусам и отделениям"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(2, type_page,
                        "Списки пациентов репродуктивного здоровья",
                        "Списки пациентов для анализа и планирования диспансеризации репродуктивного здоровья"),
            className="d-flex"
        ),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
head_reproductive_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in [1, 2]],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/dr1",
        2: f"/{main_link}/dr2"
    }
    
    return route_map[report_num]
