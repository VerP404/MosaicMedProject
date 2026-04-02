"""Настройки внешних Dash-приложений (порты из БД home_mainsettings или env)."""
import os

from apps.analytical_app.query_executor import execute_query


def get_dash_dn_port() -> int:
    """Порт приложения apps.dash_dn (по умолчанию 7777, см. PORT_DASH_DN)."""
    try:
        rows = execute_query("SELECT dash_dn_port FROM home_mainsettings LIMIT 1")
        if rows and rows[0] and rows[0][0] is not None:
            return int(rows[0][0])
    except Exception:
        pass
    return int(os.getenv("PORT_DASH_DN", "7777"))
