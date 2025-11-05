from dash import html, Input, Output, callback_context, dcc
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
                            "Показатели: система планирования",
                            "Формирует отчет по выбранным показателям выполнения с планами.")),
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
        dbc.Col(create_card(6, type_page,
                            "Стационары: по врачам",
                            "Отчет по стационарным случаям по врачам.")),
        dbc.Col(create_card(7, type_page, "Талоны по врачам", "Талоны ОМС по врачам в разрезе по месяцам.")),
        dbc.Col(create_card(8, type_page, "Диспансеризация", "Анализ диспансеризации по врачам: ОМС и детализация услуг.")),
        dbc.Col(create_card(9, type_page,
                            "Финансовые показатели",
                            "Финансовые показатели по целям и СМО с разбивкой по Инкомед, Согаз и иногородним.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)


# Основной layout
economist_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
    cards_row_2,
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in [1, 2, 3, 4, 6, 7, 8, 9]],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/svpod",
        2: f"/{main_link}/doctors",
        3: f"/{main_link}/disp_by_ages",
        4: f"/{main_link}/stationary",
        6: f"/{main_link}/doctor-stac",
        7: f"/{main_link}/doctors_talon",
        8: f"/{main_link}/dispensary",
        9: f"/{main_link}/financial_indicators",
    }
    
    return route_map[report_num]
