from dagster import job

from config.settings import ORGANIZATIONS
from .db_check import kvazar_db_check
from .extract import kvazar_extract
from .load import kvazar_load
from .transform import kvazar_transform

kvazar_assets = [
    kvazar_db_check,
    kvazar_extract,
    kvazar_transform,
    kvazar_load
]


def create_job(job_name, table_name, data_folder):
    @job(
        name=job_name,
        config={
            "ops": {
                "kvazar_db_check": {
                    "config": {
                        "organization": ORGANIZATIONS,
                        "tables": [table_name]
                    }
                },
                "kvazar_extract": {
                    "config": {
                        "mapping_file": "mosaic_conductor/etl/config/mapping.json",
                        "data_folder": f"mosaic_conductor/etl/data/{data_folder}",
                        "table_name": table_name
                    }
                },
                "kvazar_transform": {
                    "config": {
                        "mapping_file": "mosaic_conductor/etl/config/mapping.json",
                        "table_name": table_name
                    }
                },
                "kvazar_load": {
                    "config": {
                        "table_name": table_name,
                        "data_folder": f"mosaic_conductor/etl/data/{data_folder}",
                        "mapping_file": "mosaic_conductor/etl/config/mapping.json"
                    }
                }
            }
        }
    )
    def _job():
        db_result = kvazar_db_check()
        extract_result = kvazar_extract(db_result)
        transform_result = kvazar_transform(extract_result)
        kvazar_load(transform_result)

    return _job


# Создание джобов с помощью конструктора
kvazar_job_eln = create_job("kvazar_job_eln", "load_data_sick_leave_sheets", "kvazar/eln")
kvazar_job_emd = create_job("kvazar_job_emd", "load_data_emd", "kvazar/emd")
kvazar_job_recipes = create_job("kvazar_job_recipes", "load_data_recipes", "kvazar/recipe")
kvazar_job_death = create_job("kvazar_job_death", "load_data_death", "kvazar/death")
kvazar_job_reference = create_job("kvazar_job_reference", "load_data_reference", "kvazar/reference")

iszl_job_dn = create_job("iszl_job_dn", "load_data_dispansery_iszl", "iszl/dn")
