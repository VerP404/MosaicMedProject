import dagster as dg

from mosaic_conductor.selenium.iszl.jobs import iszl_selenium_jobs, iszl_selenium_schedules
from mosaic_conductor.selenium.wo.jobs import wo_selenium_jobs, wo_selenium_schedules

all_sensors = []
all_assets = []
all_jobs = wo_selenium_jobs + iszl_selenium_jobs

all_schedules = wo_selenium_schedules + iszl_selenium_schedules

defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors
)
