import dagster as dg

from mosaic_conductor.selenium.wo.jobs import wo_download_talon_job, selenium_wo_talon_schedule, wo_download_doctor_job, \
    selenium_wo_doctor_schedule, wo_download_detail_job, selenium_wo_detail_schedule, wo_download_error_job, \
    selenium_wo_error_schedule

all_sensors = []
all_assets = []
all_jobs = [
    wo_download_talon_job,
    wo_download_doctor_job,
    wo_download_detail_job,
    wo_download_error_job
]
all_schedules = [
    selenium_wo_talon_schedule,
    selenium_wo_doctor_schedule,
    selenium_wo_detail_schedule,
    selenium_wo_error_schedule
]

defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors
)
