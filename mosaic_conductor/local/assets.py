import dagster as dg

all_jobs = []
all_schedules = []

defs = dg.Definitions(
    jobs=all_jobs,
    schedules=all_schedules,
)
