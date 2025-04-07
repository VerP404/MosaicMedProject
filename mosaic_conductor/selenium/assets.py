import dagster as dg

from mosaic_conductor.selenium.wo.jobs import wo_talon_job

all_sensors = []
all_assets = []
all_jobs = [wo_talon_job]
all_schedules = []

defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors
)
