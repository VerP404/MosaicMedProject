import dagster as dg

from mosaic_conductor.etl.kvazar import kvazar_assets, kvazar_job_eln, kvazar_job_emd, kvazar_job_recipes, \
    kvazar_job_death, kvazar_job_reference
from mosaic_conductor.etl.kvazar.sensor import kvazar_sensor_eln, kvazar_sensor_emd, kvazar_sensor_recipes, \
    kvazar_sensor_death, kvazar_sensor_reference

all_assets = kvazar_assets
all_sensors = [
    kvazar_sensor_eln,
    kvazar_sensor_emd,
    kvazar_sensor_recipes,
    kvazar_sensor_death,
    kvazar_sensor_reference
]
defs = dg.Definitions(
    assets=all_assets,
    jobs=[kvazar_job_eln, kvazar_job_emd, kvazar_job_recipes, kvazar_job_death, kvazar_job_reference],
    schedules=[],
    sensors=all_sensors
)