import dagster as dg

from mosaic_conductor.update.journal.update_status import update_status_job, daily_status_update_schedule
from mosaic_conductor.update.servers.update import update_servers_job, servers_update_schedule

all_jobs = [update_status_job, update_servers_job]
all_schedules = [daily_status_update_schedule, servers_update_schedule]

defs = dg.Definitions(
    jobs=all_jobs,
    schedules=all_schedules,
)
