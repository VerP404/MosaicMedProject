#!/bin/sh
set -eu

DB_HOST="${HOST:-db}"
DB_PORT="${PORT:-5432}"

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 90); do
  if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
    echo "[entrypoint] PostgreSQL is up."
    break
  fi
  if [ "$i" -eq 90 ]; then
    echo "[entrypoint] ERROR: PostgreSQL not reachable after 90 attempts." >&2
    exit 1
  fi
  sleep 2
done

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Ensuring ETL folders..."
python mosaic_conductor/etl/create_folders.py

if [ "${RUN_IMPORT_INDICATORS:-0}" = "1" ]; then
  echo "[entrypoint] Importing indicators structure..."
  python manage.py import_indicators_structure \
    apps/plan/fixtures/indicators_structure.json --update-existing || true
fi

echo "[entrypoint] Starting application processes..."
exec "$@"
