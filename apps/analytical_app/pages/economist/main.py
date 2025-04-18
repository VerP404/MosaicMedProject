from dash import html, Input, Output, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'economist'
main_link = "economist"
label = "Экономист"

# Первая группа карточек: 4 колонки на MD+, общий gap, выравнивание по высоте
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
                            "Отчет по КСГ в разбивке по корпусам. количества талонов и стоимости")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Вторая группа: те же настройки, хотя колонок меньше
cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page,
                            "Показатели: сводная по индикаторам",
                            "Формирует отчет по выбранным индикаторным показателям.")),
        dbc.Col(create_card(6, type_page,
                            "Стационары: по врачам",
                            "Отчет по стационарным случаям по врачам.")),
        dbc.Col(create_card(7, type_page, "Талоны по врачам", "Талоны ОМС по врачам в разрезе по месяцям.")),

    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
economist_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    cards_row_1,
    cards_row_2,
])

# Callback навигации по карточкам: с n_clicks_timestamp, без ложных срабатываний
@app.callback(
    [Output('url', 'pathname'),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in range(1, 8)],
    prevent_initial_call=True
)
def navigate_pages(ts1, ts2, ts3, ts4, ts5, ts6, ts7):
    timestamps = [ts1, ts2, ts3, ts4, ts5, ts6, ts7]
    # если ни одна кнопка не была нажата — не обновляем
    if not any(timestamps):
        raise PreventUpdate

    # определяем индекс последней нажатой кнопки
    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0) + 1

    # словари меток и маршрутов
    label_map = {
        1: "Сверхподушевое финансирование",
        2: "По врачам",
        3: "Диспансеризация по возрастам",
        4: "Стационары",
        5: "Показатели: сводная по индикаторам",
        6: "Стационары: по врачам",
        7: "Талоны по врачам помесячно",
    }
    route_map = {
        1: f"/{main_link}/svpod",
        2: f"/{main_link}/doctors",
        3: f"/{main_link}/disp_by_ages",
        4: f"/{main_link}/stationary",
        5: f"/{main_link}/indicators",
        6: f"/{main_link}/doctor-stac",
        7: f"/{main_link}/doctors_talon",

    }

    selected_label = label_map[idx]
    selected_route = route_map[idx]

    # формируем хлебные крошки
    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": selected_label, "active": True}
    ]
    return selected_route, breadcrumbs
