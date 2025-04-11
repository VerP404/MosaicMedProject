from dagster import op, OpExecutionContext
from django.db import transaction
from django.db.models import Q
from apps.load_data.models import TalonRefusal


@op(
    config_schema={}
)
def update_error_log_is_fixed_op(context: OpExecutionContext, load_result: dict):
    """
    Дополнительный этап для обработки загрузки в load_data_error_log_talon.
    - Ожидается, что load_result содержит ключ 'error_set' – набор ошибок, присутствующих в последнем CSV.
    - Для каждой записи в базе с is_fixed=False, если:
        (1) её ошибка не содержится в 'error_set', ИЛИ
        (2) talon_status в списке ['4', '6', '8'],
      ставим is_fixed=True (то есть считаем, что ошибка/талон исправлен).
    """
    new_errors = set(load_result.get("error_set", []))
    if not new_errors:
        context.log.info("Набор ошибок из CSV не передан. Обновление не производится.")
        # Всё равно учитываем talon_status 4,6,8:
        # если нет error_set, то мы обновляем только те, у кого статус 4,6,8 и is_fixed=False
        with transaction.atomic():
            qs_no_errorset = TalonRefusal.objects.filter(is_fixed=False, talon_status__in=['4', '6', '8'])
            total_no_errorset = qs_no_errorset.count()
            for record in qs_no_errorset:
                record.is_fixed = True
                record.save()
            context.log.info(f"Без error_set. Статус 4,6,8 => исправлено: {total_no_errorset}")
            return {"fixed_count": total_no_errorset}

    fixed_count = 0
    with transaction.atomic():
        qs = TalonRefusal.objects.filter(is_fixed=False)
        total_to_check = qs.count()

        for record in qs:
            # Условие 1: ошибка отсутствует в последнем CSV
            condition_missing = record.error not in new_errors
            # Условие 2: talon_status в [4,6,8]
            condition_talon_status = record.talon_status in ['4', '6', '8']

            if condition_missing or condition_talon_status:
                record.is_fixed = True
                record.save()
                fixed_count += 1

    context.log.info(
        f"Из {total_to_check} записей с is_fixed=False обновлено: {fixed_count} (помечено как is_fixed=True)\n"
        f"Причины обновления: отсутствие error в последнем CSV или talon_status ∈ {{4,6,8}}."
    )
    return {"fixed_count": fixed_count}
