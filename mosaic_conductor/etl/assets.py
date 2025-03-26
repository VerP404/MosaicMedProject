import dagster as dg

from mosaic_conductor.etl.kvazar import kvazar_assets, kvazar_jobs
from mosaic_conductor.etl.kvazar.sensor import kvazar_sensors

all_sensors = kvazar_sensors
all_assets = kvazar_assets
all_jobs = kvazar_jobs
defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=[],
    sensors=all_sensors
)
