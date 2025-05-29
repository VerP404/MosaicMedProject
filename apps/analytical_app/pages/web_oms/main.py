from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'web_oms'
main_link = 'web_oms'
label = 'WEB.ОМС'

# Сетка Bootstrap: 4 колонки на MD+, общий gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Отчет 1 - По целям",
                            "Отчет по целям диспансеризации")),
        dbc.Col(create_card(2, type_page,
                            "Отчет 2 - Специальность по целям",
                            "Отчет по специальностям и целям диспансеризации")),
        dbc.Col(create_card(3, type_page,
                            "Отчет 3 - Цель по корпусам",
                            "Отчет по целям диспансеризации по корпусам")),
        dbc.Col(create_card(4, type_page,
                            "Отчет 4 - Корпус и специальность по целям",
                            "Отчет по корпусам, специальностям и целям диспансеризации")),
        dbc.Col(create_card(5, type_page,
                            "Отчет 5 - Цели и диагнозы по корпусам",
                            "Отчет по целям, диагнозам и корпусам диспансеризации")),
        dbc.Col(create_card(6, type_page,
                            "Отчет 6 - Список пациентов и их диагнозы в текущем году",
                            "Список пациентов и их диагнозы в текущем году")),
        dbc.Col(create_card(7, type_page,
                            "Отчет 7 - Уникальные пациенты и талоны по диагнозам",
                            "Статистика по уникальным пациентам по диагнозам")),
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
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in range(1, 8)],
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
        6: f"/{main_link}/web_oms_rep6",
        7: f"/{main_link}/web_oms_rep7"
    }
    
    return route_map[report_num]
