import os
from pathlib import Path

import dash
import dash_bootstrap_components as dbc

os.environ.setdefault("DASH_DISABLE_VERSION_CHECK", "true")

_CURRENT = Path(__file__).resolve().parent
_ANALYTICAL_ASSETS = _CURRENT.parent / "analytical_app" / "assets"
_LOCAL_ASSETS = _CURRENT / "assets"
_ASSETS = _LOCAL_ASSETS if _LOCAL_ASSETS.is_dir() else _ANALYTICAL_ASSETS
_BOOTSTRAP_ICONS = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"

dash_dn_app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        _BOOTSTRAP_ICONS,
    ],
    assets_folder=str(_ASSETS.resolve()),
    serve_locally=True,
    title="МозаикаМед · Подбор услуг ДН",
)
dash_dn_app.server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
server = dash_dn_app.server
