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
PORT_DASH = int(os.getenv('PORT_DASH', '8050'))
HOST_DASH = os.getenv('HOST_DASH', '0.0.0.0')

from dash import dcc, html
from apps.analytical_app.app import app
from apps.analytical_app.routes import register_routes
from components.sidebar import create_sidebar
from components.navbar import create_navbar, create_modal_168n, create_modal_status, create_modal_goal
from components.footer import create_footer

app.layout = html.Div(
    [
        dcc.Store(id='current-month-number', data=None),
        dcc.Store(id='current-month-name', data=None),
        dcc.Store(id='sidebar-state', data="collapsed"),  # Хранилище для состояния сайдбара
        dcc.Interval(id='date-interval-main', interval=600000, n_intervals=0),  # 10 минут
        dcc.Location(id="url"),
        create_navbar(),
        create_modal_168n(),
        create_modal_status(),
        create_modal_goal(),
        create_sidebar(),
        html.Div(id='page-content', style={'margin-left': '5rem', 'margin-top': '56px', 'padding': '2rem 1rem'}),
        create_footer(),
    ]
)

register_routes(app)
if __name__ == "__main__":
    app.run(debug=DEBUG_DASH, host=HOST_DASH, port=PORT_DASH)
