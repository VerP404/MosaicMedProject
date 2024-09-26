def sql_query_by_doctors(sql_cond=None):
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
                SUM(CASE
                        WHEN "Цель" in ('1', '5', '7', '9', '10', '13', '14', '140', '64', '640') THEN 1
                        ELSE 0 END)                                                            AS "Посещения",
                SUM(CASE WHEN "Цель" in ('30', '301', '305') THEN 1 ELSE 0 END)                AS "Обращения",
                SUM(CASE WHEN "Цель" in ('22') THEN 1 ELSE 0 END)                              AS "Неотложка",
                SUM(CASE WHEN "Цель" in ('3') THEN 1 ELSE 0 END)                               AS "Д. наблюдение",
                SUM(CASE WHEN "Цель" in ('561') THEN 1 ELSE 0 END)                             AS "Лаб. исследования",
                SUM(CASE WHEN "Цель" in ('541') THEN 1 ELSE 0 END)                             AS "УЗИ и эндоскопия",
                SUM(CASE WHEN "Цель" in ('32') THEN 1 ELSE 0 END)                              AS "32 цель",
                SUM(CASE WHEN "Цель" in ('307') THEN 1 ELSE 0 END)                             AS "школа СД",
                SUM(CASE WHEN "Цель" in ('В дневном стационаре', 'На дому') THEN 1 ELSE 0 END) AS "Дневной стационар",
                SUM(CASE WHEN "Цель" in ('ДВ4') THEN 1 ELSE 0 END)                             AS "ДВ4",
                SUM(CASE WHEN "Цель" in ('ДВ2') THEN 1 ELSE 0 END)                             AS "ДВ2",
                SUM(CASE WHEN "Цель" in ('ОПВ') THEN 1 ELSE 0 END)                             AS "ОПВ",
                SUM(CASE WHEN "Цель" in ('УД1') THEN 1 ELSE 0 END)                             AS "УД1",
                SUM(CASE WHEN "Цель" in ('УД2') THEN 1 ELSE 0 END)                             AS "УД2",
                SUM(CASE WHEN "Цель" in ('ДР1') THEN 1 ELSE 0 END)                             AS "ДР1",
                SUM(CASE WHEN "Цель" in ('ДР2') THEN 1 ELSE 0 END)                             AS "ДР2",
                SUM(CASE WHEN "Цель" in ('ПН1') THEN 1 ELSE 0 END)                             AS "ПН1",
                SUM(CASE WHEN "Цель" in ('ДС2') THEN 1 ELSE 0 END)                             AS "ДС2"
from (SELECT *, "Подразделение" || ' ' || split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' || ' ' ||
             CASE
                 WHEN "Врач (Профиль МП)" ~ '\(.*\)' THEN
                     substring("Врач (Профиль МП)" from 1 for position('(' in "Врач (Профиль МП)") - 1)
                 when "Врач" in ('30100001 Гугунава Георгий Хвичаевич', '30100101 Гугунава Георгий Хвичаевич') THEN
                     "Врач (Профиль МП)" || ' ' || '30100001'
                 when "Врач" in ('30100002 Гугунава Георгий Хвичаевич', '30100102 Гугунава Георгий Хвичаевич') THEN
                     "Врач (Профиль МП)" || ' ' || '30100002'
                 when "Врач" in ('11016001 Антонович Ирина Сергеевна', '11016001 Антонович Ирина Сергеевна') THEN
                     "Врач (Профиль МП)" || ' ' || '11016001'
                 when "Врач" in ('11016002 Антонович Ирина Сергеевна', '11016002 Антонович Ирина Сергеевна') THEN
                     "Врач (Профиль МП)" || ' ' || '11016002'
                 ELSE
                     "Врач (Профиль МП)"
                 END AS "Корпус Врач"
      FROM oms.oms_data) as oms
WHERE "Отчетный период выгрузки" IN ({sql_cond})
  AND "Статус" IN :status_list
  AND "Тариф" != '0'
group by "ФИО Врача", "Корпус", "Профиль"
order by "Корпус", "ФИО Врача"
    """


def sql_query_by_doctors_stac_rep(sql_cond=None):
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
              AND "Тариф" != '0'
              and "Тип талона" = 'Стационар'
        group by "ФИО Врача", "Корпус", "Профиль"
        order by "Корпус","Профиль", "ФИО Врача"
    """


