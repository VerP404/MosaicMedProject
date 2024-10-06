from dash import html, dcc, Output, Input, State, callback_context
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

# Карточки для отчётов
cards = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Сверхподушевое финансирование", className="card-title"),
                    html.P(
                        "Описание отчета по сверхподушевому финансированию, включая анализ текущего состояния.",
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
                    html.H5("Экономический анализ", className="card-title"),
                    html.P(
                        "Анализ текущего экономического состояния учреждения с выводами и рекомендациями.",
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
                    html.H5("Статистический отчет", className="card-title"),
                    html.P(
                        "Подробный отчет с текущими статистическими данными и прогнозами.",
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

# Макет страницы "Экономист" с хлебными крошками
economist_main = html.Div([
    dbc.Breadcrumb(id="economist-breadcrumb", items=[
        {"label": "Экономист", "href": "/economist", "active": True},
    ]),
    html.Hr(),
    html.Div(cards, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


# Callback для навигации и изменения хлебных крошек
@app.callback(
    [Output('url', 'pathname'),
     Output('economist-breadcrumb', 'items')],
    [Input('open-report-1', 'n_clicks'),
     Input('open-report-2', 'n_clicks'),
     Input('open-report-3', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3):
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
        breadcrumb_items.append({"label": "Экономический анализ", "active": True})
        return '/report-2', breadcrumb_items
    elif button_id == 'open-report-3' and open_report_3:
        breadcrumb_items.append({"label": "Статистический отчет", "active": True})
        return '/report-3', breadcrumb_items

    return '/economist', breadcrumb_items
