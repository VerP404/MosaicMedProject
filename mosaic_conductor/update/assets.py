import dagster as dg

from mosaic_conductor.update.journal.update_status import update_status_job, daily_status_update_schedule

defs = dg.Definitions(
    jobs=[update_status_job],
    schedules=[daily_status_update_schedule],
)
