from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'web_oms'
main_link = 'web_oms'
label = 'WEB.ОМС'

# Сетка Bootstrap для карточек
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page, "По целям", "Анализ ОМС: По целям")),
        dbc.Col(create_card(2, type_page, "Специальность по целям", "Анализ ОМС: Специальность по целям")),
        dbc.Col(create_card(3, type_page, "Корпуса по цели", "Анализ ОМС: Корпуса по цели")),
        dbc.Col(create_card(4, type_page, "Корпус и специальность по целям", "Анализ ОМС: Корпус и специальность по целям")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page, "Цели и диагнозы по корпусам", "Анализ ОМС: Цели и диагнозы по корпусам")),
        dbc.Col(create_card(6, type_page, "Список пациентов и их диагнозы в текущем году", "Анализ ОМС: Список пациентов и их диагнозы")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
web_oms_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
    cards_row_2,
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in range(1, 7)],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/web_oms_rep1",
        2: f"/{main_link}/web_oms_rep2",
        3: f"/{main_link}/web_oms_rep3",
        4: f"/{main_link}/web_oms_rep4",
        5: f"/{main_link}/web_oms_rep5",
        6: f"/{main_link}/web_oms_rep6"
    }
    
    return route_map[report_num]
