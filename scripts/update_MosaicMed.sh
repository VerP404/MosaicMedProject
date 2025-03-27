#!/bin/bash

# Определение директории, в которой находится скрипт
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Переход в корневую директорию проекта (предполагается, что скрипт находится в корне проекта)
cd "$SCRIPT_DIR/.." || exit

echo "Активируем виртуальное окружение..."
source .venv/bin/activate

echo "Обновляем код..."
git pull

echo "Устанавливаем зависимости..."
pip install -r requirements/base.txt

echo "Применяем миграции..."
python3.12 manage.py migrate

echo "Импортируем данные из JSON..."
python3.12 manage.py data_import

echo "Создаем необходимые папки..."
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
      echo "Завершаем процесс с PID $PID (файл $pidfile)..."
      kill "$PID"
      sleep 2
      if kill -0 "$PID" 2>/dev/null; then
        echo "Процесс $PID не завершился, выполняем принудительное завершение..."
        kill -9 "$PID"
      else
        echo "Процесс $PID успешно завершен."
      fi
    else
      echo "Процесс из файла $pidfile не найден."
    fi
    rm -f "$pidfile"
  else
    echo "Файл $pidfile не существует, пропускаем."
  fi
}

echo "Останавливаем запущенные процессы (если имеются)..."
kill_process "$PID_DIR/django.pid"
kill_process "$PID_DIR/analytical.pid"
kill_process "$PID_DIR/chief.pid"
kill_process "$PID_DIR/dagster.pid"

# Функция для запуска процесса с nohup и сохранением его PID
start_process() {
  local cmd="$1"
  local pidfile="$2"
  local logfile="$3"
  echo "Запускаем: $cmd"
  nohup $cmd > "$logfile" 2>&1 &
  NEW_PID=$!
  echo "Новый процесс запущен с PID $NEW_PID"
  echo $NEW_PID > "$pidfile"
}

echo "Перезапускаем процессы..."

# Запуск сервера Django
start_process "python3.12 manage.py runserver 0.0.0.0:8000" "$PID_DIR/django.pid" "$LOG_DIR/django.log"

# Запуск аналитического приложения
start_process "python3.12 apps/analytical_app/index.py" "$PID_DIR/analytical.pid" "$LOG_DIR/analytical.log"

# Запуск приложения Chief
start_process "python3.12 apps/chief_app/main.py" "$PID_DIR/chief.pid" "$LOG_DIR/chief.log"

# Запуск Dagster
start_process "python3.12 start_dagster.py --host 0.0.0.0 --port 3000" "$PID_DIR/dagster.pid" "$LOG_DIR/dagster.log"

echo "Все процессы перезапущены."
