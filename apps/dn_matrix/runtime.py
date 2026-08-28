"""Ленивая инициализация Django для процесса Dash."""
from __future__ import annotations

import os


def ensure_django() -> None:
    import django
    from django.apps import apps

    if apps.ready:
        return
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
