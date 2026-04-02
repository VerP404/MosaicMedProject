from dash import html, Input, Output, callback_context, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import request

from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card
from apps.analytical_app.dash_settings import get_dash_dn_port

# Тип страницы и базовые настройки
type_page = 'doctor'
main_link = 'doctor'
label = 'Врач'

# Сетка Bootstrap: 4 колонки на MD+, общий gap, выравнивание по высоте
cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Талоны по типу и цели",
                            "Талоны ОМС по типам и цели. Фильтрация по всем параметрам.")),
        dbc.Col(create_card(2, type_page,
                            "Отказы",
                            "Работа с отказами в оплате ОМС.")),
        dbc.Col(create_card(3, type_page,
                            "Услуги ДН",
                            "Подбор услуг при проведении диспансерного наблюдения по диагнозу и специальности.")),
    ],
    className="row-cols-1 row-cols-md-4 g-4 mb-4 align-items-stretch"
)

# Основной layout
doctor_main = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[{"label": label, "active": True}]
    ),
    html.Hr(),
    dcc.Location(id=f'url-{type_page}', refresh=True),
    cards_row_1,
])


def _host_without_port(host: str) -> str:
    """Host из заголовка Host / X-Forwarded-Host без порта (учёт IPv6 в квадратных скобках)."""
    if not host:
        return host
    if host.startswith('['):
        end = host.find(']')
        return host[: end + 1] if end != -1 else host
    if ':' in host:
        host_part, port_part = host.rsplit(':', 1)
        if port_part.isdigit():
            return host_part
    return host


@app.callback(
    Output(f'url-{type_page}', 'pathname'),
    [Input(f'open-report-{i}-{type_page}', 'n_clicks') for i in range(1, 3)],
    prevent_initial_call=True
)
def navigate_pages(*n_clicks):
    """Карточки 1–2: навигация внутри этого Dash; карточка 3 — отдельное приложение на порту dash_dn."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    report_num = int(button_id.split('-')[2])

    route_map = {
        1: f"/{main_link}/doctor_talon",
        2: f"/{main_link}/error",
    }

    return route_map[report_num]


@app.callback(
    Output('redirect-dn-external', 'href'),
    Input(f'open-report-3-{type_page}', 'n_clicks'),
    prevent_initial_call=True,
)
def redirect_to_dash_dn(n_clicks):
    """Переход на приложение dash_dn на том же хосте, порт из настроек (get_dash_dn_port)."""
    if not n_clicks:
        raise PreventUpdate
    port = get_dash_dn_port()
    host_header = request.headers.get('X-Forwarded-Host') or request.host
    if host_header:
        host_header = host_header.split(',')[0].strip()
    hostname = _host_without_port(host_header)
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    if scheme:
        scheme = scheme.split(',')[0].strip()
    return f'{scheme}://{hostname}:{port}/'
