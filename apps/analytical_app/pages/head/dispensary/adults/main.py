from dash import html, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "adults"
main_link = "adults"  # начало ссылки
label = "Диспансеризация взрослых"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "По дате формирования карты",
                            "По дате формирования карты")),
        dbc.Col(create_card(2, type_page,
                            "По отчетному периоду",
                            "По отчетному периоду")),
        dbc.Col(create_card(3, type_page,
                            "По возрастам ДВ4 и ОПВ",
                            "По возрастам ДВ4 и ОПВ")),
        dbc.Col(create_card(4, type_page,
                            "По возрастам ДВ4",
                            "По возрастам ДВ4")),
    ],
    className="mb-4 align-items-stretch",
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page,
                            "По возрастам ОПВ",
                            "По возрастам ОПВ")),
        dbc.Col(create_card(8, type_page,
                            "ДВ4 с группировкой по стоимости",
                            "ДВ4 с группировкой по стоимости")),
    ],
    className="mb-4 align-items-stretch",
)

head_adults_dd_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    html.Div(cards_row_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
    html.Div(cards_row_2, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items'),
     ],
    [Input(f'open-report-1-{type_page}', 'n_clicks'),
     Input(f'open-report-2-{type_page}', 'n_clicks'),
     Input(f'open-report-3-{type_page}', 'n_clicks'),
     Input(f'open-report-4-{type_page}', 'n_clicks'),
     Input(f'open-report-5-{type_page}', 'n_clicks'),
     Input(f'open-report-8-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4, open_report_5, open_report_8):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": label, "href": f"/{main_link}", "active": True}]

    if button_id.startswith("open-report-") and f'{main_link}' in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dv1', breadcrumb_items
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dv2', breadcrumb_items
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dv3', breadcrumb_items
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dv4', breadcrumb_items
        elif button_id == f'open-report-5-{type_page}' and open_report_5:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dv5', breadcrumb_items
        elif button_id == f'open-report-8-{type_page}' and open_report_8:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dv8', breadcrumb_items

    return f'/{main_link}', breadcrumb_items
