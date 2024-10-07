from dash import html, Output, Input, callback_context
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
                        "Открыть", color="success", className="mt-auto", id=f"open-report-1-{type_page}"
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
                        "Открыть", color="warning", className="mt-auto", id=f"open-report-2-{type_page}"
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
                        "Открыть", color="danger", className="mt-auto", id=f"open-report-3-{type_page}"
                    ),
                ]
            )
        ),
    ]
)

# Макет страницы "Экономист" с хлебными крошками
head_main = html.Div([
    dbc.Breadcrumb(id=f"economist-breadcrumb-{type_page}", items=[
        {"label": "Заведующий", "href": "/head", "active": True},
    ]),
    html.Hr(),
    # Добавляем оба набора карточек на страницу
    html.Div(cards_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


# Callback для навигации и изменения хлебных крошек
@app.callback(
    [Output(f'url-{type_page}', 'pathname'),
     Output(f'economist-breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-1-{type_page}', 'n_clicks'),
     Input(f'open-report-2-{type_page}', 'n_clicks'),
     Input(f'open-report-3-{type_page}', 'n_clicks'),
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

    if button_id == f'open-report-1-{type_page}' and open_report_1:
        breadcrumb_items.append({"label": "Сверхподушевое финансирование", "active": True})
        return '/economist/svpod', breadcrumb_items
    elif button_id == f'open-report-2-{type_page}' and open_report_2:
        breadcrumb_items.append({"label": "По врачам", "active": True})
        return '/economist/doctors', breadcrumb_items
    elif button_id == f'open-report-3-{type_page}' and open_report_3:
        breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
        return '/economist/disp_by_ages', breadcrumb_items

    return '/economist', breadcrumb_items
