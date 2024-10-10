def sql_query_amb_def(months_placeholder):
    return f"""
SELECT goal,
               COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '4' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,4,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
        FROM (SELECT *,
                     department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
                     '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
                     CASE
                         WHEN doctor_profile ~ '\\(.*\\)' THEN
                             substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
                         ELSE
                             doctor_profile
                         END AS "Корпус Врач"
              FROM data_loader_omsdata) as oms
        WHERE goal IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '32', '64', '640', '301', '305',
                        '307', '541', '561')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})

        GROUP BY goal

        UNION ALL

        SELECT
    CASE
        WHEN goal IN ('1', '5', '7', '9', '10', '32') THEN 'Посещения(1, 5, 7, 9, 10, 32)'
        WHEN goal IN ('30', '301', '305', '307') THEN 'Обращения(30, 301, 305, 307)'
        WHEN goal IN ('22') THEN 'Неотложка(22)'
        WHEN goal IN ('3') THEN 'Диспансерное набл.(3)'
        ELSE 'Другая цель'        
    END AS "Тип",
    COUNT(*) AS Всего,
    SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END) AS "Оплачен(3)",
    SUM(CASE WHEN status IN ('1', '2', '3', '4', '6', '8') THEN 1 ELSE 0 END) AS "В работе(1,2,3,4,6,8)",
    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS "Выставлен(2)",
    SUM(CASE WHEN status IN ('0', '13', '17') THEN 1 ELSE 0 END) AS "Отменен(0,13,17)",
    SUM(CASE WHEN status IN ('5', '7', '12') THEN 1 ELSE 0 END) AS "Отказан(5,7,12)",
    SUM(CASE WHEN status IN ('6', '8') THEN 1 ELSE 0 END) AS "Исправлен(6,8)",
    SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END) AS "0",
    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS "1",
    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS "2",
    SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END) AS "3",
    SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END) AS "5",
    SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END) AS "6",
    SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END) AS "7",
    SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END) AS "8",
    SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
    SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
    SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
FROM (
    SELECT *,
           department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
           '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
           CASE
               WHEN doctor_profile ~ '\\(.*\\)' THEN
                   substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
               ELSE
                   doctor_profile
           END AS "Корпус Врач"
    FROM data_loader_omsdata
) AS oms
WHERE  
    goal IN ('1', '3', '5', '7', '9', '10', '13', '14', '140', '22', '30', '32', '64', '640', '301', '305',
                '307', '541', '561')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})
GROUP BY "Тип"
    """


def sql_query_stac_def(months_placeholder):
    return f"""
 SELECT goal,
               COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
        FROM (SELECT *,
                     department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
                     '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
                     CASE
                         WHEN doctor_profile ~ '\\(.*\\)' THEN
                             substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
                         ELSE
                             doctor_profile
                         END AS "Корпус Врач"
              FROM data_loader_omsdata) as oms
        WHERE goal IN ('В дневном стационаре', 'На дому', 'Стационарно')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})
        GROUP BY goal
        ORDER BY CASE goal
                     WHEN 'На дому' THEN 1
                     WHEN 'В дневном стационаре' THEN 2
                     WHEN 'Стационарно' THEN 3
                     END
        """


def sql_query_dd_def(months_placeholder):
    return f"""
 SELECT goal,
               COUNT(*)                                       AS Всего,
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "Оплачен(3)",
               SUM(CASE WHEN status = '1' or status = '2' or status = '3' or status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "В работе(1,2,3,6,8)",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "В ТФОМС(2)",
               SUM(CASE WHEN status = '0' or status = '13' or status = '17' THEN 1 ELSE 0 END)  AS "Отменен(0,13,17)",
               SUM(CASE WHEN status = '5' or status = '7' or status = '12' THEN 1 ELSE 0 END)  AS "Отказан(5,7,12)",
               SUM(CASE WHEN status = '6' or status = '8' THEN 1 ELSE 0 END)  AS "Исправлен(6,8)",               
               SUM(CASE WHEN status = '0' THEN 1 ELSE 0 END)  AS "0",
               SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END)  AS "1",
               SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END)  AS "2",
               SUM(CASE WHEN status = '3' THEN 1 ELSE 0 END)  AS "3",
               SUM(CASE WHEN status = '5' THEN 1 ELSE 0 END)  AS "5",
               SUM(CASE WHEN status = '6' THEN 1 ELSE 0 END)  AS "6",
               SUM(CASE WHEN status = '7' THEN 1 ELSE 0 END)  AS "7",
               SUM(CASE WHEN status = '8' THEN 1 ELSE 0 END)  AS "8",
               SUM(CASE WHEN status = '12' THEN 1 ELSE 0 END) AS "12",
               SUM(CASE WHEN status = '13' THEN 1 ELSE 0 END) AS "13",
               SUM(CASE WHEN status = '17' THEN 1 ELSE 0 END) AS "17"
        FROM (SELECT *,
                     department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) ||
                     '.' || left(split_part(doctor, ' ', 4), 1) || '.' || ' ' ||
                     CASE
                         WHEN doctor_profile ~ '\\(.*\\)' THEN
                             substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
                         ELSE
                             doctor_profile
                         END AS "Корпус Врач"
              FROM data_loader_omsdata) as oms

        WHERE amount != '0'
          AND goal IN ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1', 'ДС2')
          AND "Корпус Врач" = :value_doctor
          AND report_period IN ({months_placeholder})

        GROUP BY goal
        ORDER BY CASE goal
                     WHEN 'ДВ4' THEN 1
                     WHEN 'ДВ2' THEN 2
                     WHEN 'ОПВ' THEN 3
                     WHEN 'УД1' THEN 4
                     WHEN 'УД2' THEN 5
                     WHEN 'ДР1' THEN 5
                     WHEN 'ДР2' THEN 5
                     WHEN 'ПН1' THEN 6
                     WHEN 'ДС2' THEN 7
                     END
        """
