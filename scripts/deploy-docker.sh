#!/usr/bin/env bash
# Обновление MosaicMed на сервере через Docker Compose.
#
# Использование:
#   chmod +x scripts/deploy-docker.sh
#   ./scripts/deploy-docker.sh
#
# Переменные:
#   MOSAICMED_ROOT — корень репозитория (по умолчанию: родитель scripts/)
#   DEPLOY_SKIP_BUILD=1 — не пересобирать образ
#   RUN_IMPORT_INDICATORS=1 — передать в .env или export для entrypoint

set -euo pipefail

ROOT="${MOSAICMED_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "[deploy-docker] ERROR: нет файла .env. Скопируйте: cp .env.docker.example .env" >&2
  exit 1
fi

echo "[deploy-docker] repo: $ROOT"
git pull --ff-only || {
  echo "[deploy-docker] git pull failed. Проверьте git status." >&2
  exit 1
}

if [ "${DEPLOY_SKIP_BUILD:-0}" != "1" ]; then
  echo "[deploy-docker] docker compose build mosaicmed"
  docker compose build mosaicmed
fi

echo "[deploy-docker] docker compose up -d"
docker compose up -d

echo "[deploy-docker] status:"
docker compose ps

echo "[deploy-docker] done. Логи: docker compose logs -f mosaicmed"
echo "[deploy-docker] Документация: docs/docker.md"
