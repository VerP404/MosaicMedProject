from dash import html, dcc, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

type_page = "statistic"
# Карточки для отчётов
cards_1 = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Отчет Шараповой по ДН", className="card-title"),
                    html.P(
                        "Еженедельный отчет Шараповой по ДН с формированием по дате создания талонов.",
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
                    html.H5("- Диспансеризация детей", className="card-title"),
                    html.P(
                        "-",
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
                    html.H5("- Диспансерное наблюдение", className="card-title"),
                    html.P(
                        "-",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id=f"open-report-3-{type_page}"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("- Диспансерное наблюдение работающих", className="card-title"),
                    html.P(
                        "-",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id=f"open-report-4-{type_page}"
                    ),
                ]
            )
        ),
    ]
)

statistic_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": "Статистик", "href": "/statistic", "active": True},
    ]),
    html.Hr(),
    html.Div(cards_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
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

    breadcrumb_items = [{"label": "Статистик", "href": "/statistic"}]

    if button_id.startswith("open-report-") and "statistic" in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"label": "Отчет Шараповой по ДН", "active": True})
            return '/statistic/statistic-sharapova', breadcrumb_items
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            breadcrumb_items.append({"label": "По врачам", "active": True})
            return '/statistic/doctors', breadcrumb_items
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
            return '/statistic/disp_by_ages', breadcrumb_items
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            breadcrumb_items.append({"label": "Диспансерное наблюдение работающих", "active": True})
            return '/statistic/dn_job', breadcrumb_items

    return '/statistic', breadcrumb_items
