from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "registry"
main_link = "registry"  # начало ссылки
label = "Реестры"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Реестр не госпитализированных",
                            "Пациенты не госпитализированные в стационарах.")),
        dbc.Col(create_card(2, type_page,
                            "Анализ записанных на прием",
                            "Анализ пересечений между списком ЕНП и обращениями пациентов.")),
        dbc.Col(create_card(3, type_page,
                            "Анализ школ здоровья",
                            "Отслеживание плановых явок пациентов в школах здоровья.")),
    ],
    className="row-cols-1 row-cols-md-3 g-4 mb-4 align-items-stretch",
)

cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(4, type_page,
                            "Журнал заказов анализов",
                            "Дашборд по выгрузке из журнала заказов анализов.")),
    ],
    className="row-cols-1 row-cols-md-3 g-4 mb-4 align-items-stretch",
)

registry_main = html.Div([
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
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in [1, 2, 3, 4]],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/not_hospitalized",
        2: f"/{main_link}/appointment_analysis",
        3: f"/{main_link}/health_schools",
        4: f"/{main_link}/analysis_orders",
    }
    
    return route_map[report_num]
