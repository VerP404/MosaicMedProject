# index.py

from django_plotly_dash import DjangoDash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
import os

# Определение путей к статическим файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'

external_stylesheets = [
    STATIC_URL + 'css/bootstrap.min.css',
    STATIC_URL + 'css/styles.css',
    STATIC_URL + 'css/fontawesome/all.css'
]

external_scripts = [
    STATIC_URL + 'js/bootstrap.bundle.js',
    STATIC_URL + 'js/datetime.js'
]

# Инициализация приложения Dash с использованием DjangoDash
app = DjangoDash(
    'MosaicMed',
    external_stylesheets=external_stylesheets,
    external_scripts=external_scripts,
    suppress_callback_exceptions=True
)

# Установка заголовка вкладки (можно настроить через шаблон)
app.title = 'МозаикаМед'

# Импорт необходимых компонентов
from .components.content import content
from .components.footer import footer
from .components.header import header
from .components.sidebar import get_sidebar
from .pages.main.main import main_layout
from .callback.date_reports import get_current_reporting_month
from .routes import routes

# Определение основного layout приложения
MosaicMed_layout = html.Div([
    header,
    html.Div([
        html.Div(id='sidebar-container'),
        content
    ], style={"position": "relative"}),
    footer
])

# Установка layout приложения
app.layout = html.Div(
    [
        dcc.Store(id='current-month-number', data=None),
        dcc.Store(id='current-month-name', data=None),
        dcc.Interval(id='date-interval-main', interval=600000, n_intervals=0),  # Интервал обновления 10 минут
        dcc.Location(id="url"),
        MosaicMed_layout
    ]
)

# Коллбэки
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
    if pathname == "/main":
        return main_layout

    for role_path, component in routes.items():
        if pathname == role_path:
            return component

    return html.H2("Страница не найдена")
