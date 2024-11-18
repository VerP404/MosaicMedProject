# apps/chief_app/app.py
import dash
import os
import dash_bootstrap_components as dbc

# Получаем абсолютный путь к текущей директории
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Указываем путь к папке assets
ASSETS_PATH = os.path.join(CURRENT_DIRECTORY, 'assets')

# Создание приложения Dash
app = dash.Dash(__name__,
                update_title=None,
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP,
                                      "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.10.5/font/bootstrap-icons.min.css"
                                      ])

app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.title = 'МозаикаМед: Главный врач'

server = app.server
