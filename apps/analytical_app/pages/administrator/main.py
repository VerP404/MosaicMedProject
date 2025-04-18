from dash import html, Input, Output, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'admin'
main_link = 'admin'
label = 'Администратор'

# Сетка Bootstrap: 4 колонки на MD+, единый gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Для сборки талонов",
                            "Отчет для сборки талонов по дате создания талона и цели.")),
        dbc.Col(create_card(2, type_page,
                            "Аннулирование ЭМД",
                            "В разработке! Ввод данных для формирования запроса на аннулирование ЭМД")),
        dbc.Col(create_card(3, type_page,
                            "Обновление данных",
                            "Страница обновления данных в базе данных.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
admin_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    cards_row_1,
])

# Колбэк навигации: n_clicks_timestamp + allow_duplicate
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in range(1, 4)],
    prevent_initial_call=True
)
def navigate_pages(ts1, ts2, ts3):
    timestamps = [ts1, ts2, ts3]
    if not any(timestamps):
        raise PreventUpdate

    # Определяем индекс последней нажатой кнопки
    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0) + 1

    label_map = {
        1: "Для сборки талонов",
        2: "Аннулирование ЭМД",
        3: "Обновление данных"
    }
    route_map = {
        1: f"/{main_link}/gen_invoices",
        2: f"/{main_link}/admin_delete_emd",
        3: f"/{main_link}/admin_update_data"
    }

    selected_label = label_map[idx]
    selected_route = route_map[idx]

    # Формируем хлебные крошки
    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": selected_label, "active": True}
    ]
    return selected_route, breadcrumbs