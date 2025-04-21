# apps/kvazar/update.py
from dagster import op
from sqlalchemy import text

from mosaic_conductor.etl.common.connect_db import connect_to_db


@op
def update_emd_talon_id_op(context, load_result):
    # load_result сюда передаётся, но вам он не нужен — просто триггер
    engine, _ = connect_to_db(context=context)

    sql = """
        UPDATE load_data_emd e
        SET talon_id = t.id
        FROM load_data_talons t
        WHERE e.original_epmz_id = t.source_id
        AND e.original_epmz_id <> '-'
        AND e.talon_id IS NULL;
    """

    with engine.begin() as conn:
        before = conn.execute(text(
            "SELECT COUNT(*) FROM load_data_emd WHERE talon_id IS NOT NULL"
        )).scalar_one()
        context.log.info(f"🔍 До обновления: записей с talon_id = {before}")

        result = conn.execute(text(sql))
        context.log.info(f"✅ количество записей из запроса: {result.rowcount}")

        after = conn.execute(text(
            "SELECT COUNT(*) FROM load_data_emd WHERE talon_id IS NOT NULL"
        )).scalar_one()
        context.log.info(f"🔍 После обновления: записей с talon_id = {after}")

    # возвращаем load_result, если он нужен дальше (или ничего не возвращайте)
    return load_result
