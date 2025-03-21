import dagster as dg

from mosaic_conductor.etl.kvazar import kvazar_assets, kvazar_job_eln, kvazar_job_emd, kvazar_job_recipes, \
    kvazar_job_death, kvazar_job_reference, iszl_job_dn, wo_old_job_talon, wo_old_job_doctors
from mosaic_conductor.etl.kvazar.sensor import kvazar_sensor_eln, kvazar_sensor_emd, kvazar_sensor_recipes, \
    kvazar_sensor_death, kvazar_sensor_reference, iszl_sensor_dn

all_assets = kvazar_assets
all_sensors = [
    kvazar_sensor_eln,
    kvazar_sensor_emd,
    kvazar_sensor_recipes,
    kvazar_sensor_death,
    kvazar_sensor_reference,
    iszl_sensor_dn
]
all_jobs = [
    kvazar_job_eln,
    kvazar_job_emd,
    kvazar_job_recipes,
    kvazar_job_death,
    kvazar_job_reference,
    iszl_job_dn,
    wo_old_job_talon,
    wo_old_job_doctors
]
defs = dg.Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=[],
    sensors=all_sensors
)
