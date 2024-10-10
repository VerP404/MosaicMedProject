from dash import html, dcc, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "web_oms"
main_link = "web_oms"  # начало ссылки
label = "WEB.ОМС"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "По целям",
                            "Анализ ОМС: По целям")),
        dbc.Col(create_card(2, type_page,
                            "Специальность по целям",
                            "Анализ ОМС: Специальность по целям")),
        dbc.Col(create_card(3, type_page,
                            "Корпуса по цели",
                            "Анализ ОМС: Корпуса по цели")),
        dbc.Col(create_card(4, type_page,
                            "Корпус и специальность по целям",
                            "Анализ ОМС: Корпус и специальность по целям")),
    ],
    className="mb-4 align-items-stretch",
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page,
                            "Цели и диагнозы по корпусам",
                            "Анализ ОМС: Цели и диагнозы по корпусам")),
        dbc.Col(create_card(6, type_page,
                            "Список пациентов и их диагнозы в текущем году",
                            "Анализ ОМС: Список пациентов и их диагнозы"))
    ],
    className="mb-4 align-items-stretch",
)
web_oms_main = html.Div([
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
     Input(f'open-report-6-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4, open_report_5, open_report_6):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": label, "href": f"/{main_link}", "active": True}]

    if button_id.startswith("open-report-") and f'{main_link}' in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/web_oms_rep1', breadcrumb_items
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/web_oms_rep2', breadcrumb_items
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/web_oms_rep3', breadcrumb_items
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/web_oms_rep4', breadcrumb_items
        elif button_id == f'open-report-5-{type_page}' and open_report_5:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/web_oms_rep5', breadcrumb_items
        elif button_id == f'open-report-6-{type_page}' and open_report_6:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/web_oms_rep6', breadcrumb_items

    return f'/{main_link}', breadcrumb_items
