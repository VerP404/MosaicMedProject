# apps/analytical_app/app.py
import dash
import os

# Dash 3 can ping Plotly for version updates in Dev Tools.
# In closed/offline networks this produces noisy browser console errors.
os.environ.setdefault("DASH_DISABLE_VERSION_CHECK", "true")

# Получаем абсолютный путь к текущей директории
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Указываем путь к папке assets
ASSETS_PATH = os.path.join(CURRENT_DIRECTORY, 'assets')

# CSS/JS/шрифты из assets/ (Bootstrap, bootstrap-icons, Font Awesome) — без CDN.
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    assets_folder=ASSETS_PATH,
    serve_locally=True,
    external_stylesheets=[
        "/assets/css/bootstrap.min.css",
        "/assets/css/bootstrap-icons.css",
        "/assets/css/all.min.css",
    ],
)

app.server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.title = 'МозаикаМед: Аналитика'

server = app.server

# Базовый URL Django API (задается через .env DJANGO_API_BASE)
DJANGO_API_BASE = os.getenv('DJANGO_API_BASE', 'http://127.0.0.1:8000')