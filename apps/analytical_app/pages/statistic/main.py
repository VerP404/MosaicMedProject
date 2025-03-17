from dash import html, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "statistic"
main_link = "statistic"  # начало ссылки
label = "Статистик"  # для хлебных крошек
# Карточки для отчётов
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Отчет Шараповой по ДН",
                            "Еженедельный отчет Шараповой по ДН с формированием по дате создания талонов.")),
        dbc.Col(create_card(2, type_page,
                            "Кардиологический отчет",
                            "Ежемесячный отчет по кардиологическим показателям.")),
        dbc.Col(create_card(3, type_page,
                            "Пневмонии",
                            "Отчет по пневмониям в талонах ОМС")),
        dbc.Col(create_card(4, type_page,
                            "Посещения в диспансеризации",
                            "Посещения в диспансеризации и профосмотрах взрослых для вставки в гугл-таблицу")),

    ],
    className="mb-4 align-items-stretch",
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page,
                            "Посещения в талонах",
                            "Отчет по количеству посещений пациентами взрослыми и детьми.")),
        dbc.Col(create_card(6, type_page,
                            "Отчет по ВОП",
                            "Ежемесячный отчет по ВОП для кадров.")),
        dbc.Col(create_card(7, type_page,
                            "Листы нетрудоспособности",
                            "Отчеты по листам нетрудоспособности.")),
    ],
    className="mb-4 align-items-stretch",
)
statistic_main = html.Div([
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
     Input(f'open-report-7-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4, open_report_5, open_report_6,
                   open_report_7):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    breadcrumb_items = [{"label": label, "href": f"/{main_link}", "active": True}]

    if button_id.startswith("open-report-") and main_link in button_id:
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/statistic-sharapova', breadcrumb_items
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/cardiology', breadcrumb_items
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/pneumonia', breadcrumb_items
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/dd-visits', breadcrumb_items
        elif button_id == f'open-report-5-{type_page}' and open_report_5:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/visits', breadcrumb_items
        elif button_id == f'open-report-6-{type_page}' and open_report_6:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/vop', breadcrumb_items
        elif button_id == f'open-report-7-{type_page}' and open_report_7:
            breadcrumb_items.append({"active": True})
            return f'/{main_link}/eln', breadcrumb_items

    return f'/{main_link}', breadcrumb_items
