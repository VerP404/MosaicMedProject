from dash import html, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "head"
main_link = "head"  # начало ссылки
label = "Заведующий"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Диспансеризация взрослых",
                            "Отчеты по диспансеризации взрослых")),
        dbc.Col(create_card(2, type_page,
                            "Диспансеризация детей",
                            "Отчеты по диспансеризации детей")),
        dbc.Col(create_card(3, type_page,
                            "Репродуктивное здоровье",
                            "Отчеты по диспансеризации репродуктивного здоровья")),
        dbc.Col(create_card(4, type_page,
                            "Диспансерное наблюдение работающих",
                            "Анализ работающих не прикрепленных пациентов, внесенных в ИСЗЛ")),
    ],
    className="mb-4 align-items-stretch",
)
cards_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page,
                            "Отчет Шараповой по диспансерному наблюдению",
                            "Еженедельный отчет Шараповой по ДН по дате создания талонов цель 3.")),
        dbc.Col(create_card(6, type_page,
                            "131 форма",
                            "131 форма по данным из WEB-ОМС")),
        dbc.Col(create_card(7, type_page,
                            "- Диспансерное наблюдение",
                            "-")),
        dbc.Col(create_card(8, type_page,
                            "Обращения граждан",
                            "Дашборд обращений граждан")),
    ],
    className="mb-4 align-items-stretch",
)

head_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    html.Div(cards_row_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
    html.Div(cards_2, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-1-{type_page}', 'n_clicks'),
     Input(f'open-report-2-{type_page}', 'n_clicks'),
     Input(f'open-report-3-{type_page}', 'n_clicks'),
     Input(f'open-report-4-{type_page}', 'n_clicks'),
     Input(f'open-report-5-{type_page}', 'n_clicks'),
     Input(f'open-report-6-{type_page}', 'n_clicks'),
     Input(f'open-report-7-{type_page}', 'n_clicks'),
     Input(f'open-report-8-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2, open_report_3, open_report_4, open_report_5, open_report_6,
                   open_report_7, open_report_8):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_path = f'/{main_link}'

    breadcrumb_items = [{"label": label, "href": current_path, "active": True}]

    if button_id.startswith("open-report-"):
        new_segment = None
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            new_segment = "adults"
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            new_segment = "children"
        elif button_id == f'open-report-3-{type_page}' and open_report_3:
            new_segment = "reproductive"
        elif button_id == f'open-report-4-{type_page}' and open_report_4:
            new_segment = "dn_job"
        elif button_id == f'open-report-5-{type_page}' and open_report_5:
            new_segment = "statistic-sharapova"
        elif button_id == f'open-report-6-{type_page}' and open_report_6:
            new_segment = "dispensary-reports"
        elif button_id == f'open-report-7-{type_page}' and open_report_7:
            new_segment = "dispensary-reports"
        elif button_id == f'open-report-8-{type_page}' and open_report_8:
            new_segment = "journal"
        if new_segment:
            # Добавляем новый сегмент к текущему маршруту
            new_path = f'{current_path}/{new_segment}'
            breadcrumb_items.append({"label": new_segment, "active": True})
            return new_path, breadcrumb_items

    return no_update, no_update
