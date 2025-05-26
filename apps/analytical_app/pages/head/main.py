from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# Тип страницы и базовые настройки
type_page = 'head'
main_link = 'head'
label = 'Заведующий'

# Сетка Bootstrap: 4 колонки на MD+, общий gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page, "Диспансеризация взрослых", "Отчеты по диспансеризации взрослых")),
        dbc.Col(create_card(2, type_page, "Диспансеризация детей", "Отчеты по диспансеризации детей")),
        dbc.Col(create_card(3, type_page, "Репродуктивное здоровье", "Отчеты по диспансеризации репродуктивного здоровья")),
        dbc.Col(create_card(4, type_page, "Диспансерное наблюдение работающих", "Анализ работающих не прикрепленных пациентов, внесенных в ИСЗЛ")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

cards_row_2 = dbc.Row(
    [
        dbc.Col(create_card(5, type_page, "Отчет Шараповой по ДН", "Еженедельный отчет Шараповой по ДН по дате создания талонов цель 3.")),
        dbc.Col(create_card(6, type_page, "131 форма", "131 форма по данным из WEB-ОМС")),
        dbc.Col(create_card(7, type_page, "- Диспансерное наблюдение", "-")),
        dbc.Col(create_card(8, type_page, "Обращения граждан", "Дашборд обращений граждан")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

cards_row_3 = dbc.Row(
    [
        dbc.Col(create_card(9, type_page, "Талоны по врачам (помесячно)", "Талоны ОМС по врачам в разрезе по месяцам.")),
        dbc.Col(create_card(10, type_page, "Талоны по врачам (по целям)", "Талоны ОМС по врачам и целям.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
head_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
    cards_row_2,
    cards_row_3,
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in range(1, 11)],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/adults",
        2: f"/{main_link}/children",
        3: f"/{main_link}/reproductive",
        4: f"/{main_link}/dn_job",
        5: f"/{main_link}/statistic-sharapova",
        6: f"/{main_link}/dispensary-reports",
        7: f"/{main_link}/dispensary-reports",
        8: f"/{main_link}/journal",
        9: f"/{main_link}/doctors_talon",
        10: f"/{main_link}/doctors_talon_goals",
    }
    
    return route_map[report_num]