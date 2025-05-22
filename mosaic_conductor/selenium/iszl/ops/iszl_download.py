import os
import glob
import time
import shutil
from dagster import op, Field, String, Int, List, Array


@op(
    config_schema={
        "file_pattern": Field(String, is_required=False, default_value="*.csv"),
        "timeout": Field(Int, is_required=False, default_value=60),
        "temp_download_folder": Field(String, is_required=True),
        "destination_folders": Field(Array(String), is_required=True)
    }
)
def move_iszl_downloaded_file_op(context, previous_step_result: str = "") -> str:
    """
    Операция для перемещения скачанного файла из временной директории в конечную
    """
    temp_download_folder = context.op_config["temp_download_folder"]
    destination_folders = context.op_config["destination_folders"]
    file_pattern = context.op_config["file_pattern"]
    timeout = context.op_config["timeout"]

    context.log.info(f"Ищем файл в {temp_download_folder} по шаблону {file_pattern} в течение {timeout} сек")
    end_time = time.time() + timeout
    found_file = None

    while time.time() < end_time:
        pattern = os.path.join(temp_download_folder, file_pattern)
        files = glob.glob(pattern)
        if files:
            # Выбираем самый новый файл
            found_file = max(files, key=os.path.getmtime)
            context.log.info(f"Найден файл: {found_file}")
            break
        time.sleep(2)

    if not found_file:
        raise Exception(f"Файл не найден в указанное время в папке {temp_download_folder} по шаблону {file_pattern}.")

    # Для каждого пути из списка destination_folders копируем найденный файл
    for dest in destination_folders:
        if not os.path.exists(dest):
            os.makedirs(dest)
            context.log.info(f"Папка {dest} создана.")
        filename = os.path.basename(found_file)
        destination_path = os.path.join(dest, filename)
        shutil.copy(found_file, destination_path)
        context.log.info(f"Файл скопирован в {destination_path}")

    # Удаляем исходный файл после копирования
    os.remove(found_file)
    context.log.info(f"Исходный файл {found_file} удалён из временной папки.")
    return f"Файл скопирован в папки: {destination_folders}"
