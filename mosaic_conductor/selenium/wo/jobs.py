import os
from dagster import graph, in_process_executor, Field, Array, String

from mosaic_conductor.selenium.wo.config import OMS_BROWSER, OMS_BASE_URL
from mosaic_conductor.selenium.wo.ops.wo_start import open_site_op
from mosaic_conductor.selenium.wo.ops.wo_filter import filter_input_op
from mosaic_conductor.selenium.wo.ops.wo_download import move_downloaded_file_op
from mosaic_conductor.selenium.wo.selenium_driver import selenium_driver_resource

# Конечная папка для хранения скачанного файла (OMS_TALON_FOLDER)
OMS_TALON_FOLDER = os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "old")
ADDITIONAL_FOLDER = os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "new")

# Временная папка для загрузки (например, внутри проекта)
TEMP_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "talon")


@graph
def wo_talon_graph():
    site_url = open_site_op()
    filter_result = filter_input_op(site_url)
    move_downloaded_file_op(filter_result)


wo_talon_job = wo_talon_graph.to_job(
    resource_defs={
        "selenium_driver": selenium_driver_resource
    },
    config={
        "resources": {
            "selenium_driver": {
                "config": {
                    "browser": OMS_BROWSER,
                    # Конечная папка (используется, если понадобится, но в нашем случае в move_downloaded_file_op мы работаем со списком)
                    "destination_folder": OMS_TALON_FOLDER,
                    # Временная папка для загрузки
                    "temp_download_folder": TEMP_DOWNLOAD_FOLDER,
                    "target_url": OMS_BASE_URL
                }
            }
        },
        "ops": {
            "filter_input_op": {
                "config": {
                    # Параметры фильтра можно задать, если необходимо
                }
            },
            "move_downloaded_file_op": {
                "config": {
                    "file_pattern": "journal_20*.csv",  # Шаблон файла
                    "timeout": 60,
                    "temp_download_folder": TEMP_DOWNLOAD_FOLDER,
                    "destination_folders": [OMS_TALON_FOLDER, ADDITIONAL_FOLDER]
                }
            }
        }
    },
    executor_def=in_process_executor,
)
