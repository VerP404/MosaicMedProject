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

# Остановка текущих процессов
pkill -f 'python3.12 manage.py runserver'
pkill -f 'python3.12 apps/analytical_app/index.py'
pkill -f 'python3.12 apps/chief_app/app.py'

# Перезапуск серверов в фоне
nohup python3.12 manage.py runserver 0.0.0.0:8000 &
nohup python3.12 apps/analytical_app/index.py &
nohup python3.12 apps/chief_app/app.py &
