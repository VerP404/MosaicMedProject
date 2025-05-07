from dash import html, Input, Output, callback_context
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
        dbc.Col(create_card(10, type_page,
                            "По группам здоровья ",
                            "Формирует отчет по группам здоровья при диспансеризации.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)
# Основной layout
head_adults_dd_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    cards_row_1,
    cards_row_2
])


# Callback навигации: n_clicks_timestamp + allow_duplicate
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in [1, 3, 8, 9, 10]],
    prevent_initial_call=True
)
def navigate_adults(ts1, ts3, ts8, ts9, ts10):
    timestamps = [ts1, ts3, ts8, ts9, ts10]
    if not any(timestamps):
        raise PreventUpdate

    # Определяем индекс последней нажатой кнопки
    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0)

    # Подписи и сегменты маршрутов
    mapping = {
        0: ("Отчет по видам диспансеризации", "dv1"),
        1: ("Диспансеризация по возрастам", "dv3"),
        2: ("Диспансеризация по стоимости", "dv8"),
        3: ("РЭМД диспансеризации", "dv9"),
        4: ("РЭМД диспансеризации", "dv10"),
    }
    label_text, segment = mapping[idx]
    new_path = f"/{main_link}/{segment}"

    # Хлебные крошки
    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": label_text, "active": True}
    ]
    return new_path, breadcrumbs
