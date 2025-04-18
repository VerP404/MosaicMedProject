from dash import html, Input, Output, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'statistic'
main_link = 'statistic'
label = 'Статистик'

# Сетка Bootstrap: 4 колонки на MD+, единый gap, выравнивание по высоте
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
                            "Отчет по пневмониям в талонах ОМС.")),
        dbc.Col(create_card(4, type_page,
                            "Посещения в диспансеризации",
                            "Посещения в диспансеризации и профосмотрах взрослых для вставки в гугл-таблицу.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
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
        dbc.Col(create_card(8, type_page,
                            "РЭМД 500",
                            "Отчеты по РЭМД.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
statistic_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[{"label": label, "active": True}]),
    html.Hr(),
    cards_row_1,
    cards_row_2,
])

# Колбэк навигации: n_clicks_timestamp + allow_duplicate
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in range(1, 9)],
    prevent_initial_call=True
)
def navigate_pages(ts1, ts2, ts3, ts4, ts5, ts6, ts7, ts8):
    timestamps = [ts1, ts2, ts3, ts4, ts5, ts6, ts7, ts8]
    if not any(timestamps):
        raise PreventUpdate

    # Определяем последнюю нажатую кнопку
    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0) + 1

    # Словари меток и маршрутов
    label_map = {
        1: "Отчет Шараповой по ДН",
        2: "Кардиологический отчет",
        3: "Пневмонии",
        4: "Посещения в диспансеризации",
        5: "Посещения в талонах",
        6: "Отчет по ВОП",
        7: "Листы нетрудоспособности",
        8: "РЭМД 500",
    }
    route_map = {
        1: f"/{main_link}/statistic-sharapova",
        2: f"/{main_link}/cardiology",
        3: f"/{main_link}/pneumonia",
        4: f"/{main_link}/dd-visits",
        5: f"/{main_link}/visits",
        6: f"/{main_link}/vop",
        7: f"/{main_link}/eln",
        8: f"/{main_link}/remd500",
    }

    selected_label = label_map[idx]
    selected_route = route_map[idx]

    # Формируем хлебные крошки
    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": selected_label, "active": True}
    ]
    return selected_route, breadcrumbs
