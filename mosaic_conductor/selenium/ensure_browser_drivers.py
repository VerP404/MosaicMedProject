#!/usr/bin/env python3
"""Прогрев ChromeDriver/GeckoDriver в mosaic_conductor/selenium/.drivers/."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from mosaic_conductor.selenium.driver_resolver import DRIVERS_DIR, ensure_driver


def _needed_browsers():
    names = []
    for key in ("ISZL_BROWSER", "OMS_BROWSER", "DAGSTER_WO_BROWSER"):
        value = (os.getenv(key) or "").strip().lower().strip("'\"")
        if value in ("chrome", "firefox"):
            names.append(value)
    if not names:
        names = ["chrome"]
    return sorted(set(names))


def main():
    needed = _needed_browsers()
    print(f"[INFO] Нужны драйверы для: {', '.join(needed)}")
    print(f"[INFO] Каталог кэша: {DRIVERS_DIR}")
    ok = []
    failed = []
    for browser in needed:
        try:
            path = ensure_driver(browser, refresh=True)
            print(f"[INFO] {browser}: {path}")
            ok.append(browser)
        except Exception as e:
            print(f"[WARN] Не удалось подготовить драйвер {browser}: {e}")
            failed.append(browser)
    if not ok:
        print(
            "[ERROR] Не удалось подготовить ни один браузерный драйвер. "
            "Проверьте наличие Chrome/Firefox и доступ в интернет."
        )
        return 1
    if failed:
        print(f"[WARN] Часть драйверов не подготовлена: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
