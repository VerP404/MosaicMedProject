from dash import html, Input, Output, no_update, callback_context
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = 'economist'
main_link = "economist"  # начало ссылки
label = "Экономист"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Показатели: выполнение по месяцам",
                            "Формирует отчет по выбранным показателям выполнения по месяцам с планами.")),
        dbc.Col(create_card(2, type_page,
                            "По врачам",
                            "Анализ выставления целей по врачам.")),
        dbc.Col(create_card(3, type_page,
                            "Диспансеризация по возрастам",
                            "Отчет по всем видам диспансеризации по возрастам с разбивкой по полу и возрасту.")),
        dbc.Col(create_card(4, type_page,
                            "Стационары",
                            "Отчет по КСГ в разбивке по корпусам. "
                            "колическтва талонов и стоимости")),
    ],
    className="mb-4 align-items-stretch",
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page,
                            "Показатели: сводная по индикаторам",
                            "Формирует отчет по выбранным индикаторным показателям.")),
    ],
    className="mb-4 align-items-stretch",
)
economist_main = html.Div([
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
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4, open_report_5):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": label, "href": f"/{main_link}", "active": True}]

    if button_id.startswith("open-report-") and main_link in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"label": "Сверхподушевое финансирование", "active": True})
            return f'/{main_link}/svpod', breadcrumb_items
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            breadcrumb_items.append({"label": "По врачам", "active": True})
            return f'/{main_link}/doctors', breadcrumb_items
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            breadcrumb_items.append({"label": "Диспансеризация по возрастам", "active": True})
            return f'/{main_link}/disp_by_ages', breadcrumb_items
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            breadcrumb_items.append({"label": "Стационары", "active": True})
            return f'/{main_link}/stationary', breadcrumb_items
        elif button_id == f'open-report-5-{type_page}' and open_report_5:
            breadcrumb_items.append({"label": "Стационары", "active": True})
            return f'/{main_link}/indicators', breadcrumb_items

    return f'/{main_link}', breadcrumb_items
