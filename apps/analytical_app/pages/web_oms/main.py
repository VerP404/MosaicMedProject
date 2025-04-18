from dash import html, Input, Output, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'web_oms'
main_link = 'web_oms'
label = 'WEB.ОМС'

# Сетка Bootstrap для карточек
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page, "По целям", "Анализ ОМС: По целям")),
        dbc.Col(create_card(2, type_page, "Специальность по целям", "Анализ ОМС: Специальность по целям")),
        dbc.Col(create_card(3, type_page, "Корпуса по цели", "Анализ ОМС: Корпуса по цели")),
        dbc.Col(create_card(4, type_page, "Корпус и специальность по целям", "Анализ ОМС: Корпус и специальность по целям")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page, "Цели и диагнозы по корпусам", "Анализ ОМС: Цели и диагнозы по корпусам")),
        dbc.Col(create_card(6, type_page, "Список пациентов и их диагнозы в текущем году", "Анализ ОМС: Список пациентов и их диагнозы")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
web_oms_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[{"label": label, "active": True}]),
    html.Hr(),
    cards_row_1,
    cards_row_2,
])

# Колбэк навигации: n_clicks_timestamp + allow_duplicate
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in range(1, 7)],
    prevent_initial_call=True
)
def navigate_pages(ts1, ts2, ts3, ts4, ts5, ts6):
    timestamps = [ts1, ts2, ts3, ts4, ts5, ts6]
    if not any(timestamps):
        raise PreventUpdate

    # Определяем последнюю нажатую кнопку
    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0) + 1

    label_map = {
        1: "По целям",
        2: "Специальность по целям",
        3: "Корпуса по цели",
        4: "Корпус и специальность по целям",
        5: "Цели и диагнозы по корпусам",
        6: "Список пациентов и их диагнозы в текущем году"
    }
    route_map = {
        1: f"/{main_link}/web_oms_rep1",
        2: f"/{main_link}/web_oms_rep2",
        3: f"/{main_link}/web_oms_rep3",
        4: f"/{main_link}/web_oms_rep4",
        5: f"/{main_link}/web_oms_rep5",
        6: f"/{main_link}/web_oms_rep6"
    }

    selected_label = label_map[idx]
    selected_route = route_map[idx]

    # Формируем хлебные крошки
    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": selected_label, "active": True}
    ]
    return selected_route, breadcrumbs
