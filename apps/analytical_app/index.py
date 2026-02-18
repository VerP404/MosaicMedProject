import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(BASE_DIR)

# Загружаем переменные окружения
from dotenv import load_dotenv

env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

# Получаем настройки напрямую из переменных окружения
DEBUG_DASH = os.getenv('DEBUG_DASH', 'True').lower() == 'true'
PORT_DASH = int(os.getenv('PORT_DASH', '5000'))
HOST_DASH = os.getenv('HOST_DASH', '0.0.0.0')
DJANGO_API_BASE = os.getenv('DJANGO_API_BASE', 'http://127.0.0.1:8000')

from dash import dcc, html
from apps.analytical_app.app import app
from apps.analytical_app.routes import register_routes, routes
from apps.analytical_app.components.sidebar import create_sidebar
from apps.analytical_app.components.navbar import create_navbar, create_modal_168n, create_modal_status, create_modal_goal
from apps.analytical_app.components.footer import create_footer, get_content_style

# Стили для основного контейнера
content_style = {
    'marginLeft': '5rem',  # Отступ для сайдбара
    'marginTop': '56px',  # Отступ для навбара
    'padding': '2rem 1rem',
    'paddingBottom': '60px',  # Отступ снизу для футера
    'minHeight': 'calc(100vh - 96px)'  # Минимальная высота контента
}

app.layout = html.Div(
    [
        dcc.Store(id='current-month-number', data=None),
        dcc.Store(id='current-month-name', data=None),
        dcc.Store(id='sidebar-state', data="collapsed"),  # Хранилище для состояния сайдбара
        dcc.Interval(id='date-interval-main', interval=600000, n_intervals=0),  # 10 минут
        dcc.Location(id="url", refresh=True),
        create_navbar(),
        create_modal_168n(),
        create_modal_status(),
        create_modal_goal(),
        create_sidebar(),
        html.Div(id='page-content', style=content_style),
        create_footer(),
    ]
)

register_routes(app)

if __name__ == "__main__":
    app.run(
        debug=DEBUG_DASH,
        host=HOST_DASH,
        port=PORT_DASH,
        dev_tools_disable_version_check=True,
    )
