import dagster as dg

from mosaic_conductor.etl.kvazar import kvazar_assets, kvazar_jobs
from mosaic_conductor.etl.kvazar.sensor import kvazar_sensors
from mosaic_conductor.etl.common.connect_db import connect_to_db
from dagster import asset, AssetIn, Output, OpExecutionContext
import pandas as pd
import os
import subprocess

all_sensors = kvazar_sensors
all_assets = kvazar_assets
all_jobs = kvazar_jobs
defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=[],
    sensors=all_sensors
)


@asset(name="iszl_people_snapshot")
def iszl_people_snapshot(context: OpExecutionContext) -> Output[str]:
    """Ищет последний CSV населения и возвращает путь к файлу."""
    base_dir = os.path.join(os.getcwd(), "mosaic_conductor", "etl", "data", "iszl", "people")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    # Берём последний файл по времени изменения
    candidates = [
        os.path.join(base_dir, f)
        for f in os.listdir(base_dir)
        if f.lower().endswith(".csv")
    ]
    if not candidates:
        raise FileNotFoundError(f"В каталоге {base_dir} нет CSV файлов населения")
    latest = max(candidates, key=os.path.getmtime)
    context.log.info(f"Найден CSV: {latest}")
    return Output(latest)


@asset(name="iszl_people_sync", ins={"csv_path": AssetIn("iszl_people_snapshot")})
def iszl_people_sync(context: OpExecutionContext, csv_path: str) -> Output[str]:
    """Запускает Django management-команду sync_iszl_people для снапшот-синхронизации."""
    manage_py = os.path.join(os.getcwd(), "manage.py")
    if not os.path.exists(manage_py):
        raise FileNotFoundError("manage.py не найден — запуск команды невозможен")
    cmd = [
        "python",
        manage_py,
        "sync_iszl_people",
        f"--file={csv_path}",
        "--encoding=utf-8-sig",
        "--delimiter=;",
        "--chunk=2000",
    ]
    context.log.info(f"Выполняю: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        context.log.error(res.stdout)
        context.log.error(res.stderr)
        raise RuntimeError("sync_iszl_people завершилась с ошибкой")
    context.log.info(res.stdout)
    return Output("ok")

