import dagster as dg

from mosaic_conductor.selenium.wo.jobs import wo_talon_job, selenium_wo_talon_schedule, wo_doctor_job, selenium_wo_doctor_schedule

all_sensors = []
all_assets = []
all_jobs = [wo_talon_job, wo_doctor_job]
all_schedules = [selenium_wo_talon_schedule, selenium_wo_doctor_schedule]

defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors
)
