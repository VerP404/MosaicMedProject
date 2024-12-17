from dash import html, callback_context, no_update, Output, Input
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
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    html.Div(cards_row_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items'),
     ],
    [Input(f'open-report-1-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": label, "href": f"/{main_link}", "active": True}]

    if button_id.startswith("open-report-") and main_link in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"label": "Не госпитализированные", "active": True})
            return f'/{main_link}/not_hospitalized', breadcrumb_items
    return f'/{main_link}', breadcrumb_items
