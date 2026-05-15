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
_DASH_DN_CUSTOM_CSS = _ASSETS / "dash_dn_custom.css"


def _sync_dash_dn_custom_css() -> None:
    """Копирует custom.css в assets_folder — Dash подхватит файл автоматически (без html.Style)."""
    src = _LOCAL_ASSETS / "custom.css"
    if not src.is_file():
        return
    try:
        if not _DASH_DN_CUSTOM_CSS.exists() or src.stat().st_mtime > _DASH_DN_CUSTOM_CSS.stat().st_mtime:
            _DASH_DN_CUSTOM_CSS.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    except OSError:
        pass


_sync_dash_dn_custom_css()

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
