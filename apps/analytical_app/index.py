# apps/analytical_app/index.py
import sys
import os

# Получаем путь к корневой директории проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(BASE_DIR)

from config.settings import DEBUG_DASH
from config.settings import PORT_DASH

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
    app.run_server(debug=DEBUG_DASH, host='0.0.0.0', port=PORT_DASH)
