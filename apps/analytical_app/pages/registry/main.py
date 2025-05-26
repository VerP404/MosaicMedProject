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
    ],
    className="mb-4 align-items-stretch",
)

registry_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    html.Div(cards_row_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in [1]],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/not_hospitalized"
    }
    
    return route_map[report_num]
