"""
Dagster op: после загрузки bronze iszl_job_dn синхронизирует dn_app.
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys

from dagster import Failure, Field, Int, op


@op(
    config_schema={
        "year": Field(
            Int,
            is_required=False,
            default_value=0,
            description="0 = автоопределение PlanYear из load_data_dispansery_iszl",
        ),
    }
)
def sync_dn_from_iszl_op(context, load_result):
    """
    Вызывает management command sync_dn_from_iszl после успешной загрузки
    load_data_dispansery_iszl.
    """
    year = int(context.op_config.get("year") or 0)

    manage_py = os.path.join(os.getcwd(), "manage.py")
    python_spec = os.environ.get("DJANGO_PYTHON_BIN")
    python_cmd = shlex.split(python_spec) if python_spec else [sys.executable]

    if not os.path.exists(manage_py):
        raise Failure("manage.py не найден — sync_dn_from_iszl невозможен")

    cmd = [*python_cmd, manage_py, "sync_dn_from_iszl", f"--year={year}"]
    context.log.info(f"Запуск: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.stdout:
        context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise Failure(
            f"sync_dn_from_iszl завершился с кодом {result.returncode}. {detail[:800]}"
        )

    return f"dn_app sync year_arg={year}; prior={load_result}"
