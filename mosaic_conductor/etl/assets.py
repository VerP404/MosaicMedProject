import datetime
import dagster as dg
from dagster import op, job, sensor, RunRequest

@op
def print_time_op(context):
    now = datetime.datetime.now()
    context.log.info(f"Текущее время: {now}")
    return now

@job
def time_job():
    print_time_op()

@sensor(job=time_job, minimum_interval_seconds=10)
def time_sensor(context):
    now = datetime.datetime.now()
    context.log.info(f"Сенсор сработал в {now}")
    # Используем текущее время в качестве run_key, чтобы сенсор запускался каждый раз
    yield RunRequest(run_key=str(now), run_config={})

# Определения для Dagster, чтобы включить job и sensor в репозиторий.
defs = dg.Definitions(
    jobs=[time_job],
    sensors=[time_sensor],
)
