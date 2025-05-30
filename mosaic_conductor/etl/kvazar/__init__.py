from typing import Optional, Callable

from dagster import job, graph, in_process_executor

from config.settings import ORGANIZATIONS
from .db_check import kvazar_db_check
from .extract import kvazar_extract
from .load import kvazar_load
from .transform import kvazar_transform
from .update import update_personnel_op
from .update_emd_talon import update_emd_talon_id_op
from .update_error import update_error_log_is_fixed_op
from .update_oms_data import update_oms_data_op

kvazar_assets = [
    kvazar_db_check,
    kvazar_extract,
    kvazar_transform,
    kvazar_load
]


def create_etl_job(
        job_name: str,
        table_name: str,
        data_folder: str,
        mapping_file: str,
        op_fn: Optional[Callable] = None,
        op_config: Optional[dict] = None,
):
    @graph(name=f"{job_name}_graph")
    def etl_graph():
        db_result = kvazar_db_check()
        extract_result = kvazar_extract(db_result)
        transform_result = kvazar_transform(extract_result)
        load_result = kvazar_load(transform_result)
        if op_fn is not None:
            update_result = op_fn(load_result)
            return update_result
        return load_result

    job_ops = {
        "kvazar_db_check": {
            "config": {
                "organization": ORGANIZATIONS,
                "tables": [table_name],
            }
        },
        "kvazar_extract": {
            "config": {
                "mapping_file": f"mosaic_conductor/etl/config/{mapping_file}",
                "data_folder": f"mosaic_conductor/etl/data/{data_folder}",
                "table_name": table_name,
            }
        },
        "kvazar_transform": {
            "config": {
                "mapping_file": f"mosaic_conductor/etl/config/{mapping_file}",
                "table_name": table_name,
            }
        },
        "kvazar_load": {
            "config": {
                "table_name": table_name,
                "data_folder": f"mosaic_conductor/etl/data/{data_folder}",
                "mapping_file": f"mosaic_conductor/etl/config/{mapping_file}",
            }
        },
    }
    # Если дополнительная операция передана, добавляем её конфигурацию
    if op_fn is not None and op_config is not None:
        op_name = getattr(op_fn, "__name__", "op_fn")
        job_ops[op_name] = {"config": op_config or {}}

    job_config = {"ops": job_ops}

    return etl_graph.to_job(
        name=job_name,
        config=job_config,
        executor_def=in_process_executor,
    )


# Пример создания джоба wo_job_doctors с дополнительным этапом обновления данных
from .update import update_personnel_op

wo_job_doctors = create_etl_job(
    "wo_job_doctors",
    "load_data_doctor",
    "weboms/doctor/new",
    "oms_mapping.json",
    op_fn=update_personnel_op,  # Дополнительный оп для обновления Person и DoctorRecord
    op_config={}  # Если конфигурация для update_personnel_op не требуется, можно передать пустой словарь
)

# Остальные джобы создаются как ранее:
kvazar_job_eln = create_etl_job(
    "kvazar_job_eln",
    "load_data_sick_leave_sheets",
    "kvazar/eln",
    "mapping.json",
)
kvazar_job_emd = create_etl_job(
    "kvazar_job_emd",
    "load_data_emd",
    "kvazar/emd",
    "mapping.json",
    op_fn=update_emd_talon_id_op,
    op_config={}
)
kvazar_job_recipes = create_etl_job(
    "kvazar_job_recipes",
    "load_data_recipes",
    "kvazar/recipe",
    "mapping.json",
)
kvazar_job_death = create_etl_job(
    "kvazar_job_death",
    "load_data_death",
    "kvazar/death",
    "mapping.json",
)
kvazar_job_reference = create_etl_job(
    "kvazar_job_reference",
    "load_data_reference",
    "kvazar/reference",
    "mapping.json",
)
iszl_job_dn = create_etl_job(
    "iszl_job_dn",
    "load_data_dispansery_iszl",
    "iszl/dn",
    "mapping.json",
)
iszl_job_dn_work = create_etl_job(
    "iszl_job_dn_work",
    "load_data_dn_work_iszl",
    "iszl/dn_work",
    "mapping.json",
)
iszl_job_people = create_etl_job(
    "iszl_job_people",
    "load_data_iszl_population",
    "iszl/people",
    "mapping.json",
)
wo_old_job_talon = create_etl_job(
    "wo_old_job_talon",
    "data_loader_omsdata",
    "weboms/talon/old",
    "oms_old_mapping.json",
)
wo_old_job_doctors = create_etl_job(
    "wo_old_job_doctors",
    "data_loader_doctordata",
    "weboms/doctor/old",
    "oms_old_mapping.json",
)


def update_talon_and_oms(load_result):
    emd_result = update_emd_talon_id_op(load_result)
    oms_result = update_oms_data_op(emd_result)
    return oms_result


wo_job_talon = create_etl_job(
    "wo_job_talon",
    "load_data_talons",
    "weboms/talon/new",
    "oms_mapping.json",
    op_fn=update_talon_and_oms,
)

wo_job_detailed = create_etl_job(
    "wo_job_detailed",
    "load_data_detailed_medical_examination",
    "weboms/detailed",
    "oms_mapping.json",
    op_fn=update_talon_and_oms,
)
wo_job_errorlog = create_etl_job(
    "wo_job_errorlog",
    "load_data_error_log_talon",
    "weboms/errorlog",
    "oms_mapping.json",
    op_fn=update_error_log_is_fixed_op,
)

wo_job_journal_appeals = create_etl_job(
    "wo_job_journal_appeals",
    "load_data_journal_appeals",
    "kvazar/journal_appeals",
    "mapping.json",
)
kvazar_jobs = [
    kvazar_job_eln,
    kvazar_job_emd,
    kvazar_job_recipes,
    kvazar_job_death,
    kvazar_job_reference,
    iszl_job_dn,
    iszl_job_dn_work,
    iszl_job_people,
    wo_old_job_talon,
    wo_old_job_doctors,
    wo_job_doctors,
    wo_job_talon,
    wo_job_detailed,
    wo_job_errorlog,
    wo_job_journal_appeals
]
