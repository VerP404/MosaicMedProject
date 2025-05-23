import os
from dagster import graph, in_process_executor, schedule, RetryPolicy, GraphDefinition

from mosaic_conductor.selenium.config import OMS_BROWSER, OMS_BASE_URL
from mosaic_conductor.selenium.wo.ops.wo_start import open_site_wo_op
from mosaic_conductor.selenium.wo.ops.wo_filter import filter_input_op, filter_input_doctor_op, filter_input_detail_op, \
    filter_input_error_op
from mosaic_conductor.selenium.wo.ops.wo_download import move_wo_downloaded_file_op
from mosaic_conductor.selenium.selenium_driver import selenium_driver_resource


def create_download_job(
        job_name: str,
        target_url: str,
        browser: str,
        temp_download_folder: str,
        destination_folders: list,
        file_pattern: str,
        filter_wo_input_op_fn,  # функция-оп для фильтрации, например filter_input_op или другая
        extra_filter_config: dict = None,
        retry_attempts: int = 3,
        retry_delay: int = 300,
):
    """
    Создает Dagster job для скачивания файлов из веб-приложения.

    :param job_name: имя job.
    :param target_url: URL для открытия (логин, главная страница и т.д.).
    :param browser: тип браузера ("chrome" или "firefox").
    :param temp_download_folder: временная папка для загрузок.
    :param destination_folders: список конечных папок для копирования файла.
    :param file_pattern: шаблон для поиска загруженного файла (например, "journal_20*.csv").
    :param filter_wo_input_op_fn: оп-функция, отвечающая за установку фильтров на нужной странице.
    :param extra_filter_config: дополнительные настройки для фильтра (если требуются).
    :param retry_attempts: количество повторных попыток выполнения job при ошибке.
    :param retry_delay: задержка в секундах между повторными попытками.
    """

    @graph(name=f"{job_name}_graph")
    def download_graph():
        site_url = open_site_wo_op()
        filter_result = filter_wo_input_op_fn(site_url)
        move_wo_downloaded_file_op(filter_result)

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
            filter_wo_input_op_fn.__name__: {"config": extra_filter_config or {}},
            "move_wo_downloaded_file_op": {
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
        tags={"dagster/max_retries": str(retry_attempts), "dagster/retry_delay": str(retry_delay)}
    )


wo_download_talon_job = create_download_job(
    job_name="wo_download_talon_job",
    target_url=OMS_BASE_URL,
    browser=OMS_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "talon"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "old"),
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "talon", "new")
    ],
    file_pattern="journal_202*.csv",
    filter_wo_input_op_fn=filter_input_op,
    extra_filter_config={},
    retry_attempts=3,
    retry_delay=300,
)
wo_download_doctor_job = create_download_job(
    job_name="wo_download_doctor_job",
    target_url=OMS_BASE_URL,
    browser=OMS_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "doctor"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "doctor", "old"),
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "doctor", "new")
    ],
    file_pattern="journal_Doctors*.csv",
    filter_wo_input_op_fn=filter_input_doctor_op,
    extra_filter_config={},
    retry_attempts=3,
    retry_delay=300,
)

wo_download_detail_job = create_download_job(
    job_name="wo_download_detail_job",
    target_url=OMS_BASE_URL,
    browser=OMS_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "detailed"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "detailed"),
    ],
    file_pattern="journal_Detailed_Medical_Examination*.csv",
    filter_wo_input_op_fn=filter_input_detail_op,
    extra_filter_config={},
    retry_attempts=3,
    retry_delay=300,
)
wo_download_error_job = create_download_job(
    job_name="wo_download_error_job",
    target_url=OMS_BASE_URL,
    browser=OMS_BROWSER,
    temp_download_folder=os.path.join(os.getcwd(), "uploads", "errorlog"),
    destination_folders=[
        os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "weboms", "errorlog"),
    ],
    file_pattern="journal_ErrorLog_*.csv",
    filter_wo_input_op_fn=filter_input_error_op,
    extra_filter_config={},
    retry_attempts=3,
    retry_delay=300,
)


@schedule(
    cron_schedule="0 7-21 * * *",
    job=wo_download_talon_job,
    execution_timezone="Europe/Moscow"
)
def selenium_wo_talon_schedule(_context):
    return {}


@schedule(
    cron_schedule="10 8-17 * * *",
    job=wo_download_doctor_job,
    execution_timezone="Europe/Moscow"
)
def selenium_wo_doctor_schedule(_context):
    return {}


@schedule(
    cron_schedule="15 7,13 * * *",
    job=wo_download_detail_job,
    execution_timezone="Europe/Moscow"
)
def selenium_wo_detail_schedule(_context):
    return {}


@schedule(
    cron_schedule="20 7-16 * * *",
    job=wo_download_error_job,
    execution_timezone="Europe/Moscow"
)
def selenium_wo_error_schedule(_context):
    return {}


wo_selenium_jobs = [
    wo_download_talon_job,
    wo_download_doctor_job,
    wo_download_detail_job,
    wo_download_error_job
]

wo_selenium_schedules = [
    selenium_wo_talon_schedule,
    selenium_wo_doctor_schedule,
    selenium_wo_detail_schedule,
    selenium_wo_error_schedule
]
