from dash import html, dcc, Input, Output, no_update, callback_context
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

type_page = 'economist'
cards_1 = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Сверхподушевое финансирование", className="card-title"),
                    html.P(
                        "Отчет по фактическому выполнению сверхподушевого финансирования с указанием "
                        "колическтва талонов и стоимости",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="success", className="mt-auto", id=f"open-report-1-{type_page}"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("По врачам", className="card-title"),
                    html.P(
                        "Анализ выставления целей по врачам.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="warning", className="mt-auto", id=f"open-report-2-{type_page}"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Диспансеризация по возрастам", className="card-title"),
                    html.P(
                        "Отчет по всем видам диспансеризации по возрастам с разбивкой по полу и возрасту.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id=f"open-report-3-{type_page}"
                    ),
                ]
            )
        ),
    ]
)

cards_2 = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Стационары", className="card-title"),
                    html.P(
                        "Отчет по КСГ в разбивке по корпусам.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="success", className="mt-auto", id=f"open-report-4-economist"
                    ),
                ]
            )
        ),
    ]
)

# Макет страницы "Экономист" с хлебными крошками
economist_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": "Экономист", "href": "/economist", "active": True},
    ]),
    html.Hr(),
    html.Div(cards_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
    html.Div(cards_2, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items'),
     ],
    [Input(f'open-report-1-{type_page}', 'n_clicks'),
     Input(f'open-report-2-{type_page}', 'n_clicks'),
     Input(f'open-report-3-{type_page}', 'n_clicks'),
     Input(f'open-report-4-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": "Экономист", "href": "/economist"}]

    if button_id.startswith("open-report-") and "economist" in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"label": "Сверхподушевое финансирование", "active": True})
            return '/economist/svpod', breadcrumb_items
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            breadcrumb_items.append({"label": "По врачам", "active": True})
            return '/economist/doctors', breadcrumb_items
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
            return '/economist/disp_by_ages', breadcrumb_items
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            breadcrumb_items.append({"label": "Стационары", "active": True})
            return '/economist/stationary', breadcrumb_items

    return '/economist', breadcrumb_items
