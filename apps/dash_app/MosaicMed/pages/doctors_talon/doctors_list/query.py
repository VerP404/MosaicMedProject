def sql_query_by_doc(sql_cond):
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
                SUM(CASE WHEN "Цель" in ('1') THEN 1 ELSE 0 END)                              AS "1",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "3",
                SUM(CASE WHEN "Цель" in ('5') THEN 1 ELSE 0 END)                              AS "5",
                SUM(CASE WHEN "Цель" in ('7') THEN 1 ELSE 0 END)                              AS "7",
                SUM(CASE WHEN "Цель" in ('9') THEN 1 ELSE 0 END)                              AS "9",
                SUM(CASE WHEN "Цель" in ('10') THEN 1 ELSE 0 END)                              AS "10",
                SUM(CASE WHEN "Цель" in ('13') THEN 1 ELSE 0 END)                              AS "13",
                SUM(CASE WHEN "Цель" in ('14') THEN 1 ELSE 0 END)                              AS "14",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "22",
                SUM(CASE WHEN "Цель" in ('30') THEN 1 ELSE 0 END)                              AS "30",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32",
                SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)                              AS "64",
                SUM(CASE WHEN "Цель" in ('140') THEN 1 ELSE 0 END)                              AS "140",
                SUM(CASE WHEN "Цель" in ('301') THEN 1 ELSE 0 END)                             AS "301",
                SUM(CASE WHEN "Цель" in ('305') THEN 1 ELSE 0 END)                              AS "305",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                              AS "307",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                              AS "541",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                              AS "561",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре') THEN 1 ELSE 0 END)              AS "В дс",
                SUM(CASE WHEN "Цель" in ('На дому') THEN 1 ELSE 0 END)                              AS "На дому",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """


def sql_query_by_doc_end_treatment(sql_cond=None):
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
                SUM(CASE WHEN "Цель" in ('1') THEN 1 ELSE 0 END)                              AS "1",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "3",
                SUM(CASE WHEN "Цель" in ('5') THEN 1 ELSE 0 END)                              AS "5",
                SUM(CASE WHEN "Цель" in ('7') THEN 1 ELSE 0 END)                              AS "7",
                SUM(CASE WHEN "Цель" in ('9') THEN 1 ELSE 0 END)                              AS "9",
                SUM(CASE WHEN "Цель" in ('10') THEN 1 ELSE 0 END)                              AS "10",
                SUM(CASE WHEN "Цель" in ('13') THEN 1 ELSE 0 END)                              AS "13",
                SUM(CASE WHEN "Цель" in ('14') THEN 1 ELSE 0 END)                              AS "14",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "22",
                SUM(CASE WHEN "Цель" in ('30') THEN 1 ELSE 0 END)                              AS "30",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32",
                SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)                              AS "64",
                SUM(CASE WHEN "Цель" in ('140') THEN 1 ELSE 0 END)                              AS "140",
                SUM(CASE WHEN "Цель" in ('301') THEN 1 ELSE 0 END)                             AS "301",
                SUM(CASE WHEN "Цель" in ('305') THEN 1 ELSE 0 END)                              AS "305",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                              AS "307",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                              AS "541",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                              AS "561",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре') THEN 1 ELSE 0 END)              AS "В дс",
                SUM(CASE WHEN "Цель" in ('На дому') THEN 1 ELSE 0 END)                              AS "На дому",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE to_date("Окончание лечения", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
  AND "Тариф" != '0'
  AND "Статус" IN :status_list
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """


def sql_query_by_doc_end_form(sql_cond=None):
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
                SUM(CASE WHEN "Цель" in ('1') THEN 1 ELSE 0 END)                              AS "1",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "3",
                SUM(CASE WHEN "Цель" in ('5') THEN 1 ELSE 0 END)                              AS "5",
                SUM(CASE WHEN "Цель" in ('7') THEN 1 ELSE 0 END)                              AS "7",
                SUM(CASE WHEN "Цель" in ('9') THEN 1 ELSE 0 END)                              AS "9",
                SUM(CASE WHEN "Цель" in ('10') THEN 1 ELSE 0 END)                              AS "10",
                SUM(CASE WHEN "Цель" in ('13') THEN 1 ELSE 0 END)                              AS "13",
                SUM(CASE WHEN "Цель" in ('14') THEN 1 ELSE 0 END)                              AS "14",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "22",
                SUM(CASE WHEN "Цель" in ('30') THEN 1 ELSE 0 END)                              AS "30",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32",
                SUM(CASE WHEN "Цель" in ('64') THEN 1 ELSE 0 END)                              AS "64",
                SUM(CASE WHEN "Цель" in ('140') THEN 1 ELSE 0 END)                              AS "140",
                SUM(CASE WHEN "Цель" in ('301') THEN 1 ELSE 0 END)                             AS "301",
                SUM(CASE WHEN "Цель" in ('305') THEN 1 ELSE 0 END)                              AS "305",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                              AS "307",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                              AS "541",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                              AS "561",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре') THEN 1 ELSE 0 END)              AS "В дс",
                SUM(CASE WHEN "Цель" in ('На дому') THEN 1 ELSE 0 END)                              AS "На дому",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
  AND "Тариф" != '0'
  AND "Статус" IN :status_list
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """