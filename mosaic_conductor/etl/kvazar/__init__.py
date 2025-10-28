import os
import shlex
import subprocess
import sys
import time
from typing import Optional, Callable

from dagster import job, graph, in_process_executor, op, Failure

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
    "data_loader_iszlpeople",
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


@op(config_schema={"csv_path": str})
def load_journal_appeals_op(context):
    csv_path = context.op_config["csv_path"]
    csv_path = os.path.abspath(csv_path)
    manage_py = os.path.join(os.getcwd(), "manage.py")
    python_spec = os.environ.get("DJANGO_PYTHON_BIN")
    python_cmd = shlex.split(python_spec) if python_spec else [sys.executable]

    if not os.path.exists(csv_path):
        raise Failure(f"CSV файл не найден: {csv_path}")
    if not os.path.exists(manage_py):
        raise Failure("manage.py не найден — запуск load_journal_appeals невозможен")

    cmd = [
        *python_cmd,
        manage_py,
        "load_journal_appeals",
        f"--file={csv_path}",
        "--encoding=utf-8-sig",
        "--delimiter=;",
    ]

    context.log.info(f"Запуск команды: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        context.log.error(result.stdout)
        context.log.error(result.stderr)
        # Перемещаем файл в папку errors с сохранением ошибки
        error_dir = os.path.join(os.path.dirname(csv_path), "errors")
        os.makedirs(error_dir, exist_ok=True)
        
        file_name = os.path.basename(csv_path)
        name, ext = os.path.splitext(file_name)
        timestamp = int(time.time())
        error_file = os.path.join(error_dir, f"{name}_{timestamp}_error{ext}")
        error_txt = os.path.join(error_dir, f"{name}_{timestamp}_error.txt")
        
        try:
            # Перемещаем CSV файл
            os.rename(csv_path, error_file)
            context.log.info(f"Файл {file_name} перемещён в {error_file}")
            
            # Создаём файл с ошибкой
            with open(error_txt, "w", encoding="utf-8") as f:
                f.write(f"Ошибка загрузки файла: {file_name}\n")
                f.write(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Код возврата: {result.returncode}\n\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n\nSTDERR:\n")
                f.write(result.stderr)
            
            context.log.info(f"Создан файл с ошибкой: {error_txt}")
            
        except OSError as exc:
            context.log.error(f"Не удалось переместить файл в папку ошибок: {exc}")
        
        raise Failure(
            description="Команда load_journal_appeals завершилась с ошибкой",
            metadata={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "error_file": error_file,
                "error_txt": error_txt,
            }
        )

    context.log.info(result.stdout)

    try:
        os.remove(csv_path)
        context.log.info(f"Файл {csv_path} удалён после успешной загрузки")
    except FileNotFoundError:
        context.log.warning(f"Файл {csv_path} отсутствует при удалении — возможно, удалён вне процесса")
    except OSError as exc:
        context.log.error(f"Не удалось удалить файл {csv_path}: {exc}")
        raise Failure(f"Не удалось удалить файл {csv_path}: {exc}")

    return "ok"


@job(name="kvazar_job_load_journal_appeals")
def kvazar_job_load_journal_appeals():
    load_journal_appeals_op()
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
    wo_job_journal_appeals,
    kvazar_job_load_journal_appeals
]
