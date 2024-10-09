from dash import html, dcc, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

type_page = "head"
# Карточки для отчётов
cards_1 = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Диспансеризация взрослых", className="card-title"),
                    html.P(
                        "Диспансеризация взрослых",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="success", className="mt-auto", id=f"open-report-1-head"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Диспансеризация детей", className="card-title"),
                    html.P(
                        "Диспансеризация детей.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="warning", className="mt-auto", id=f"open-report-2-head"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Диспансерное наблюдение", className="card-title"),
                    html.P(
                        "Диспансерное наблюдение.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id=f"open-report-3-head"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Диспансерное наблюдение работающих", className="card-title"),
                    html.P(
                        "Анализ не прикрепленных пациентов, внесенных в ИСЗЛ как проходивших диспансерное "
                        "наблюдение на основании договора заключенного с работодателем",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id=f"open-report-4-head"
                    ),
                ]
            )
        ),
    ]
)

head_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-head", items=[
        {"label": "Заведующий", "href": "/head", "active": True},
    ]),
    html.Hr(),
    html.Div(cards_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('breadcrumb-head', 'items'),
     ],
    [Input(f'open-report-1-head', 'n_clicks'),
     Input(f'open-report-2-head', 'n_clicks'),
     Input(f'open-report-3-head', 'n_clicks'),
     Input(f'open-report-4-head', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": "Заведующий", "href": "/head"}]

    if button_id.startswith("open-report-") and "head" in button_id:
        if button_id == f'open-report-1-head' and open_report_1:
            breadcrumb_items.append({"label": "Сверхподушевое финансирование", "active": True})
            return '/head/svpod', breadcrumb_items
        elif button_id == f'open-report-2-head' and open_report_2:
            breadcrumb_items.append({"label": "По врачам", "active": True})
            return '/head/doctors', breadcrumb_items
        elif button_id == f'open-report-3-head' and open_report_3:
            breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
            return '/head/disp_by_ages', breadcrumb_items
        elif button_id == f'open-report-4-head' and open_report_4:
            breadcrumb_items.append({"label": "Диспансерное наблюдение работающих", "active": True})
            return '/head/dn_job', breadcrumb_items

    return '/head', breadcrumb_items
