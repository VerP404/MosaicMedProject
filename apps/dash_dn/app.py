import os
from pathlib import Path

import dash
import dash_bootstrap_components as dbc

os.environ.setdefault("DASH_DISABLE_VERSION_CHECK", "true")

_CURRENT = Path(__file__).resolve().parent
_ANALYTICAL_ASSETS = _CURRENT.parent / "analytical_app" / "assets"
_LOCAL_ASSETS = _CURRENT / "assets"
# В `apps/dash_dn/assets/` лежит только `custom.css`, а `bootstrap*.css` и шрифты bootstrap-icons
# находятся в `apps/analytical_app/assets/`. Поэтому для офлайн-режима всегда используем
# assets аналитического приложения.
_ASSETS = _ANALYTICAL_ASSETS

dash_dn_app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    # Подключаем Bootstrap и bootstrap-icons локально, чтобы не зависеть от интернета.
    external_stylesheets=[
        "/assets/css/bootstrap.min.css",
        "/assets/css/bootstrap-icons.css",
    ],
    assets_folder=str(_ASSETS.resolve()),
    serve_locally=True,
    title="МозаикаМед · Подбор услуг ДН",
)
dash_dn_app.server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
server = dash_dn_app.server
