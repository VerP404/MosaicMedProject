def sql_query_by_doctors_mest(sql_cond):
    return f"""
select distinct "Корпус Врач"                                                                  as "ФИО Врача",
                "Подразделение"                                                                as "Корпус",
                CASE
                    WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                        substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                    ELSE
                        "Врач (Профиль МП)"
                    END                                                                        AS "Профиль",
                count(*)                                                                       as "Всего",
                SUM(CASE WHEN "Цель" = '1' THEN 1 ELSE 0 END)                AS "1",
                SUM(CASE WHEN "Цель" = '3' THEN 1 ELSE 0 END)                AS "3",
                SUM(CASE WHEN "Цель" = '5' THEN 1 ELSE 0 END)                AS "5",
                SUM(CASE WHEN "Цель" = '7' THEN 1 ELSE 0 END)                AS "7",
                SUM(CASE WHEN "Цель" = '9' THEN 1 ELSE 0 END)                AS "9",
                SUM(CASE WHEN "Цель" = '10' THEN 1 ELSE 0 END)                AS "10",
                SUM(CASE WHEN "Цель" = '13' THEN 1 ELSE 0 END)                AS "13",
                SUM(CASE WHEN "Цель" = '14' THEN 1 ELSE 0 END)                AS "14",
                SUM(CASE WHEN "Цель" = '22' THEN 1 ELSE 0 END)                AS "22",
                SUM(CASE WHEN "Цель" = '30' THEN 1 ELSE 0 END)                AS "30",
                SUM(CASE WHEN "Цель" = '32' THEN 1 ELSE 0 END)                AS "32",
                SUM(CASE WHEN "Цель" = '64' THEN 1 ELSE 0 END)                AS "64",
                SUM(CASE WHEN "Цель" = '140' THEN 1 ELSE 0 END)                AS "140",
                SUM(CASE WHEN "Цель" = '301' THEN 1 ELSE 0 END)                AS "301",
                SUM(CASE WHEN "Цель" = '305' THEN 1 ELSE 0 END)                AS "305",
                SUM(CASE WHEN "Цель" = '307' THEN 1 ELSE 0 END)                AS "307",
                SUM(CASE WHEN "Цель" = '541' THEN 1 ELSE 0 END)                AS "541",
                SUM(CASE WHEN "Цель" = '561' THEN 1 ELSE 0 END)                AS "561",
                SUM(CASE WHEN "Цель" = '640' THEN 1 ELSE 0 END)                AS "640"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
    and "Код СМО" like '360%'
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус","Профиль", "ФИО Врача"
    """

def sql_query_by_doctors_inog(sql_cond):
    return f"""
select distinct "Корпус Врач"                                                                  as "ФИО Врача",
                "Подразделение"                                                                as "Корпус",
                CASE
                    WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                        substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                    ELSE
                        "Врач (Профиль МП)"
                    END                                                                        AS "Профиль",
                count(*)                                                                       as "Всего",
                SUM(CASE WHEN "Цель" = '1' THEN 1 ELSE 0 END)                AS "1",
                SUM(CASE WHEN "Цель" = '3' THEN 1 ELSE 0 END)                AS "3",
                SUM(CASE WHEN "Цель" = '5' THEN 1 ELSE 0 END)                AS "5",
                SUM(CASE WHEN "Цель" = '7' THEN 1 ELSE 0 END)                AS "7",
                SUM(CASE WHEN "Цель" = '9' THEN 1 ELSE 0 END)                AS "9",
                SUM(CASE WHEN "Цель" = '10' THEN 1 ELSE 0 END)                AS "10",
                SUM(CASE WHEN "Цель" = '13' THEN 1 ELSE 0 END)                AS "13",
                SUM(CASE WHEN "Цель" = '14' THEN 1 ELSE 0 END)                AS "14",
                SUM(CASE WHEN "Цель" = '22' THEN 1 ELSE 0 END)                AS "22",
                SUM(CASE WHEN "Цель" = '30' THEN 1 ELSE 0 END)                AS "30",
                SUM(CASE WHEN "Цель" = '32' THEN 1 ELSE 0 END)                AS "32",
                SUM(CASE WHEN "Цель" = '64' THEN 1 ELSE 0 END)                AS "64",
                SUM(CASE WHEN "Цель" = '140' THEN 1 ELSE 0 END)                AS "140",
                SUM(CASE WHEN "Цель" = '301' THEN 1 ELSE 0 END)                AS "301",
                SUM(CASE WHEN "Цель" = '305' THEN 1 ELSE 0 END)                AS "305",
                SUM(CASE WHEN "Цель" = '307' THEN 1 ELSE 0 END)                AS "307",
                SUM(CASE WHEN "Цель" = '541' THEN 1 ELSE 0 END)                AS "541",
                SUM(CASE WHEN "Цель" = '561' THEN 1 ELSE 0 END)                AS "561",
                SUM(CASE WHEN "Цель" = '640' THEN 1 ELSE 0 END)                AS "640"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE "Отчетный период выгрузки" IN ({sql_cond})
AND "Статус" IN :status_list
    and "Код СМО" not like '360%'
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус","Профиль", "ФИО Врача"
    """

def sql_query_by_doctors_stac(sql_cond):
    return f"""
select distinct "Корпус Врач"                                                                  as "ФИО Врача",
                "Подразделение"                                                                as "Корпус",
                CASE
                    WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                        substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                    ELSE
                        "Врач (Профиль МП)"
                    END                                                                        AS "Профиль",
                count(*)                                                                       as "Всего",
                SUM(CASE WHEN "Цель" = 'В дневном стационаре' THEN 1 ELSE 0 END)                AS "В дневном",
                SUM(CASE WHEN "Цель" = 'На дому' THEN 1 ELSE 0 END)                AS "На дому",
                sum(CAST("Посещения" AS numeric(8))) as "К-во посещений"

from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE "Отчетный период выгрузки" IN ({sql_cond})
AND "Статус" IN :status_list
    and "Тип талона" = 'Стационар'
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус","Профиль", "ФИО Врача"
    """
