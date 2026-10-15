#!/bin/bash
# Полный перезапуск Dagster (webserver + daemon + code location gRPC).
# Чинит DagsterUserCodeUnreachableError / UNAVAILABLE на unix:/tmp/... без ребута ОС.
#
# Использование (из корня проекта или откуда угодно):
#   bash scripts/restart_dagster.sh
#   bash scripts/restart_dagster.sh --port 3000
#   bash scripts/restart_dagster.sh --status   # только статус, без рестарта

set -euo pipefail

PORT="${DAGSTER_PORT:-3000}"
STATUS_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --status) STATUS_ONLY=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--port 3000] [--status]"
      exit 0
      ;;
    *)
      echo "[ERROR] Неизвестный аргумент: $1" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

LOG_DIR="${PROJECT_ROOT}/mosaic_conductor/dagster_home"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/dagster.log"

# Python: предпочитаем venv проекта
if [[ -x "${PROJECT_ROOT}/.venv/bin/python3.12" ]]; then
  PY="${PROJECT_ROOT}/.venv/bin/python3.12"
elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
  PY="${PROJECT_ROOT}/.venv/bin/python"
elif command -v python3.12 >/dev/null 2>&1; then
  PY="$(command -v python3.12)"
else
  PY="$(command -v python3)"
fi

echo "=============================================="
echo "Dagster restart: $(date)"
echo "PROJECT_ROOT=${PROJECT_ROOT}"
echo "PYTHON=${PY}"
echo "PORT=${PORT}"
echo "LOG=${LOG_FILE}"
echo "=============================================="

show_status() {
  echo "[STATUS] процессы:"
  if pgrep -af 'start_dagster\.py|dagster-webserver|dagster-daemon|dagster api grpc' >/dev/null 2>&1; then
    pgrep -af 'start_dagster\.py|dagster-webserver|dagster-daemon|dagster api grpc' || true
  else
    echo "  (нет)"
  fi
  if command -v ss >/dev/null 2>&1; then
    echo "[STATUS] порт ${PORT}:"
    ss -ltnp "sport = :${PORT}" 2>/dev/null || true
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
  fi
}

if [[ "${STATUS_ONLY}" -eq 1 ]]; then
  show_status
  exit 0
fi

kill_dagster() {
  echo "[INFO] Останавливаем Dagster..."
  # Сначала мягко
  pkill -f 'start_dagster\.py' 2>/dev/null || true
  pkill -f 'dagster-webserver' 2>/dev/null || true
  pkill -f 'dagster-daemon' 2>/dev/null || true
  pkill -f 'dagster api grpc' 2>/dev/null || true
  # xvfb-run обёртки из start_dagster.py
  pkill -f 'xvfb-run .*dagster' 2>/dev/null || true
  sleep 2

  # Если остались — force
  if pgrep -af 'start_dagster\.py|dagster-webserver|dagster-daemon|dagster api grpc' >/dev/null 2>&1; then
    echo "[WARN] Остались процессы — kill -9"
    pkill -9 -f 'start_dagster\.py' 2>/dev/null || true
    pkill -9 -f 'dagster-webserver' 2>/dev/null || true
    pkill -9 -f 'dagster-daemon' 2>/dev/null || true
    pkill -9 -f 'dagster api grpc' 2>/dev/null || true
    pkill -9 -f 'xvfb-run .*dagster' 2>/dev/null || true
    sleep 1
  fi

  # Старые unix-сокеты code location в /tmp (источник UNAVAILABLE)
  find /tmp -maxdepth 1 -type s -name 'tmp*' -user "$(id -un)" -delete 2>/dev/null || true

  if pgrep -af 'start_dagster\.py|dagster-webserver|dagster-daemon|dagster api grpc' >/dev/null 2>&1; then
    echo "[ERROR] Не удалось остановить все процессы Dagster:" >&2
    pgrep -af 'start_dagster\.py|dagster-webserver|dagster-daemon|dagster api grpc' || true
    exit 1
  fi
  echo "[INFO] Dagster остановлен."
}

start_dagster() {
  if [[ ! -f "${PROJECT_ROOT}/start_dagster.py" ]]; then
    echo "[ERROR] Нет ${PROJECT_ROOT}/start_dagster.py" >&2
    exit 1
  fi
  if [[ ! -f "${PROJECT_ROOT}/workspace.yaml" ]]; then
    echo "[ERROR] Нет ${PROJECT_ROOT}/workspace.yaml" >&2
    exit 1
  fi

  echo "[INFO] Запуск start_dagster.py --host 0.0.0.0 --port ${PORT}"
  # Важно: не в /dev/null — иначе диагностировать нечего
  nohup "${PY}" start_dagster.py --host 0.0.0.0 --port "${PORT}" \
    >>"${LOG_FILE}" 2>&1 &
  echo $! >"${LOG_DIR}/start_dagster.pid"
  echo "[INFO] PID start_dagster=$(cat "${LOG_DIR}/start_dagster.pid")"
}

wait_ready() {
  echo "[INFO] Ждём готовности UI :${PORT} (до 45с)..."
  local i
  for i in $(seq 1 45); do
    if curl -fsS -o /dev/null --connect-timeout 1 "http://127.0.0.1:${PORT}/" 2>/dev/null; then
      echo "[OK] UI отвечает на http://127.0.0.1:${PORT}/"
      return 0
    fi
    # процесс мог сразу упасть
    if ! pgrep -f 'start_dagster\.py' >/dev/null 2>&1; then
      echo "[ERROR] start_dagster.py уже не запущен. Хвост лога:" >&2
      tail -80 "${LOG_FILE}" >&2 || true
      exit 1
    fi
    sleep 1
  done
  echo "[WARN] UI ещё не ответил за 45с. Хвост лога:"
  tail -80 "${LOG_FILE}" || true
  show_status
  return 1
}

kill_dagster
start_dagster
wait_ready || true
show_status

echo "=============================================="
echo "Готово. Лог: ${LOG_FILE}"
echo "В UI нажмите Reload definitions, затем Launch."
echo "=============================================="
