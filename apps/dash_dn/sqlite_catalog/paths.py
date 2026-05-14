from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PACKAGE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "dn_catalog.sqlite"
# Сид базы «до 01.04» (slug matrix_before_*); при отсутствии файла seed_if_empty смотрит legacy seed_global.json
SEED_MATRIX_BEFORE_JSON = DATA_DIR / "seed_matrix_before.json"
SEED_GLOBAL_JSON = DATA_DIR / "seed_global.json"


def get_db_path() -> Path:
    env = os.getenv("DASH_DN_SQLITE")
    if env:
        return Path(env).expanduser().resolve()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH.resolve()
