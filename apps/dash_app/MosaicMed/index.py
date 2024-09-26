# index.py
import os
import sys

from dash import Input, Output, dcc, html
from flask_login import current_user

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from services.MosaicMed.flaskapp.models import user_has_access
from services.MosaicMed.app import app
from services.MosaicMed.components.content import content
from services.MosaicMed.components.footer import footer
from services.MosaicMed.components.header import header
from services.MosaicMed.components.sidebar import get_sidebar  # Импортируем функцию
from services.MosaicMed.pages.main.main import main_layout
from services.MosaicMed.callback.date_reports import get_current_reporting_month
from database.db_conn import init_db
from services.MosaicMed.routes import routes

MosaicMed_layout = html.Div([
    header,
    html.Div([
        html.Div(id='sidebar-container'),
        content
    ], style={"position": "relative"}),
    footer
])

app.layout = html.Div(
    [
        dcc.Store(id='current-month-number', data=None),
        dcc.Store(id='current-month-name', data=None),
        dcc.Interval(id='date-interval-main', interval=600000, n_intervals=0),  # 1 час
        dcc.Location(id="url"),
        MosaicMed_layout
    ]
)


@app.callback(
    Output('sidebar-container', 'children'),
    [Input('url', 'pathname')]
)
def update_sidebar(pathname):
    return get_sidebar()


@app.callback(
    Output('current-month-number', 'data'),
    Output('current-month-name', 'data'),
    [Input('date-interval-main', 'n_intervals')]
)
def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_num, current_month_name


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    def check_access_and_render(user, user_access, path, role, comp):
        if path == role:
            if user.has_role('admin') or user_access(user.role, role):
                return comp
            else:
                return html.H2("Доступ запрещен")
        return None

    if not current_user.is_authenticated and pathname != '/login':
        return dcc.Location(pathname='/login', id='redirect')
    # Главная страница
    if pathname == "/main":
        return main_layout
    # Логин
    elif pathname == "/login":
        return dcc.Location(pathname='/login', id='redirect')

    for role_path, component in routes.items():
        result = check_access_and_render(current_user, user_has_access, pathname, role_path, component)
        if result:
            return result

    return html.H2("Страница не найдена")


if __name__ == "__main__":
    init_db()
    app.run_server(debug=False, host='0.0.0.0', port='5000')
