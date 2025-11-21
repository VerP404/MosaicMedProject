from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# "Диспансеризация детей"
type_page = 'children'
main_link = 'head/children'
label = 'Диспансеризация детей'

# Сетка Bootstrap: 4 колонки на MD+, единый gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(
            create_card(1, type_page,
                        "Отчет по видам диспансеризации детей",
                        "Все виды диспансеризации детей с разбивкой по целям, корпусам и отделениям"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(2, type_page,
                        "Диспансеризация детей по возрастам",
                        "Все виды диспансеризации детей с разбивкой по возрастам"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(3, type_page,
                        "Список прикрепленных детей",
                        "Список прикрепленных детей с отметками о наличии ПН1"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(4, type_page,
                        "Уникальные дети в ПН",
                        "Уникальные дети в талонах диспансеризации детей"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(5, type_page,
                        "Записаны, но нет ПН1",
                        "Журнал записей vs ПН1 для детей 0–17 лет"),
            className="d-flex"
        ),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
head_children_dd_main = html.Div([
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
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in range(1, 6)],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/pn1",
        2: f"/{main_link}/pn2",
        3: f"/{main_link}/pn3",
        4: f"/{main_link}/pn4",
        5: f"/{main_link}/pn5",
    }
    
    return route_map[report_num]
