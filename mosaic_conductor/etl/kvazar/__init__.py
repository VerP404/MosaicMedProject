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



def create_job(job_name, table_name, data_folder, mapping_file="mapping.json"):
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
                        "mapping_file": f"mosaic_conductor/etl/config/{mapping_file}",
                        "data_folder": f"mosaic_conductor/etl/data/{data_folder}",
                        "table_name": table_name
                    }
                },
                "kvazar_transform": {
                    "config": {
                        "mapping_file": f"mosaic_conductor/etl/config/{mapping_file}",
                        "table_name": table_name,
                        "is_talon": True
                    }
                },
                "kvazar_load": {
                    "config": {
                        "table_name": table_name,
                        "data_folder": f"mosaic_conductor/etl/data/{data_folder}",
                        "mapping_file": f"mosaic_conductor/etl/config/{mapping_file}",
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
kvazar_job_eln = create_job("kvazar_job_eln",
                            "load_data_sick_leave_sheets",
                            "kvazar/eln")
kvazar_job_emd = create_job("kvazar_job_emd",
                            "load_data_emd",
                            "kvazar/emd")
kvazar_job_recipes = create_job("kvazar_job_recipes",
                                "load_data_recipes",
                                "kvazar/recipe")
kvazar_job_death = create_job("kvazar_job_death",
                              "load_data_death",
                              "kvazar/death")
kvazar_job_reference = create_job("kvazar_job_reference",
                                  "load_data_reference",
                                  "kvazar/reference")

iszl_job_dn = create_job("iszl_job_dn",
                         "load_data_dispansery_iszl",
                         "iszl/dn")

iszl_job_people = create_job("iszl_job_people",
                             "load_data_iszl_population",
                             "iszl/people")

wo_old_job_talon = create_job("wo_old_job_talon",
                              "data_loader_omsdata",
                              "weboms/talon/old",
                              "oms_old_mapping.json")

wo_old_job_doctors = create_job("wo_old_job_doctors",
                                "data_loader_doctordata",
                                "weboms/doctor",
                                "oms_old_mapping.json")

wo_job_talon = create_job("wo_job_talon",
                          "load_data_talons",
                          "weboms/talon/new",
                          "oms_mapping.json")


kvazar_jobs = [
    kvazar_job_eln,
    kvazar_job_emd,
    kvazar_job_recipes,
    kvazar_job_death,
    kvazar_job_reference,
    iszl_job_dn,
    wo_old_job_talon,
    wo_old_job_doctors,
    wo_job_talon
]