import os
from dagster import graph, in_process_executor, schedule

from mosaic_conductor.selenium.config import ISZL_BASE_URL, ISZL_BROWSER
from mosaic_conductor.selenium.iszl.ops.iszl_start import open_site_iszl_op
from mosaic_conductor.selenium.iszl.ops.iszl_filter import iszl_filter_input_dispanser_op, iszl_filter_input_download_op
from mosaic_conductor.selenium.iszl.ops.iszl_download import move_iszl_downloaded_file_op
from mosaic_conductor.selenium.selenium_driver import selenium_driver_resource


def create_download_job(
        job_name: str,
        target_url: str,
        browser: str,
        temp_download_folder: str,
        destination_folders: list,
        file_pattern: str,
        filter_iszl_input_op_fn,
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
    :param filter_iszl_input_op_fn: оп-функция, отвечающая за установку фильтров на нужной странице.
    :param extra_filter_config: дополнительные настройки для фильтра (если требуются).
    """

    @graph(name=f"{job_name}_graph")
    def download_graph():
        site_url = open_site_iszl_op()
        filter_result = filter_iszl_input_op_fn(site_url)
        move_iszl_downloaded_file_op(filter_result)

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
            filter_iszl_input_op_fn.__name__: {"config": extra_filter_config or {}},
            "move_iszl_downloaded_file_op": {
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


# Задача для скачивания отчета по диспансерному наблюдению
iszl_download_dispanser_job = create_download_job(
    job_name="iszl_download_dispanser_job",
    target_url=ISZL_BASE_URL,
    browser=ISZL_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "iszl", "dispanser"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "iszl", "dispanser")
    ],
    file_pattern="dispanser_*.csv",
    filter_iszl_input_op_fn=iszl_filter_input_dispanser_op,
    extra_filter_config={},
)

# Задача для скачивания других отчетов в формате CSV
iszl_download_csv_job = create_download_job(
    job_name="iszl_download_csv_job",
    target_url=ISZL_BASE_URL,
    browser=ISZL_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "iszl", "reports"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "iszl", "reports")
    ],
    file_pattern="report_*.csv",
    filter_iszl_input_op_fn=iszl_filter_input_download_op,
    extra_filter_config={},
)


# Расписания для запуска задач
@schedule(
    cron_schedule="0 8 * * *",  # Запуск каждый день в 8 утра
    job=iszl_download_dispanser_job,
    execution_timezone="Europe/Moscow"
)
def selenium_iszl_dispanser_schedule(_context):
    return {}


@schedule(
    cron_schedule="30 8 * * *",  # Запуск каждый день в 8:30 утра
    job=iszl_download_csv_job,
    execution_timezone="Europe/Moscow"
)
def selenium_iszl_csv_schedule(_context):
    return {}


# Списки для экспорта
iszl_selenium_jobs = [
    iszl_download_dispanser_job,
    iszl_download_csv_job
]

iszl_selenium_schedules = [
    selenium_iszl_dispanser_schedule,
    selenium_iszl_csv_schedule
]
