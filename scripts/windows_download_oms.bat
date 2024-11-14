@echo off

rem Активация виртуального окружения
call C:\MosaicMedProject\.venv\Scripts\activate

rem Добавление пути к модулю dash_apps в PYTHONPATH
set "PYTHONPATH=%PYTHONPATH%;C:\MosaicMedProject\"

rem Запуск Django-команды
python "C:\MosaicMedProject\manage.py load_data_oms"

rem Деактивация виртуального окружения
python "C:\MosaicMedProject\manage.py" load_data_oms

exit
