from dash import html, Input, Output, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

# "Репродуктивное здоровье"
type_page = 'reproductive'
main_link = 'head/reproductive'
label = 'Репродуктивное здоровье'

# Bootstrap-сетка: 4 колонки на MD+, единый gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(
            create_card(1, type_page,
                        "Отчет по видам диспансеризации",
                        "Все виды диспансеризации репродуктивного здоровья с разбивкой по целям, корпусам и отделениям"),
            className="d-flex"
        ),
        dbc.Col(
            create_card(2, type_page,
                        "Списки пациентов репродуктивного здоровья",
                        "Списки пациентов для анализа и планирования диспансеризации репродуктивного здоровья"),
            className="d-flex"
        ),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
data_div = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[{"label": label, "active": True}]),
    html.Hr(),
    cards_row_1,
])
head_reproductive_main = data_div

# Callback навигации: n_clicks_timestamp + allow_duplicate
@app.callback(
    [Output('url', 'pathname', allow_duplicate=True), Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-{i}-{type_page}', 'n_clicks_timestamp') for i in [1, 2]],
    prevent_initial_call=True
)
def navigate_reproductive(ts1, ts2):
    timestamps = [ts1, ts2]
    if not any(timestamps):
        raise PreventUpdate

    idx = max(range(len(timestamps)), key=lambda i: timestamps[i] or 0) + 1

    label_map = {
        1: "Отчет по видам диспансеризации",
        2: "Списки пациентов репродуктивного здоровья"
    }
    route_map = {
        1: f"/{main_link}/dr1",
        2: f"/{main_link}/dr2"
    }
    selected_label = label_map[idx]
    selected_route = route_map[idx]

    breadcrumbs = [
        {"label": label, "href": f"/{main_link}", "active": False},
        {"label": selected_label, "active": True}
    ]
    return selected_route, breadcrumbs
