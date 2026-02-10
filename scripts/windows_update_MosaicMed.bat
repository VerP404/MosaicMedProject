@echo off
rem Skript obnovleniya i zapuska MosaicMed (analog update_MosaicMed.sh)
rem Sohranyayte fayl v UTF-8. Dlya kirillicy v konsoli: chcp 65001 i zapusk v tom zhe okne.

setlocal enabledelayedexpansion

rem ========== Kodirovka: UTF-8 dlya konsoli i dlya Python v drugom okruzhenii ==========
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

rem Лог с временной меткой (в папке скрипта или в TEMP)
set LOG_SUFFIX=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set LOG_SUFFIX=%LOG_SUFFIX: =0%
set "LOG_FILE=%~dp0update_MosaicMed_%LOG_SUFFIX%.log"

rem Директория скрипта и корень проекта
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PROJECT_ROOT=%SCRIPT_DIR%\.."

cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo [ERROR] Ne udalos pereyti v koren proekta: %PROJECT_ROOT%
    pause
    exit /b 1
)

rem Перенаправление вывода в лог и на экран (через tee-подобную запись в консоль + файл)
rem В bat нет tee; пишем в лог и дублируем echo в консоль
call :log "=============================================="
call :log "Nachalo obnovleniya: %date% %time%"
call :log "Log: %LOG_FILE%"
call :log "=============================================="

rem ----- Очистка старых логов Dagster storage (старше 14 дней) -----
call :log "[INFO] Ochistka staryh logov v mosaic_conductor\dagster_home\storage..."
set "STORAGE_DIR=%PROJECT_ROOT%\mosaic_conductor\dagster_home\storage"
if exist "%STORAGE_DIR%" (
    forfiles /p "%STORAGE_DIR%" /s /m *.* /d -14 /c "cmd /c del @path" 2>nul
    call :log "[INFO] Ochistka storage zavershena."
) else (
    call :log "[INFO] Papka storage ne naydena, propusk."
)

rem ----- PostgreSQL (Windows: опциональный запуск службы) -----
call :log "[INFO] Proverka PostgreSQL..."
net start | findstr /i "postgresql" >nul 2>&1
if errorlevel 1 (
    rem Попытка запустить типичную службу PostgreSQL
    net start postgresql-x64-16 2>nul
    net start postgresql-x64-15 2>nul
    net start postgresql-x64-14 2>nul
    net start PostgreSQL 2>nul
    if errorlevel 1 (
        call :log "[WARN] Sluzhba PostgreSQL ne zapushchena. Zapustite vruchnuyu esli nuzhna."
    ) else (
        call :log "[INFO] PostgreSQL zapushchen."
    )
) else (
    call :log "[INFO] PostgreSQL uzhe zapushchen."
)

rem ----- Проверка и добавление переменных в .env -----
call :log "[INFO] Proverka fayla .env..."
if not exist ".env" (
    echo # MosaicMed .env > .env
    call :log "[WARN] Sozdan fayl .env"
)
call :check_env "ISZL_USERNAME" "1"
call :check_env "ISZL_PASSWORD" "1"
call :check_env "ISZL_BROWSER" "chrome"
call :check_env "ISZL_BASE_URL" "http://10.36.29.2:8088/"
call :log "[INFO] Proverka .env zavershena."

rem ----- Активация виртуального окружения -----
call :log "[INFO] Aktivaciya virtualnogo okruzheniya..."
if not exist ".venv\Scripts\activate.bat" (
    call :log "[ERROR] Ne nayden .venv\Scripts\activate.bat"
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat

rem ----- Обновление кода -----
call :log "[INFO] git pull..."
git pull
if errorlevel 1 (
    call :log "[ERROR] git pull zavershilsya s oshibkoy!"
) else (
    call :log "[INFO] git pull uspeshno."
)

rem ----- Установка зависимостей -----
call :log "[INFO] Ustanovka zavisimostey..."
pip install -r requirements\base.txt
if errorlevel 1 (
    call :log "[ERROR] Oshibka pri ustanovke zavisimostey!"
) else (
    call :log "[INFO] Zavisimosti ustanovleny."
)

rem ----- Миграции -----
call :log "[INFO] Migracii (manage.py migrate)..."
python manage.py migrate
if errorlevel 1 (
    call :log "[ERROR] Migracii zavershilis s oshibkoy!"
) else (
    call :log "[INFO] Migracii vypolneny uspeshno."
)

rem ----- Создание папок для данных -----
call :log "[INFO] Sozdanie papok (create_folders.py)..."
python mosaic_conductor\etl\create_folders.py
if errorlevel 1 (
    call :log "[ERROR] Ne udalos sozdat papki dlya dannyh!"
) else (
    call :log "[INFO] Papki sozdany."
)

rem ----- Импорт структуры индикаторов -----
call :log "[INFO] Import struktury indikatorov..."
python manage.py import_indicators_structure apps/plan/fixtures/indicators_structure.json --update-existing
if errorlevel 1 (
    call :log "[ERROR] Import struktury indikatorov zavershilsya s oshibkoy!"
) else (
    call :log "[INFO] Struktura indikatorov importirovana."
)

rem ----- Остановка текущих процессов (те же сервисы, что в .sh) -----
call :log "[INFO] Ostanovka tekushchih processov..."

rem Порты: 8000 Django, 5000 analytical_app, 5001 chief_app, 5020 masterd_dashboard, 3000 dagit (start_dagster)
call :kill_port 8000
call :kill_port 5000
call :kill_port 5001
call :kill_port 5020
call :kill_port 3000

rem Остановка процессов dagster-daemon (могут не слушать порт)
taskkill /f /im dagster-daemon.exe 2>nul
taskkill /f /im dagit.exe 2>nul

call :log "[INFO] Processy ostanovleny."

rem ----- Запуск серверов в отдельных окнах -----
call :log "[INFO] Zapusk serverov..."

start "Django runserver 8000" /min python manage.py runserver 0.0.0.0:8000
start "Analytical app 5000" /min python apps\analytical_app\index.py
start "Chief app 5001" /min python apps\chief_app\main.py
start "MasterD dashboard 5020" /min python apps\masterd_dashboard\app.py --host 0.0.0.0 --port 5020
start "Dagster (dagit) 3000" /min python start_dagster.py --host 0.0.0.0 --port 3000

call :log "=============================================="
call :log "Obnovlenie zaversheno: %date% %time%"
call :log "=============================================="

echo.
echo Gotovo. Log: %LOG_FILE%
pause
exit /b 0

rem ========== Подпрограмма: запись в лог и в консоль ==========
:log
echo %* >> "%LOG_FILE%"
echo %*
exit /b 0

rem ========== Подпрограмма: добавить переменную в .env если нет ==========
:check_env
set "VAR_NAME=%~1"
set "VAR_VAL=%~2"
findstr /b /c:"%VAR_NAME%=" .env >nul 2>&1
if errorlevel 1 (
    echo. >> .env
    echo # %VAR_NAME% >> .env
    echo %VAR_NAME%=%VAR_VAL% >> .env
    call :log "[INFO] Dobavlena peremennaya %VAR_NAME%"
)
exit /b 0

rem ========== Подпрограмма: завершить процесс по порту ==========
:kill_port
set "PORT=%~1"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    set "PID=%%a"
    if not "!PID!"=="" (
        call :log "[INFO] Zavershenie processa na portu %PORT% (PID !PID!)"
        taskkill /f /pid !PID! 2>nul
    )
)
exit /b 0
