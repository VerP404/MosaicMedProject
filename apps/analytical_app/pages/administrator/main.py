from dash import html, Input, Output, callback_context, dcc
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
        dbc.Col(create_card(4, type_page,
                            "SQL Редактор",
                            "Тестирование SQL запросов (только SELECT)")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
admin_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
])

# Обновленный callback для навигации
@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in range(1, 5)],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])
    
    route_map = {
        1: f"/{main_link}/gen_invoices",
        2: f"/{main_link}/admin_delete_emd",
        3: f"/{main_link}/admin_update_data",
        4: f"/{main_link}/sql_editor"
    }
    
    return route_map[report_num]