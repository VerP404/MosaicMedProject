from dash import html, Output, Input, callback_context
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

# Карточки для отчётов
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
                        "Открыть", color="success", className="mt-auto", id="open-report-1"
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
                        "Открыть", color="warning", className="mt-auto", id="open-report-2"
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
                        "Открыть", color="danger", className="mt-auto", id="open-report-3"
                    ),
                ]
            )
        ),
    ]
)

# Второй набор карточек (с уникальными идентификаторами)
cards_2 = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Финансовый отчет", className="card-title"),
                    html.P(
                        "Отчет по выполнению финансовых целей с указанием сумм и метрик.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="success", className="mt-auto", id="open-report-4"  # Уникальный id
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Целевые метрики", className="card-title"),
                    html.P(
                        "Анализ выставления целей по метрикам.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="warning", className="mt-auto", id="open-report-5"  # Уникальный id
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Отчет по диспансеризации", className="card-title"),
                    html.P(
                        "Развернутый отчет по диспансеризации по возрастным группам.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id="open-report-6"  # Уникальный id
                    ),
                ]
            )
        ),
    ]
)

# Макет страницы "Экономист" с хлебными крошками
economist_main = html.Div([
    dbc.Breadcrumb(id="economist-breadcrumb", items=[
        {"label": "Экономист", "href": "/economist", "active": True},
    ]),
    html.Hr(),
    # Добавляем оба набора карточек на страницу
    html.Div(cards_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
    html.Div(cards_2, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


# Callback для навигации и изменения хлебных крошек
@app.callback(
    [Output('url', 'pathname'),
     Output('economist-breadcrumb', 'items')],
    [Input('open-report-1', 'n_clicks'),
     Input('open-report-2', 'n_clicks'),
     Input('open-report-3', 'n_clicks'),
     Input('open-report-4', 'n_clicks'),
     Input('open-report-5', 'n_clicks'),
     Input('open-report-6', 'n_clicks')
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4, open_report_5, open_report_6):
    ctx = callback_context
    if not ctx.triggered:
        return '/economist', [{"label": "Экономист", "href": "/economist", "active": True}]
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": "Экономист", "href": "/economist"}]

    if button_id == 'open-report-1' and open_report_1:
        breadcrumb_items.append({"label": "Сверхподушевое финансирование", "active": True})
        return '/economist/svpod', breadcrumb_items
    elif button_id == 'open-report-2' and open_report_2:
        breadcrumb_items.append({"label": "По врачам", "active": True})
        return '/economist/doctors', breadcrumb_items
    elif button_id == 'open-report-3' and open_report_3:
        breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
        return '/economist/disp_by_ages', breadcrumb_items

    elif button_id == 'open-report-4' and open_report_4:
        breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
        return '/economist/disp_by_ages', breadcrumb_items
    elif button_id == 'open-report-5' and open_report_5:
        breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
        return '/economist/disp_by_ages', breadcrumb_items
    elif button_id == 'open-report-6' and open_report_6:
        breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
        return '/economist/disp_by_ages', breadcrumb_items
    return '/economist', breadcrumb_items
