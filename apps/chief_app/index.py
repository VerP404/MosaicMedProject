# apps/chief_app/index.py
import sys
import os

from apps.chief_app.app import app
from config.settings import PORT_DASH, DEBUG_DASH, PORT_DASH_CHIEF

# Получаем путь к корневой директории проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(BASE_DIR)

from datetime import datetime
import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc

from apps.chief_app import main_color
from apps.chief_app.components.header import header
from apps.chief_app.components.footer import footer
from apps.chief_app.components.content import content


# Установка layout приложения
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        header,
        html.Div([
            content
        ], style={"position": "relative", "minHeight": "calc(100vh - 120px)"}),  # Учитываем высоту хедера и футера
        footer
    ],
    style={"backgroundColor": main_color, "height": "100vh", "overflow": "hidden"}
)


# Callback для обновления времени
@app.callback(Output('live-time', 'children'),
              Input('interval-component', 'n_intervals'))
def update_time(n):
    return datetime.now().strftime("%d-%m-%Y %H:%M")


if __name__ == "__main__":
    app.run_server(debug=DEBUG_DASH, host='0.0.0.0', port=PORT_DASH)
