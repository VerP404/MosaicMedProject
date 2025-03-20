@echo off
rem Определение директории скрипта
set SCRIPT_DIR=%~dp0

rem Переход в корневую директорию проекта
cd /d %SCRIPT_DIR%\..

rem Активация виртуального окружения
call .venv\Scripts\activate.bat

rem Обновление кода из репозитория
git pull

rem Установка зависимостей
pip install -r requirements\base.txt

rem Выполнение миграций
python manage.py migrate

rem Импорт данных из JSON
python manage.py data_import

rem Остановка текущих процессов проекта
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq manage.py runserver" /fo csv /nh') do taskkill /pid %%a
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq index.py" /fo csv /nh') do taskkill /pid %%a
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq main.py" /fo csv /nh') do taskkill /pid %%a

rem Остановка процесса дагстера, если он запущен (уберите амперсанд в шаблоне)
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq start_dagster.py --host 0.0.0.0 --port 3000" /fo csv /nh') do taskkill /pid %%a

rem Перезапуск серверов проекта в фоне
start "" python manage.py runserver 0.0.0.0:8000
start "" python apps\analytical_app\index.py
start "" python apps\chief_app\main.py

rem Запуск дагстера (daemon и UI) через универсальный скрипт start_dagster.py
start "" python start_dagster.py --host 0.0.0.0 --port 3000

rem Деактивация виртуального окружения
call deactivate.bat
