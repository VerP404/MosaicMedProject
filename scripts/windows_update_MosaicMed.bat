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

rem Остановка текущих процессов
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq manage.py runserver" /fo csv /nh') do taskkill /pid %%a
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq index.py" /fo csv /nh') do taskkill /pid %%a
for /f "tokens=5" %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq app.py" /fo csv /nh') do taskkill /pid %%a

rem Перезапуск серверов в фоне
start "" python manage.py runserver 0.0.0.0:8000
start "" python apps\analytical_app\index.py
start "" python apps\chief_app\app.py

rem Деактивация виртуального окружения
deactivate.bat
