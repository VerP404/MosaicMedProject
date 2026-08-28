"""Импорт JSON-пакета матрицы ДН (schema_version=1 + checksum)."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.dn_matrix.services.bundle import import_bundle


class Command(BaseCommand):
    help = "Импорт пакета матрицы ДН (JSON) в БД."

    def add_arguments(self, parser):
        parser.add_argument(
            "bundle_path",
            type=str,
            help="Путь к .json (schema_version=1, поле checksum)",
        )
        parser.add_argument(
            "--activate",
            action="store_true",
            help="После импорта выставить статус издания «Активна».",
        )

    def handle(self, *args, **options):
        path = Path(options["bundle_path"])
        if not path.is_file():
            raise CommandError(f"Файл не найден: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(str(e)) from e

        try:
            edition = import_bundle(data, activate=bool(options["activate"]))
        except ValidationError as e:
            raise CommandError(str(e)) from e

        status = edition.status
        self.stdout.write(
            self.style.SUCCESS(f"Импортировано издание id={edition.id} code={edition.code!r} ({status}).")
        )
