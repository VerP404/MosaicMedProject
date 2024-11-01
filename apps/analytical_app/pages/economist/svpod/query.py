import pandas as pd

from apps.analytical_app.pages.SQL_query.query import base_query
from apps.analytical_app.query_executor import engine


def sql_qery_sv_pod(sql_cond):
    return f"""
SELECT CASE
           WHEN goal = '541' and amount in ('589.82') THEN '541 УЗИ 589.82'
           WHEN goal = '541' and amount in ('1179.64') THEN '541 УЗИ 1179.64'
           WHEN goal = '541' and amount in ('1769.46') THEN '541 УЗИ 1769.46'
           WHEN goal = '541' and amount in ('2359.28') THEN '541 УЗИ 2359.28'
           WHEN goal = '541' and amount = '895.02' THEN '541 Эндоскопия'
           WHEN goal = '541' and amount = '2077.79' THEN '541 Колоноскопия'
           WHEN goal = '541' and amount = '2972.81' THEN '541 гастроскопия и Колоноскопия'
           WHEN goal = '541' and amount = '399.6' THEN '541 ошибка'
           WHEN goal = '541' and amount = '1059.57' THEN '541 эзофагоскопия'
           END                                                AS "Цель",
       COUNT(*)                                               AS "К-во",
       ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM data_loader_omsdata
WHERE report_period IN ({sql_cond})
  AND status IN :status_list
  and tariff != '0'
  and smo_code like '360%'
  AND sanctions = '-'
  AND goal = '541'
group by goal, amount
union all

SELECT goal,
       count(*)                                               as "К-во",
       ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM data_loader_omsdata
WHERE report_period IN ({sql_cond})
  AND status IN :status_list
  and tariff != '0'
  and smo_code like '360%'
  AND sanctions = '-'
  AND goal IN ('64', '13', '32', 'ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1', 'ДС2', '307', '561')
GROUP BY goal
union all

SELECT CASE
           WHEN goal = 'ДР1' AND gender = 'Ж' THEN 'ДР1 Ж'
           WHEN goal = 'ДР1' AND gender = 'М' THEN 'ДР1 М'
           WHEN goal = 'ДР2' AND gender = 'Ж' THEN 'ДР2 Ж'
           WHEN goal = 'ДР2' AND gender = 'М' THEN 'ДР2 М'
           ELSE 'ДР'
           END                                                 as Цель_,
       count(*)                                                as "К-во",
       ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM data_loader_omsdata
WHERE report_period IN ({sql_cond})
  AND status IN :status_list
  and tariff != '0'
  and smo_code like '360%'
  AND sanctions = '-'
  AND goal in ('ДР1', 'ДР2')
GROUP BY Цель_

union all

SELECT concat(goal, ' ', tariff)                            as Цель_,
       count(*)                                                as "К-во",
       ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM data_loader_omsdata
WHERE report_period IN ({sql_cond})
  AND status IN :status_list
  and tariff != '0'
  and smo_code like '360%'
  AND sanctions = '-'
  AND goal = '307'
GROUP BY Цель_

union all

SELECT CASE
           WHEN goal = '22' AND home_visits = '0' THEN '22 в МО'
           WHEN goal = '22' AND home_visits = '1' THEN '22 на дому'
           ELSE goal || ' ' || home_visits
           END                                                 as Цель_,
       count(*)                                                as "К-во",
       ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM data_loader_omsdata
WHERE report_period IN ({sql_cond})
  AND status IN :status_list
  and tariff != '0'
  and smo_code like '360%'
  AND sanctions = '-'
  AND goal = '22'
GROUP BY Цель_

union all

SELECT CASE
           WHEN goal = '3' and mp_profile = '136' THEN '3 акушерство и гинекология'
           WHEN goal = '3' and mp_profile = '28' THEN '3 инфекционные болезни'
           WHEN goal = '3' and mp_profile = '29' and main_diagnosis not like 'I%'
               THEN '3 кардиологии другие'
           WHEN goal = '3' and mp_profile = '29' and main_diagnosis like 'I%' THEN '3 кардиологии БСК'
           WHEN goal = '3' and mp_profile = '53' THEN '3 неврологии'
           WHEN goal = '3' and (mp_profile = '57' or mp_profile = '97') and main_diagnosis like 'E11%'
               THEN '3 Терапия сахарный диабет'
           WHEN goal = '3' and (mp_profile = '57' or mp_profile = '97') and main_diagnosis like 'I%'
               THEN '3 Терапия БСК'
           WHEN goal = '3' and (mp_profile = '57' or mp_profile = '97') and
                main_diagnosis not like any (array ['I%', 'E11%']) THEN '3 Терапия другие'
           WHEN goal = '3' and mp_profile = '60' and main_diagnosis like 'C%' and
                main_diagnosis not like 'C44%' THEN '3 онкологии C44'
           WHEN goal = '3' and mp_profile = '60' and main_diagnosis like 'C44%' THEN '3 онкологии C01-C96'
           WHEN goal = '3' and mp_profile = '60' and main_diagnosis not like 'C%' THEN '3 онкологии'
           WHEN goal = '3' and mp_profile = '162' THEN '3 оториноларингологии'
           WHEN goal = '3' and mp_profile = '65' THEN '3 офтальмологии'
           WHEN goal = '3' and mp_profile = '100' THEN '3 травматологии и ортопедии'
           WHEN goal = '3' and mp_profile = '108' THEN '3 урологии'
           WHEN goal = '3' and mp_profile = '112' THEN '3 хирургии'
           WHEN goal = '3' and mp_profile = '122' THEN '3 эндокринологии'
           ELSE goal
           END                                                 AS "Цель",
       COUNT(*)                                                AS "К-во",
       ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"
FROM data_loader_omsdata
WHERE report_period IN ({sql_cond})
  AND status IN :status_list
  and sanctions = '-'
  AND goal = '3'
  AND tariff != '0'
  and smo_code like '360%'
GROUP BY CASE
             WHEN goal = '3' and mp_profile = '136' THEN '3 акушерство и гинекология'
             WHEN goal = '3' and mp_profile = '28' THEN '3 инфекционные болезни'
             WHEN goal = '3' and mp_profile = '29' and main_diagnosis not like 'I%'
                 THEN '3 кардиологии другие'
             WHEN goal = '3' and mp_profile = '29' and main_diagnosis like 'I%' THEN '3 кардиологии БСК'
             WHEN goal = '3' and mp_profile = '53' THEN '3 неврологии'
             WHEN goal = '3' and (mp_profile = '57' or mp_profile = '97') and main_diagnosis like 'E11%'
                 THEN '3 Терапия сахарный диабет'
             WHEN goal = '3' and (mp_profile = '57' or mp_profile = '97') and main_diagnosis like 'I%'
                 THEN '3 Терапия БСК'
             WHEN goal = '3' and (mp_profile = '57' or mp_profile = '97') and
                  main_diagnosis not like any (array ['I%', 'E11%']) THEN '3 Терапия другие'
             WHEN goal = '3' and mp_profile = '60' and main_diagnosis like 'C%' and
                  main_diagnosis not like 'C44%' THEN '3 онкологии C44'
             WHEN goal = '3' and mp_profile = '60' and main_diagnosis like 'C44%'
                 THEN '3 онкологии C01-C96'
             WHEN goal = '3' and mp_profile = '60' and main_diagnosis not like 'C%' THEN '3 онкологии'
             WHEN goal = '3' and mp_profile = '162' THEN '3 оториноларингологии'
             WHEN goal = '3' and mp_profile = '65' THEN '3 офтальмологии'
             WHEN goal = '3' and mp_profile = '100' THEN '3 травматологии и ортопедии'
             WHEN goal = '3' and mp_profile = '108' THEN '3 урологии'
             WHEN goal = '3' and mp_profile = '112' THEN '3 хирургии'
             WHEN goal = '3' and mp_profile = '122' THEN '3 эндокринологии'
             ELSE goal
             end
union all
select distinct ksg,
                COUNT(*)                                                AS "К-во",
                ROUND(SUM(CAST(tariff AS numeric(10, 2)))::numeric, 2) as "Сумма"

from data_loader_omsdata
where report_period IN ({sql_cond})
  AND status IN :status_list
  and ksg != '-'
  AND tariff != '0'
  and smo_code like '360%'
   and sanctions = '-'
group by ksg
"""


# Функция для генерации условий фильтрации на основе планов
def get_filter_conditions(group_ids, year):
    # Преобразуем group_ids в строку формата "1, 2, 3" для использования в SQL
    group_ids_str = ", ".join(map(str, group_ids))

    # Получаем условия фильтрации из таблицы на основе group_ids и year
    query = f"""
    SELECT field_name, filter_type, values
    FROM plan_filtercondition
    WHERE group_id IN ({group_ids_str}) AND year = {year}
    """
    conditions_df = pd.read_sql(query, engine)

    # Генерируем условия для SQL
    filter_clauses = []
    for _, row in conditions_df.iterrows():
        field_name = row['field_name']
        filter_type = row['filter_type']
        values = row['values']

        if filter_type == 'in':
            filter_clauses.append(f"{field_name} IN ({values})")
        elif filter_type == 'exact':
            filter_clauses.append(f"{field_name} = {values}")

    # Объединяем условия через AND
    return " AND ".join(filter_clauses)


def sql_query_rep(selected_year, group_id, months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12', inogorod=None,
                  sanction=None, amount_null=None,
                  building=None, department=None, profile=None, doctor=None, input_start=None, input_end=None,
                  treatment_start=None, treatment_end=None, filter_conditions=None, mode='finance'):
    # Основной базовый запрос
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor, input_start, input_end, treatment_start, treatment_end)

    # Начало основного запроса
    if mode == 'finance':
        query = f"""
        {base}
            SELECT
                report_month_number AS month,
                SUM(CASE WHEN status = '1' THEN amount_numeric END) AS новые,
                SUM(CASE WHEN status = '2' THEN amount_numeric END) AS в_тфомс,
                SUM(CASE WHEN status = '3' THEN amount_numeric END) AS оплачено,
                SUM(CASE WHEN status IN ('5', '7', '12') THEN amount_numeric END) AS отказано,
                SUM(CASE WHEN status IN ('6', '8', '4') THEN amount_numeric END) AS исправлено,
                SUM(CASE WHEN status IN ('0', '13', '17') THEN amount_numeric END) AS отменено
            FROM oms
            """
    else:
        query = f"""
        {base}
            SELECT
                report_month_number AS month,
                COUNT(CASE WHEN status = '1' THEN 1 END) AS новые,
                COUNT(CASE WHEN status = '2' THEN 1 END) AS в_тфомс,
                COUNT(CASE WHEN status = '3' THEN 1 END) AS оплачено,
                COUNT(CASE WHEN status IN ('5', '7', '12') THEN 1 END) AS отказано,
                COUNT(CASE WHEN status IN ('6', '8', '4') THEN 1 END) AS исправлено,
                COUNT(CASE WHEN status IN ('0', '13', '17') THEN 1 END) AS отменено
            FROM oms
        """

    # Условия WHERE
    where_conditions = []
    if filter_conditions:
        where_conditions.append(filter_conditions)

    # Добавляем условия WHERE в запрос, если они есть
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)

    # Завершаем запрос с группировкой и сортировкой
    query += """
    GROUP BY month
    ORDER BY month
    """

    return query
