from dagster import op, Field, String
import os
import shutil


@op(
    config_schema={
        "destination_folder": Field(String, description="Папка для сохранения файла"),
        "new_file_name": Field(String, default_value="downloaded_file.csv", description="Новое имя файла")
    }
)
def post_process_op(context, input_file: str):
    destination_folder = context.op_config["destination_folder"]
    new_file_name = context.op_config["new_file_name"]

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    new_file_path = os.path.join(destination_folder, new_file_name)

    try:
        shutil.move(input_file, new_file_path)
        context.log.info(f"Файл перемещен в: {new_file_path}")
    except Exception as e:
        context.log.error(f"Ошибка перемещения файла: {e}")
        raise e

    return new_file_path
