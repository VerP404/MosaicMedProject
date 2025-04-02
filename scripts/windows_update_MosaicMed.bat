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

rem Создание папок для файлов с данными
python manage.py mosaic_conductor\etl\create_folders.py

rem Импорт данных из JSON
python manage.py data_import

rem Остановка текущих процессов
for /f "tokens=2 delims=," %%a in ('wmic process where "name='python.exe' and commandline like '%%manage.py runserver%%'" get processid /format:csv') do (
    if not "%%a"=="ProcessId" taskkill /pid %%a /f
)

for /f "tokens=2 delims=," %%a in ('wmic process where "name='python.exe' and commandline like '%%index.py%%'" get processid /format:csv') do (
    if not "%%a"=="ProcessId" taskkill /pid %%a /f
)

for /f "tokens=2 delims=," %%a in ('wmic process where "name='python.exe' and commandline like '%%main.py%%'" get processid /format:csv') do (
    if not "%%a"=="ProcessId" taskkill /pid %%a /f
)
rem Перезапуск серверов в фоне
start "" python manage.py runserver 0.0.0.0:8000
start "" python apps\analytical_app\index.py
start "" python apps\chief_app\main.py

rem Деактивация виртуального окружения
deactivate.bat
