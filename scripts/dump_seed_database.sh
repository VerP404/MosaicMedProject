#!/usr/bin/env bash
# Дамп «стартовой» БД MosaicMed без данных конкретной МО.
#
# Остаётся: схема + справочники + структура индикаторов + меню/настройки.
# Не попадает (только данные; схема таблиц сохраняется):
#   талоны, ЭМД, рецепты, журналы, население ИСЗЛ, корпуса/отделения МО,
#   числовые планы, персонал МО, пациенты льготников и т.п.
#
# Использование (с хоста, где доступен pg_dump и Postgres):
#   export PGPASSWORD=...
#   ./scripts/dump_seed_database.sh \
#     -h localhost -p 55433 -U postgres -d mosaicmed \
#     -f backup/mosaicmed_seed_YYYYMMDD.dump
#
# Docker (пример):
#   docker compose --env-file .env.docker exec -T db \
#     pg_dump -U postgres -d mosaicmed -Fc \
#     $(./scripts/dump_seed_database.sh --print-excludes) \
#     > backup/mosaicmed_seed.dump
#
# Восстановление:
#   createdb / или пустая БД mosaicmed
#   pg_restore -U postgres -d mosaicmed --no-owner --clean --if-exists backup/mosaicmed_seed.dump
#   python manage.py migrate --noinput
#   # при необходимости: import_indicators_structure, import_basic_nsi
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXCLUDE_FILE="${ROOT}/scripts/seed_db_exclude_data_tables.txt"

print_excludes_only=0
if [[ "${1:-}" == "--print-excludes" ]]; then
  print_excludes_only=1
  shift
fi

if [[ ! -f "$EXCLUDE_FILE" ]]; then
  echo "ERROR: нет файла $EXCLUDE_FILE" >&2
  exit 1
fi

excludes=()
while IFS= read -r line || [[ -n "$line" ]]; do
  # trim / skip comments and empty
  line="${line%%#*}"
  line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$line" ]] && continue
  excludes+=(--exclude-table-data="${line}")
done < "$EXCLUDE_FILE"

if [[ "$print_excludes_only" -eq 1 ]]; then
  printf '%q ' "${excludes[@]}"
  echo
  exit 0
fi

OUT=""
PG_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)
      OUT="$2"
      shift 2
      ;;
    *)
      PG_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$OUT" ]]; then
  stamp="$(date +%Y%m%d_%H%M%S)"
  mkdir -p "${ROOT}/backup"
  OUT="${ROOT}/backup/mosaicmed_seed_${stamp}.dump"
fi

echo "[dump-seed] excluding data for ${#excludes[@]} table patterns from $EXCLUDE_FILE"
echo "[dump-seed] writing: $OUT"

# -Fc custom format (удобно для pg_restore)
# Схема всех таблиц + данные только неисключённых
pg_dump "${PG_ARGS[@]}" -Fc --no-owner --no-acl \
  "${excludes[@]}" \
  -f "$OUT"

echo "[dump-seed] done: $OUT"
echo "[dump-seed] restore example:"
echo "  pg_restore -U postgres -d mosaicmed --no-owner --clean --if-exists \"$OUT\""
