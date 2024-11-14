import sys
import os
from datetime import datetime

from apps.chief_app import main_color
from apps.chief_app.components.content import content
from apps.chief_app.components.footer import footer
from apps.chief_app.components.header import header

# Определяем корневую директорию проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(BASE_DIR)

# Импортируем настройки
from config.settings import PORT_DASH_CHIEF

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input

# Получаем абсолютный путь к текущей директории
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(CURRENT_DIRECTORY, 'assets')
print(ASSETS_PATH)
# Создание приложения Dash
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                serve_locally=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP,
                                      r'C:\DjangoProject\MosaicMedProject\apps\chief_app\asset\scss\styles.css',
                                      r'C:\DjangoProject\MosaicMedProject\apps\chief_app\asset\scss\card.css',
                                      ]
                )
app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.title = 'МозаикаМед-Дашборд'


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


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=PORT_DASH_CHIEF)
