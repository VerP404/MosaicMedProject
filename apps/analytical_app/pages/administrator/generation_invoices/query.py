from apps.analytical_app.pages.SQL_query.query import base_query


def sql_query_fen_inv(selected_year, months_placeholder, inogorod, sanction, amount_null, building: None,
                      department=None,
                      profile=None,
                      doctor=None,
                      input_start=None, input_end=None,
                      treatment_start=None,
                      treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
SELECT TO_CHAR(TO_DATE(initial_input_date, 'DD-MM-YYYY'), 'DD-MM-YYYY')                       AS input_date,
       COUNT(CASE WHEN goal = '1' THEN 1 END)                                                 AS "1",
       COUNT(CASE WHEN goal = '3' THEN 1 END)                                                 AS "3",
       COUNT(CASE WHEN goal in ('305', '307') THEN 1 END)                                     AS "305,307 D",
       COUNT(CASE WHEN goal in ('13', '14', '140') THEN 1 END)                                AS "13,14,140 Z",
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
WHERE status IN ('1', '2', '4', '6', '8')
GROUP BY TO_DATE(initial_input_date, 'DD-MM-YYYY')
ORDER BY TO_DATE(initial_input_date, 'DD-MM-YYYY') DESC
    """
    return query