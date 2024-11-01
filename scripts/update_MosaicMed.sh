#!/bin/bash

# Переход в директорию проекта (относительный путь)
cd "$(dirname "$0")/.." || exit

# Активация виртуального окружения
source .venv/bin/activate


# Обновление кода
git pull

# Выполнение миграций
python3.12 manage.py migrate

# Остановка текущих процессов
pkill -f 'python3.12 manage.py runserver'
pkill -f 'python3.12 apps/analytical_app/index.py'

# Перезапуск серверов в фоне
nohup python3.12 manage.py runserver 0.0.0.0:8000 &
nohup python3.12 apps/analytical_app/index.py &
