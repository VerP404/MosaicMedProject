#!/bin/bash

# Определение директории, в которой находится скрипт
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Переход в корневую директорию проекта (предполагается, что scripts находится в корне проекта)
cd "$SCRIPT_DIR/.." || exit

# Активация виртуального окружения
source .venv/bin/activate

# Обновление кода
git pull

# Установка зависимостей
pip install -r requirements/base.txt

# Выполнение миграций
python3.12 manage.py migrate

# Импорт данных из JSON
python3.12 manage.py data_import

# Создание папок для файлов с данными
python3.12 mosaic_conductor/etl/create_folders.py

# Определение директорий для PID-файлов и логов
PID_DIR="./pids"
LOG_DIR="./logs"

mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

# Функция для корректного завершения процесса по PID-файлу
kill_process() {
  local pidfile="$1"
  if [[ -f "$pidfile" ]]; then
    PID=$(cat "$pidfile")
    if kill -0 "$PID" 2>/dev/null; then
      echo "Завершаем процесс с PID $PID (файл $pidfile)"
      kill "$PID"
      sleep 2
      if kill -0 "$PID" 2>/dev/null; then
        echo "Процесс $PID не завершился, принудительное завершение"
        kill -9 "$PID"
      fi
    else
      echo "Процесс из файла $pidfile не найден"
    fi
    rm -f "$pidfile"
  fi
}

# Завершение запущенных процессов, если PID-файлы существуют
kill_process "$PID_DIR/django.pid"
kill_process "$PID_DIR/analytical.pid"
kill_process "$PID_DIR/chief.pid"
kill_process "$PID_DIR/dagster.pid"

# Перезапуск процессов с записью PID в соответствующие файлы

# Запуск сервера Django
nohup python3.12 manage.py runserver 0.0.0.0:8000 > "$LOG_DIR/django.log" 2>&1 &
echo $! > "$PID_DIR/django.pid"

# Запуск аналитического приложения
nohup python3.12 apps/analytical_app/index.py > "$LOG_DIR/analytical.log" 2>&1 &
echo $! > "$PID_DIR/analytical.pid"

# Запуск приложения Chief
nohup python3.12 apps/chief_app/main.py > "$LOG_DIR/chief.log" 2>&1 &
echo $! > "$PID_DIR/chief.pid"

# Запуск Dagster
nohup python3.12 start_dagster.py --host 0.0.0.0 --port 3000 > "$LOG_DIR/dagster.log" 2>&1 &
echo $! > "$PID_DIR/dagster.pid"
