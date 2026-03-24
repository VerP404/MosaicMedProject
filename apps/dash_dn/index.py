"""
Запуск Dash-приложения «Подбор услуг ДН» (отдельно от Django, SQLite).

По умолчанию: http://0.0.0.0:7777/
Порт: PORT_DASH_DN (иначе 7777), хост: HOST_DASH_DN (иначе 0.0.0.0).
База: DASH_DN_SQLITE (иначе apps/dash_dn/data/dn_catalog.sqlite).
Правка глобального справочника в UI: DASH_DN_GLOBAL_ADMIN_PASSWORD (см. вкладку «Справочники»).

Из корня репозитория:
    python -m apps.dash_dn
    python apps/dash_dn/index.py
"""
from __future__ import annotations

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass


def main() -> None:
    debug = os.getenv("DEBUG_DASH_DN", "True").lower() == "true"
    port = int(os.getenv("PORT_DASH_DN", "7777"))
    host = os.getenv("HOST_DASH_DN", "0.0.0.0")

    from apps.dash_dn.sqlite_catalog.catalog_ops import init_app_database

    init_app_database()

    import apps.dash_dn.dn_services_page  # noqa: F401 - callbacks
    import apps.dash_dn.reference_pages  # noqa: F401 - reference UI + Store
    import apps.dash_dn.analysis_page  # noqa: F401 - анализ CSV выгрузки

    from apps.dash_dn.shell import init_layout
    from apps.dash_dn.app import dash_dn_app

    init_layout()

    dash_dn_app.run(
        debug=debug,
        host=host,
        port=port,
        dev_tools_disable_version_check=True,
    )


if __name__ == "__main__":
    main()
