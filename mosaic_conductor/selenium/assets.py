import dagster as dg

from mosaic_conductor.selenium.wo import selenium_etl_job

all_sensors = []
all_assets = []
all_jobs = [selenium_etl_job]
all_schedules = []
defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors
)
