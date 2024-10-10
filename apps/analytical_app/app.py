# apps/analytical_app/app.py
import dash
import dash_bootstrap_components as dbc
import os

# Получаем абсолютный путь к текущей директории
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Указываем путь к папке assets
ASSETS_PATH = os.path.join(CURRENT_DIRECTORY, 'assets')

app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                assets_folder=ASSETS_PATH
                )

app.title = 'МозаикаМед-Аналитика'

server = app.server
