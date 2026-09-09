# apps/chief_app/app.py
import dash
import os

os.environ.setdefault("DASH_DISABLE_VERSION_CHECK", "true")

# Получаем абсолютный путь к текущей директории
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Указываем путь к папке assets
ASSETS_PATH = os.path.join(CURRENT_DIRECTORY, 'assets')

# Создание приложения Dash (Bootstrap и bootstrap-icons из assets/, без CDN)
app = dash.Dash(
    __name__,
    update_title=None,
    suppress_callback_exceptions=True,
    assets_folder=ASSETS_PATH,
    serve_locally=True,
    external_stylesheets=[
        "/assets/css/bootstrap.min.css",
        "/assets/css/bootstrap-icons.css",
    ],
)

app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.title = 'МозаикаМед: Главный врач'

server = app.server
