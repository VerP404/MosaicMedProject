from apps.analytical_app.pages.SQL_query.query import base_query


def sql_query_fen_inv(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                      department=None,
                      profile=None,
                      doctor=None,
                      input_start=None, input_end=None,
                      treatment_start=None,
                      treatment_end=None,
                      status_list=None):
    # Если months_placeholder пустой, используем все месяцы
    if not months_placeholder or months_placeholder.strip() == '':
        months_placeholder = ', '.join(map(str, range(1, 13)))
    
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end,
                      status_list=status_list)
    query = f"""
    {base}
SELECT TO_CHAR(TO_DATE(initial_input_date, 'DD-MM-YYYY'), 'DD-MM-YYYY')                       AS input_date,
       COUNT(CASE WHEN goal = '1' THEN 1 END)                                                 AS "1",
       COUNT(CASE WHEN goal = '3' THEN 1 END)                                                 AS "3",
       COUNT(CASE WHEN goal in ('305', '307') THEN 1 END)                                     AS "305,307 D",
       COUNT(CASE WHEN goal in ('113', '114', '14') THEN 1 END)                                AS "113,114,14 Z",
       COUNT(CASE WHEN goal in ('64', '640') THEN 1 END)                                      AS "64 G",
       COUNT(CASE WHEN goal in ('541', '561') THEN 1 END)                                     AS "541,561 E",
       COUNT(CASE WHEN goal = '22' THEN 1 END)                                                AS "22 N",
       COUNT(CASE WHEN goal in ('30', '301') THEN 1 END)                                      AS "30,301 O",
       COUNT(CASE
                 WHEN goal NOT LIKE 'Д%'
                     AND goal NOT LIKE 'О%'
                     AND goal NOT LIKE 'У%'
                     AND goal NOT LIKE 'П%'
                     AND main_diagnosis_code LIKE 'C%'
                     THEN 1
           END)                                                                               AS "C",
       COUNT(CASE WHEN goal in ('5', '7', '9', '10', '32') THEN 1 END)                        AS "5,7,9,10,32 P",
       COUNT(CASE WHEN goal in ('В дневном стационаре', 'На дому', 'Стационарно') THEN 1 END) AS "SD",
       COUNT(case when goal = 'ДВ4' then 1 end)                                                 as "ДВ4 V",
       COUNT(case when goal = 'ДВ2' then 1 end)                                                 as "ДВ2 T",
       COUNT(case when goal = 'ОПВ' then 1 end)                                                 as "ОПВ P",
       COUNT(case when goal = 'УД1' then 1 end)                                                 as "УД1 U",
       COUNT(case when goal = 'УД2' then 1 end)                                                 as "УД2 Y",
       COUNT(case when goal = 'ДР1' then 1 end)                                                 as "ДР1 R",
       COUNT(case when goal = 'ДР2' then 1 end)                                                 as "ДР2 Q",
       COUNT(case when goal = 'ПН1' then 1 end)                                                 as "ПН1 N",
       COUNT(case when goal = 'ДС2' then 1 end)                                                 as "ДС2 S"
FROM oms
WHERE 1=1
GROUP BY TO_DATE(initial_input_date, 'DD-MM-YYYY')
HAVING (
    COUNT(CASE WHEN goal = '1' THEN 1 END) +
    COUNT(CASE WHEN goal = '3' THEN 1 END) +
    COUNT(CASE WHEN goal in ('305', '307') THEN 1 END) +
    COUNT(CASE WHEN goal in ('113', '114', '14') THEN 1 END) +
    COUNT(CASE WHEN goal in ('64', '640') THEN 1 END) +
    COUNT(CASE WHEN goal in ('541', '561') THEN 1 END) +
    COUNT(CASE WHEN goal = '22' THEN 1 END) +
    COUNT(CASE WHEN goal in ('30', '301') THEN 1 END) +
    COUNT(CASE
              WHEN goal NOT LIKE 'Д%'
                  AND goal NOT LIKE 'О%'
                  AND goal NOT LIKE 'У%'
                  AND goal NOT LIKE 'П%'
                  AND main_diagnosis_code LIKE 'C%'
                  THEN 1
        END) +
    COUNT(CASE WHEN goal in ('5', '7', '9', '10', '32') THEN 1 END) +
    COUNT(CASE WHEN goal in ('В дневном стационаре', 'На дому', 'Стационарно') THEN 1 END) +
    COUNT(case when goal = 'ДВ4' then 1 end) +
    COUNT(case when goal = 'ДВ2' then 1 end) +
    COUNT(case when goal = 'ОПВ' then 1 end) +
    COUNT(case when goal = 'УД1' then 1 end) +
    COUNT(case when goal = 'УД2' then 1 end) +
    COUNT(case when goal = 'ДР1' then 1 end) +
    COUNT(case when goal = 'ДР2' then 1 end) +
    COUNT(case when goal = 'ПН1' then 1 end) +
    COUNT(case when goal = 'ДС2' then 1 end)
) > 0
ORDER BY TO_DATE(initial_input_date, 'DD-MM-YYYY') DESC
    """
    return query


def sql_query_details(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
                      department=None,
                      profile=None,
                      doctor=None,
                      input_start=None, input_end=None,
                      treatment_start=None,
                      treatment_end=None,
                      status_list=None,
                      input_date=None,
                      column_id=None):
    """
    SQL-запрос для детализации талонов по дате формирования и колонке цели
    """
    # Если months_placeholder пустой, используем все месяцы
    if not months_placeholder or months_placeholder.strip() == '':
        months_placeholder = ', '.join(map(str, range(1, 13)))
    
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end,
                      status_list=status_list)
    
    # Определяем фильтр по goal на основе выбранной колонки
    goal_filter = ""
    if column_id:
        if column_id == "1":
            goal_filter = "AND goal = '1'"
        elif column_id == "3":
            goal_filter = "AND goal = '3'"
        elif column_id == "305,307 D":
            goal_filter = "AND goal IN ('305', '307')"
        elif column_id == "113,114,14 Z":
            goal_filter = "AND goal IN ('113', '114', '14')"
        elif column_id == "64 G":
            goal_filter = "AND goal IN ('64', '640')"
        elif column_id == "541,561 E":
            goal_filter = "AND goal IN ('541', '561')"
        elif column_id == "22 N":
            goal_filter = "AND goal = '22'"
        elif column_id == "30,301 O":
            goal_filter = "AND goal IN ('30', '301')"
        elif column_id == "C":
            goal_filter = """AND goal NOT LIKE 'Д%'
                AND goal NOT LIKE 'О%'
                AND goal NOT LIKE 'У%'
                AND goal NOT LIKE 'П%'
                AND main_diagnosis_code LIKE 'C%'"""
        elif column_id == "5,7,9,10,32 P":
            goal_filter = "AND goal IN ('5', '7', '9', '10', '32')"
        elif column_id == "SD":
            goal_filter = "AND goal IN ('В дневном стационаре', 'На дому', 'Стационарно')"
        elif column_id == "ДВ4 V":
            goal_filter = "AND goal = 'ДВ4'"
        elif column_id == "ДВ2 T":
            goal_filter = "AND goal = 'ДВ2'"
        elif column_id == "ОПВ P":
            goal_filter = "AND goal = 'ОПВ'"
        elif column_id == "УД1 U":
            goal_filter = "AND goal = 'УД1'"
        elif column_id == "УД2 Y":
            goal_filter = "AND goal = 'УД2'"
        elif column_id == "ДР1 R":
            goal_filter = "AND goal = 'ДР1'"
        elif column_id == "ДР2 Q":
            goal_filter = "AND goal = 'ДР2'"
        elif column_id == "ПН1 N":
            goal_filter = "AND goal = 'ПН1'"
        elif column_id == "ДС2 S":
            goal_filter = "AND goal = 'ДС2'"
    
    # Фильтр по дате формирования
    date_filter = ""
    if input_date:
        date_filter = f"AND TO_DATE(initial_input_date, 'DD-MM-YYYY') = TO_DATE('{input_date}', 'DD-MM-YYYY')"
    
    query = f"""
    {base}
    SELECT talon AS "Талон",
           goal AS "Цель",
           status AS "Статус",
           patient AS "Пациент",
           birth_date AS "Дата рождения",
           treatment_start AS "Дата начала",
           treatment_end AS "Дата окончания",
           initial_input_date AS "Дата формирования",
           last_change_date AS "Дата изменения",
           smo_code AS "Код СМО",
           COALESCE(amount_numeric, 0) AS "Сумма",
           enp AS "ЕНП",
           doctor AS "Врач",
           specialty AS "Специальность",
           building AS "Корпус",
           department AS "Отделение"
    FROM oms
    WHERE 1=1
        {date_filter}
        {goal_filter}
    ORDER BY talon
    """
    return query