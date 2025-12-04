#!/bin/bash

# Определение лог-файла с временной меткой для текущего обновления
LOG_FILE="/tmp/update_MosaicMed_$(date +'%Y%m%d_%H%M%S').log"

# Перенаправление STDOUT и STDERR только для этапов обновления, фоновые процессы будут иметь отдельное перенаправление
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=============================================="
echo "Начало выполнения скрипта обновления: $(date)"
echo "Лог обновления записывается в: $LOG_FILE"
echo "=============================================="

echo "[INFO] Очистка /tmp..."
find /tmp -mindepth 1 -not -name "$(basename "$LOG_FILE")" -exec rm -rf {} + 2>/dev/null
echo "[INFO] Очистка /tmp завершена."

echo "[INFO] Очистка старых логов в папке storage..."
# Очистка старых логов (старше 14 дней), исключая важные файлы
find mosaic_conductor/dagster_home/storage -type f \
    -not -path "./__repository__*" \
    -not -name "index.db" \
    -not -name "runs.db" \
    -not -name "schedules.db" \
    -mtime +14 \
    -delete 2>/dev/null
echo "[INFO] Очистка логов в storage завершена."

echo "[INFO] Проверка состояния PostgreSQL..."

# Проверка состояния
if systemctl is-active --quiet postgresql; then
    echo "[INFO] PostgreSQL уже запущен."
else
    echo "[WARN] PostgreSQL не запущен. Попытка запуска..."
    if sudo systemctl start postgresql; then
        echo "[INFO] PostgreSQL успешно запущен."
    else
        echo "[ERROR] Не удалось запустить PostgreSQL. Проверьте конфигурацию службы."
        systemctl status postgresql --no-pager
        exit 1
    fi
fi

# Определение директории, в которой находится скрипт
echo "[INFO] Определяем директорию скрипта..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[INFO] SCRIPT_DIR = ${SCRIPT_DIR}"

# Переход в корневую директорию проекта (предполагается, что scripts находится в корне проекта)
echo "[INFO] Переход в корневую директорию проекта..."
cd "$SCRIPT_DIR/.." || { echo "[ERROR] Не удалось перейти в корневую директорию!"; exit 1; }
echo "[INFO] Текущая директория: $(pwd)"

# Функция для проверки и добавления переменной в .env файл
check_and_add_env_variable() {
    local env_file=".env"
    local var_name=$1
    local var_value=$2
    local var_comment=$3

    echo "[INFO] Проверка наличия переменной $var_name в $env_file..."
    
    # Проверяем существование файла .env
    if [ ! -f "$env_file" ]; then
        echo "[WARN] Файл $env_file не найден, создаем новый..."
        touch "$env_file"
    fi
    
    # Проверяем, есть ли переменная в файле .env
    if grep -q "^$var_name=" "$env_file"; then
        echo "[INFO] Переменная $var_name уже существует в $env_file, пропускаем."
    else
        echo "[INFO] Добавляем переменную $var_name=$var_value в $env_file..."
        
        # Добавляем комментарий, если он указан
        if [ -n "$var_comment" ]; then
            echo -e "\n# $var_comment" >> "$env_file"
        fi
        
        # Добавляем переменную
        echo "$var_name=$var_value" >> "$env_file"
        echo "[INFO] Переменная $var_name добавлена."
    fi
}

# Проверка и добавление необходимых переменных окружения
echo "[INFO] Проверка и обновление файла .env..."

# Список переменных для проверки в формате: имя переменной, значение по умолчанию, комментарий
check_and_add_env_variable "ISZL_USERNAME" "1" "Пользователь"
check_and_add_env_variable "ISZL_PASSWORD" "1" "Пароль"
check_and_add_env_variable "ISZL_BROWSER" "chrome" "браузер"
check_and_add_env_variable "ISZL_BASE_URL" "http://10.36.29.2:8088/" "url"

echo "[INFO] Проверка файла .env завершена."

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

# Создание папок для файлов с данными
echo "[INFO] Создание папок (python3.12 mosaic_conductor/etl/create_folders.py)..."
python3.12 mosaic_conductor/etl/create_folders.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Не удалось создать папки для данных!"
else
    echo "[INFO] Папки успешно созданы."
fi

# Импорт структуры индикаторов
echo "[INFO] Импорт структуры индикаторов (python3.12 manage.py import_indicators_structure)..."
python3.12 manage.py import_indicators_structure apps/plan/fixtures/indicators_structure.json --update-existing
if [ $? -ne 0 ]; then
    echo "[ERROR] Импорт структуры индикаторов завершился с ошибкой!"
else
    echo "[INFO] Структура индикаторов успешно импортирована."
fi

# Остановка текущих процессов
echo "[INFO] Остановка текущих процессов..."
pkill -f 'python3.12 manage.py runserver' 2>/dev/null
pkill -f 'python3.12 apps/analytical_app/index.py' 2>/dev/null
pkill -f 'python3.12 apps/chief_app/main.py' 2>/dev/null
pkill -f 'python3.12 apps/masterd_dashboard/app.py' 2>/dev/null
pkill -f 'python3.12 start_dagster.py --host 0.0.0.0 --port 3000' 2>/dev/null
echo "[INFO] Основные процессы остановлены (если были запущены)."

echo "[INFO] Поиск и остановка процессов dagster-daemon..."
DAGSTER_DAEMON_PIDS=$(pgrep -f 'dagster-daemon run')
if [ -n "$DAGSTER_DAEMON_PIDS" ]; then
    echo "[INFO] Останавливаем процессы dagster-daemon: $DAGSTER_DAEMON_PIDS"
    kill $DAGSTER_DAEMON_PIDS 2>/dev/null
else
    echo "[INFO] Процессы dagster-daemon не найдены."
fi

echo "[INFO] Поиск и остановка процессов dagit..."
DAGIT_PIDS=$(pgrep -f 'dagit')
if [ -n "$DAGIT_PIDS" ]; then
    echo "[INFO] Останавливаем процессы dagit: $DAGIT_PIDS"
    kill $DAGIT_PIDS 2>/dev/null
else
    echo "[INFO] Процессы dagit не найдены."
fi

# Перезапуск серверов в фоне
echo "[INFO] Перезапуск серверов..."
nohup python3.12 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
nohup python3.12 apps/analytical_app/index.py > /dev/null 2>&1 &
nohup python3.12 apps/chief_app/main.py > /dev/null 2>&1 &
nohup python3.12 apps/masterd_dashboard/app.py --host 0.0.0.0 --port 5020 > /dev/null 2>&1 &
nohup python3.12 start_dagster.py --host 0.0.0.0 --port 3000 > /dev/null 2>&1 &

echo "=============================================="
echo "Скрипт обновления завершён: $(date)"
echo "=============================================="
