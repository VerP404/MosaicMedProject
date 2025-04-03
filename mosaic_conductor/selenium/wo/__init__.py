import os
from dagster import graph
from mosaic_conductor.selenium.wo.ops.set_filters import set_filters_op
from mosaic_conductor.selenium.wo.ops.download import download_file_op
from mosaic_conductor.selenium.wo.ops.post_process import post_process_op
from mosaic_conductor.selenium.wo.driver_resource import selenium_driver_resource
from mosaic_conductor.selenium.wo.config import TARGET_URL, DEFAULT_BROWSER, USERNAME, PASSWORD

from mosaic_conductor.selenium.wo.ops.authenticate import authenticate_op


@graph
def selenium_etl_graph():
    # Этап 1: авторизация
    _ = authenticate_op()
    # Этап 2: установка фильтров
    _ = set_filters_op()
    # Этап 3: скачивание файла
    downloaded_file = download_file_op()
    # Этап 4: пост-обработка файла
    processed_file = post_process_op(downloaded_file)
    return processed_file


# Преобразуем граф в job с ресурсом selenium_driver и конфигурацией op-ов
selenium_etl_job = selenium_etl_graph.to_job(
    resource_defs={
        "selenium_driver": selenium_driver_resource
    },
    config={
        "ops": {
            "authenticate_op": {
                "config": {
                    "username": USERNAME,
                    "password": PASSWORD,
                    "target_url": TARGET_URL
                }
            },
            "set_filters_op": {
                "config": {
                    "start_date": "01-04-25",
                    "end_date": "01-04-25",
                    "start_date_treatment": "01-04-25"
                }
            },
            "download_file_op": {
                "config": {
                    "file_pattern": "journal_*.csv",
                    "destination_folder": os.getenv("DESTINATION_FOLDER", "/default/destination/path")
                }
            },
            "post_process_op": {
                "config": {
                    "destination_folder": os.getenv("DESTINATION_FOLDER", "/default/destination/path"),
                    "new_file_name": "downloaded_file.csv"
                }
            }
        },
        "resources": {
            "selenium_driver": {
                "config": {
                    "browser": DEFAULT_BROWSER,
                    "destination_folder": os.getenv("DESTINATION_FOLDER", "/default/destination/path")
                }
            }
        }
    }
)
