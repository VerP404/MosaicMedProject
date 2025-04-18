from dash import html, Input, Output, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# "Диспансеризация детей"
type_page = 'children'
main_link = 'head/children'
label = 'Диспансеризация детей'

# Сетка Bootstrap: 4 колонки на MD+, единый gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(
            create_card(1, type_page,
                        "Отчет по видам диспансеризации детей",
                        "Все виды диспансеризации детей с разбивкой по целям, корпусам и отделениям"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(2, type_page,
                        "Диспансеризация детей по возрастам",
                        "Все виды диспансеризации детей с разбивкой по возрастам"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(3, type_page,
                        "Список прикрепленных детей",
                        "Список прикрепленных детей с отметками о наличии ПН1"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(4, type_page,
                        "Уникальные дети в ПН",
                        "Уникальные дети в талонах диспансеризации детей"),
            className="d-flex"
        ),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
head_children_dd_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    cards_row_1,
])

# Callback навигации: n_clicks_timestamp + allow_duplicate
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True), Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in range(1, 5)],
    prevent_initial_call=True
)
def navigate_children(ts1, ts2, ts3, ts4):
    timestamps = [ts1, ts2, ts3, ts4]
    if not any(timestamps):
        raise PreventUpdate

    # Определяем индекс последней нажатой кнопки
    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0) + 1

    # Подписи и сегменты маршрутов
    label_map = {
        1: "Отчет по видам диспансеризации детей",
        2: "Диспансеризация детей по возрастам",
        3: "Список прикрепленных детей",
        4: "Уникальные дети в ПН",
    }
    route_map = {
        1: f"/{main_link}/pn1",
        2: f"/{main_link}/pn2",
        3: f"/{main_link}/pn3",
        4: f"/{main_link}/pn4",
    }
    selected_label = label_map[idx]
    selected_route = route_map[idx]

    # Хлебные крошки
    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": selected_label, "active": True}
    ]
    return selected_route, breadcrumbs
