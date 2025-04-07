import os
from dagster import graph, in_process_executor, Field, Array, String, schedule

from mosaic_conductor.selenium.wo.config import OMS_BROWSER, OMS_BASE_URL
from mosaic_conductor.selenium.wo.ops.wo_start import open_site_op
from mosaic_conductor.selenium.wo.ops.wo_filter import filter_input_op
from mosaic_conductor.selenium.wo.ops.wo_download import move_downloaded_file_op
from mosaic_conductor.selenium.wo.selenium_driver import selenium_driver_resource


def create_download_job(
        job_name: str,
        target_url: str,
        browser: str,
        temp_download_folder: str,
        destination_folders: list,
        file_pattern: str,
        filter_input_op_fn,  # функция-оп для фильтрации, например filter_input_op или другая
        extra_filter_config: dict = None,
):
    """
    Создает Dagster job для скачивания файлов из веб-приложения.

    :param job_name: имя job.
    :param target_url: URL для открытия (логин, главная страница и т.д.).
    :param browser: тип браузера ("chrome" или "firefox").
    :param temp_download_folder: временная папка для загрузок.
    :param destination_folders: список конечных папок для копирования файла.
    :param file_pattern: шаблон для поиска загруженного файла (например, "journal_20*.csv").
    :param filter_input_op_fn: оп-функция, отвечающая за установку фильтров на нужной странице.
    :param extra_filter_config: дополнительные настройки для фильтра (если требуются).
    """

    @graph
    def download_graph():
        site_url = open_site_op()
        filter_result = filter_input_op_fn(site_url)
        move_downloaded_file_op(filter_result)

    job_config = {
        "resources": {
            "selenium_driver": {
                "config": {
                    "browser": browser,
                    "destination_folder": destination_folders[0],
                    "temp_download_folder": temp_download_folder,
                    "target_url": target_url
                }
            }
        },
        "ops": {
            filter_input_op_fn.__name__: {"config": extra_filter_config or {}},
            "move_downloaded_file_op": {
                "config": {
                    "file_pattern": file_pattern,
                    "timeout": 60,
                    "temp_download_folder": temp_download_folder,
                    "destination_folders": destination_folders
                }
            }
        }
    }
    return download_graph.to_job(
        name=job_name,
        resource_defs={"selenium_driver": selenium_driver_resource},
        config=job_config,
        executor_def=in_process_executor,
    )


# Конечная папка для хранения скачанного файла (OMS_TALON_FOLDER)
OMS_TALON_FOLDER = os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "old")
ADDITIONAL_FOLDER = os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "new")

# Временная папка для загрузки (например, внутри проекта)
TEMP_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "talon")

wo_talon_job = create_download_job(
    job_name="wo_talon_job",
    target_url=OMS_BASE_URL,
    browser=OMS_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "talon"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "old"),
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "new")
    ],
    file_pattern="journal_202*.csv",
    filter_input_op_fn=filter_input_op,  # передаем стандартную функцию фильтрации
    extra_filter_config={},  # если нужны дополнительные настройки для фильтрации
)


#
# @graph
# def wo_talon_graph():
#     site_url = open_site_op()
#     filter_result = filter_input_op(site_url)
#     move_downloaded_file_op(filter_result)
#
#
# wo_talon_job = wo_talon_graph.to_job(
#     resource_defs={
#         "selenium_driver": selenium_driver_resource
#     },
#     config={
#         "resources": {
#             "selenium_driver": {
#                 "config": {
#                     "browser": OMS_BROWSER,
#                     # Конечная папка (используется, если понадобится, но в нашем случае в move_downloaded_file_op мы работаем со списком)
#                     "destination_folder": OMS_TALON_FOLDER,
#                     # Временная папка для загрузки
#                     "temp_download_folder": TEMP_DOWNLOAD_FOLDER,
#                     "target_url": OMS_BASE_URL
#                 }
#             }
#         },
#         "ops": {
#             "filter_input_op": {
#                 "config": {
#                     # Параметры фильтра можно задать, если необходимо
#                 }
#             },
#             "move_downloaded_file_op": {
#                 "config": {
#                     "file_pattern": "journal_20*.csv",  # Шаблон файла
#                     "timeout": 60,
#                     "temp_download_folder": TEMP_DOWNLOAD_FOLDER,
#                     "destination_folders": [OMS_TALON_FOLDER, ADDITIONAL_FOLDER]
#                 }
#             }
#         }
#     },
#     executor_def=in_process_executor,
# )


@schedule(
    cron_schedule="0 * * * *",
    job=wo_talon_job,
    execution_timezone="Europe/Moscow"
)
def wo_talon_schedule(_context):
    return {}
