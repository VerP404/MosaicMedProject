#!/bin/bash

# Определение лог-файла с временной меткой для текущего обновления
LOG_FILE="/tmp/update_MosaicMed_$(date +'%Y%m%d_%H%M%S').log"
echo "[INFO] Очистка /tmp..."
find /tmp -mindepth 1 ! -name "$(basename "$LOG_FILE")" -exec rm -rf {} +
echo "[INFO] Очистка /tmp завершена."
# Перенаправление STDOUT и STDERR только для этапов обновления, фоновые процессы будут иметь отдельное перенаправление
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=============================================="
echo "Начало выполнения скрипта обновления: $(date)"
echo "Лог обновления записывается в: $LOG_FILE"
echo "=============================================="

# Определение директории, в которой находится скрипт
echo "[INFO] Определяем директорию скрипта..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[INFO] SCRIPT_DIR = ${SCRIPT_DIR}"

# Переход в корневую директорию проекта (предполагается, что scripts находится в корне проекта)
echo "[INFO] Переход в корневую директорию проекта..."
cd "$SCRIPT_DIR/.." || { echo "[ERROR] Не удалось перейти в корневую директорию!"; exit 1; }
echo "[INFO] Текущая директория: $(pwd)"

# Активация виртуального окружения
echo "[INFO] Активация виртуального окружения..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Не удалось активировать виртуальное окружение!"
    exit 1
fi

# Обновление кода
echo "[INFO] Обновление кода (git pull)..."
git pull
if [ $? -ne 0 ]; then
    echo "[ERROR] git pull завершился с ошибкой!"
else
    echo "[INFO] git pull выполнен успешно."
fi

# Установка зависимостей
echo "[INFO] Установка зависимостей (pip install -r requirements/base.txt)..."
pip install -r requirements/base.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Ошибка при установке зависимостей!"
else
    echo "[INFO] Зависимости установлены."
fi

# Выполнение миграций
echo "[INFO] Выполнение миграций (python3.12 manage.py migrate)..."
python3.12 manage.py migrate
if [ $? -ne 0 ]; then
    echo "[ERROR] Миграции завершились с ошибкой!"
else
    echo "[INFO] Миграции выполнены успешно."
fi

# Импорт данных из JSON
echo "[INFO] Импорт данных (python3.12 manage.py data_import)..."
python3.12 manage.py data_import
if [ $? -ne 0 ]; then
    echo "[ERROR] Ошибка при импорте данных!"
else
    echo "[INFO] Импорт данных выполнен успешно."
fi

# Создание папок для файлов с данными
echo "[INFO] Создание папок (python3.12 mosaic_conductor/etl/create_folders.py)..."
python3.12 mosaic_conductor/etl/create_folders.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Не удалось создать папки для данных!"
else
    echo "[INFO] Папки успешно созданы."
fi

# Остановка текущих процессов
echo "[INFO] Остановка текущих процессов..."
pkill -f 'python3.12 manage.py runserver'
pkill -f 'python3.12 apps/analytical_app/index.py'
pkill -f 'python3.12 apps/chief_app/main.py'
pkill -f 'python3.12 start_dagster.py --host 0.0.0.0 --port 3000'
echo "[INFO] Основные процессы остановлены (если были запущены)."

echo "[INFO] Поиск и остановка процессов dagster-daemon..."
DAGSTER_DAEMON_PIDS=$(pgrep -f 'dagster-daemon run')
if [ -n "$DAGSTER_DAEMON_PIDS" ]; then
    echo "[INFO] Останавливаем процессы dagster-daemon: $DAGSTER_DAEMON_PIDS"
    kill $DAGSTER_DAEMON_PIDS
else
    echo "[INFO] Процессы dagster-daemon не найдены."
fi

echo "[INFO] Поиск и остановка процессов dagit..."
DAGIT_PIDS=$(pgrep -f 'dagit')
if [ -n "$DAGIT_PIDS" ]; then
    echo "[INFO] Останавливаем процессы dagit: $DAGIT_PIDS"
    kill $DAGIT_PIDS
else
    echo "[INFO] Процессы dagit не найдены."
fi

# Перезапуск серверов в фоне
echo "[INFO] Перезапуск серверов..."
nohup python3.12 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
nohup python3.12 apps/analytical_app/index.py > /dev/null 2>&1 &
nohup python3.12 apps/chief_app/main.py > /dev/null 2>&1 &
nohup python3.12 start_dagster.py --host 0.0.0.0 --port 3000 > /dev/null 2>&1 &

echo "=============================================="
echo "Скрипт обновления завершён: $(date)"
echo "=============================================="
