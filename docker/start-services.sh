#!/bin/sh
set -eu

LOG_DIR=/app/logs
mkdir -p "$LOG_DIR"

stop_services() {
  echo "[start-services] Stopping processes..."
  pkill -f 'manage.py runserver' 2>/dev/null || true
  pkill -f 'apps/analytical_app/index.py' 2>/dev/null || true
  pkill -f 'apps/chief_app/main.py' 2>/dev/null || true
  pkill -f 'apps/masterd_dashboard/app.py' 2>/dev/null || true
  pkill -f 'start_dagster.py' 2>/dev/null || true
  pkill -f 'apps/dash_dn/index.py' 2>/dev/null || true
  pkill -f 'dagster-daemon run' 2>/dev/null || true
  pkill -f 'dagit' 2>/dev/null || true
  sleep 2
}

trap 'stop_services; exit 0' INT TERM

stop_services

echo "[start-services] Django :8000"
python manage.py runserver 0.0.0.0:8000 >>"$LOG_DIR/django.log" 2>&1 &
PID_DJ=$!

echo "[start-services] analytical_app :${PORT_DASH:-5000}"
python apps/analytical_app/index.py >>"$LOG_DIR/analytical_app.log" 2>&1 &
PID_AN=$!

echo "[start-services] chief_app :${PORT_DASH_CHIEF:-5001}"
python apps/chief_app/main.py >>"$LOG_DIR/chief_app.log" 2>&1 &
PID_CH=$!

echo "[start-services] masterd_dashboard :${MASTERD_PORT:-5020}"
HOST=0.0.0.0 PORT=${MASTERD_PORT:-5020} python apps/masterd_dashboard/app.py >>"$LOG_DIR/masterd.log" 2>&1 &
PID_MD=$!

echo "[start-services] Dagster :${DAGSTER_PORT:-3000}"
python start_dagster.py --host 0.0.0.0 --port "${DAGSTER_PORT:-3000}" >>"$LOG_DIR/dagster.log" 2>&1 &
PID_DG=$!

echo "[start-services] dash_dn :${PORT_DASH_DN:-7777}"
python apps/dash_dn/index.py >>"$LOG_DIR/dash_dn.log" 2>&1 &
PID_DN=$!

echo "[start-services] All services started. Logs: $LOG_DIR"
echo "[start-services] PIDs: django=$PID_DJ analytical=$PID_AN chief=$PID_CH masterd=$PID_MD dagster=$PID_DG dash_dn=$PID_DN"

# Держим PID 1 живым, пока жив Django (основной процесс)
while kill -0 "$PID_DJ" 2>/dev/null; do
  sleep 5
done

echo "[start-services] Django exited, shutting down..." >&2
stop_services
exit 1
