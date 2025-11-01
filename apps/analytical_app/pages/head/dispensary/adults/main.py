from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# "Диспансеризация взрослых"
type_page = 'adults'
main_link = 'head/adults'
label = 'Диспансеризация взрослых'

# Сетка Bootstrap: 3 карточки, равная сетка на MD+ и gap
cards_row_1 = dbc.Row(
    [
        dbc.Col(
            create_card(1, type_page,
                        "Отчет по видам диспансеризации",
                        "Все виды диспансеризации с разбивкой по целям, корпусам и отделениям"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(3, type_page,
                        "Диспансеризация по возрастам",
                        "Все виды диспансеризации с разбивкой по возрастам"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(8, type_page,
                        "Диспансеризация по стоимости",
                        "Все виды диспансеризации с группировкой по стоимости"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(9, type_page,
                        "РЭМД диспансеризации",
                        "По статусам и месяцам."),
            className="d-flex"
        ),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(
            create_card(10, type_page,
                        "По возрастам и группам здоровья",
                        "Формирует отчет по возрастам и группам здоровья в диспансеризации."),
            className="d-flex"
        ),
        dbc.Col(
            create_card(11, type_page,
                        "Анализ карт на формирование ЭМД",
                        "Пустая страница. Далее добавим логику."),
            className="d-flex"
        ),
        dbc.Col(
            create_card(12, type_page,
                        "Записаны, но не прошли",
                        "Записаны на прием, но нет ДВ4/ОПВ в выбранном году"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(13, type_page,
                        "Прикрепленные не прошедшие",
                        "Прикрепленные пациенты без диспансеризации с фильтрами по полу и возрасту"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(14, type_page,
                        "Диспансеризация в организованных коллективах",
                        "Сводная таблица по возрастам и типам диспансеризации на основе загруженных талонов"),
            className="d-flex"
        ),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)
# Основной layout
head_adults_dd_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
    cards_row_2
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in [1, 3, 8, 9, 10, 11, 12, 13, 14]],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/dv1",
        3: f"/{main_link}/dv3",
        8: f"/{main_link}/dv8",
        9: f"/{main_link}/dv9",
        10: f"/{main_link}/dv10",
        11: f"/{main_link}/dv11",
        12: f"/{main_link}/dv12",
        13: f"/{main_link}/dv13",
        14: f"/{main_link}/dv14",
    }
    
    return route_map[report_num]
