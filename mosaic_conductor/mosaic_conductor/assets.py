import dagster as dg

from mosaic_conductor.mosaic_conductor.web.jobs import google_search_job

defs = dg.Definitions(
    assets=[],
    jobs=[google_search_job],
    schedules=[],
    sensors=[]
)
