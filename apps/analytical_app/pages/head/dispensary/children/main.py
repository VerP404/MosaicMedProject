from dash import html, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "children"
main_link = "head/children"  # начало ссылки
label = "Диспансеризация детей"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Отчет по видам диспансеризации детей",
                            "Все виды диспансеризации детей с разбивкой по целям, корпусам и отделениям")),
        dbc.Col(create_card(2, type_page,
                            "Диспансеризация детей по возрастам",
                            "Все виды диспансеризации детей с разбивкой по возрастам")),
    ],
    className="mb-4 align-items-stretch",
)

head_children_dd_main = html.Div([
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
     Input(f'open-report-2-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": label, "href": f"/{main_link}", "active": True}]

    if button_id == f'open-report-1-{type_page}' and open_report_1:
        breadcrumb_items.append({"active": True})
        return f'/{main_link}/pn1', breadcrumb_items
    elif button_id == f'open-report-2-{type_page}' and open_report_2:
        breadcrumb_items.append({"active": True})
        return f'/{main_link}/pn2', breadcrumb_items

    return f'/{main_link}', breadcrumb_items
