def sql_query_econ_1(sql_cond):
    return f"""
        with subquery as (
        SELECT
            CASE
                WHEN "Подразделение" = 'ГП №3' THEN 'Корпус №1'
                WHEN "Подразделение" = 'ОАПП №1' THEN 'Корпус №2'
                WHEN "Подразделение" = 'ГП №11' THEN 'Корпус №3'
                WHEN "Подразделение" = 'ОАПП №2' THEN 'Корпус №6'
                WHEN "Подразделение" = 'ДП №1' THEN 'ДП №1'
                WHEN "Подразделение" LIKE 'ДП №8%' THEN 'ДП №8'
                WHEN "Подразделение" = 'ЖК' THEN 'ЖК'
                ELSE "Подразделение"
            END AS "Корпус",
            CASE
                WHEN "Цель" IN ('1', '5', '7', '9', '10', '14', '140', '640') THEN 1
                ELSE 0
            END AS Посещения,
            CASE
                WHEN "Цель" = '30' THEN 1
                ELSE 0
            END AS Обращения,
            CASE
                WHEN "Цель" = '22' THEN 1
                ELSE 0
            END AS Неотложка,
            CASE
                WHEN "Цель" = '3' THEN 1
                ELSE 0
            END AS Дисп_набл
        FROM
            oms.oms_data
        WHERE "Отчетный период выгрузки" IN ({sql_cond})
          AND "Статус" IN :status_list
          AND "Тариф" != '0'
          and "Код СМО" like '360%'
          AND "Санкции" is null
    )

    SELECT
        "Корпус",
        SUM(Посещения) AS Посещения,
        SUM(Обращения) AS Обращения,
        SUM(Неотложка) AS Неотложка,
        SUM(Дисп_набл) AS Дисп_набл
    FROM subquery
    GROUP BY
        ROLLUP("Корпус")
    ORDER BY
        CASE
            WHEN "Корпус" = 'Корпус №1' THEN 1
            WHEN "Корпус" = 'Корпус №2' THEN 2
            WHEN "Корпус" = 'Корпус №3' THEN 3
            WHEN "Корпус" = 'Корпус №6' THEN 4
            WHEN "Корпус" = 'ДП №1' THEN 5
            WHEN "Корпус" = 'ДП №8' THEN 6
            WHEN "Корпус" = 'ЖК' THEN 7
            ELSE 8
        END;
    """


def sql_query_econ_2(sql_cond):
    return f"""
with subquery as (
    SELECT
        CASE
            WHEN "Подразделение" = 'ГП №3' THEN 'Корпус №1'
            WHEN "Подразделение" = 'ОАПП №1' THEN 'Корпус №2'
            WHEN "Подразделение" = 'ГП №11' and "Врач (Профиль МП)" not in ('136 акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)') 
                    and "Врач" not in ('11112018 Шадрин Илья Сергеевич') THEN 'Корпус №3'
            WHEN "Подразделение" = 'ОАПП №2' THEN 'Корпус №6'
            WHEN "Подразделение" = 'ДП №1' THEN 'ДП №1'
            WHEN "Подразделение" LIKE 'ДП №8%' THEN 'ДП №8'
            WHEN "Подразделение" = 'ГП №11' and "Врач" in ('11136001 Сорокина Татьяна Валентиновна', 
                                                           '11136005 Карандеев Максим Анатольевич', 
                                                           '11112018 Шадрин Илья Сергеевич') THEN 'ЦАХ'
            WHEN "Подразделение" = 'ГП №11' and "Врач" in ('11136007 Столярова Тамара Владимировна', 
                                                           '11136014 Войтко Валерия Александровна') THEN 'Гинекология'
            ELSE '-'
        END AS "Корпус",
        CASE
            WHEN "Цель" = 'В дневном стационаре' THEN 1
            ELSE 0
        END AS "Дневной",
            CASE
            WHEN "Цель" = 'На дому' THEN 1
            ELSE 0
        END AS "На дому"
    FROM
        oms.oms_data
    WHERE "Отчетный период выгрузки" IN ({sql_cond})
          AND "Статус" IN :status_list
          AND "Цель" in ('В дневном стационаре', 'На дому')
          AND "Тариф" != '0'
          and "Код СМО" like '360%'
          AND "Санкции" is null
)

SELECT
    "Корпус",
    SUM("Дневной") AS "Дневной стационар",
    SUM("На дому") AS "На дому"
FROM subquery
where "Корпус" != '-'
GROUP BY
    ROLLUP("Корпус")
ORDER BY
    CASE
        WHEN "Корпус" = 'Корпус №1' THEN 1
        WHEN "Корпус" = 'Корпус №2' THEN 2
        WHEN "Корпус" = 'Корпус №3' THEN 3
        WHEN "Корпус" = 'Корпус №6' THEN 4
        WHEN "Корпус" = 'ДП №1' THEN 5
        WHEN "Корпус" = 'ДП №8' THEN 6
        WHEN "Корпус" = 'ЦАХ' THEN 7
        WHEN "Корпус" = 'Гинекология' THEN 8
        ELSE 9
    END;
    """

def sql_query_econ_3(sql_cond):
    return f"""
        select "Подразделение" as Корпус,
           sum(CASE when "Цель" = 'ПН1' then 1 else 0 end) as ПН1,
           sum(CASE when "Цель" = 'ДС2' then 1 else 0  end) as ДС2
        from oms.oms_data
        where "Отчетный период выгрузки" IN ({sql_cond})
          AND "Статус" IN :status_list
          AND "Цель" in ('ПН1', 'ДС2')
          AND "Тариф" != '0'
          and "Код СМО" like '360%'
          AND "Санкции" is null
        group by ROLLUP(Корпус);
    """

def sql_query_econ_4(sql_cond):
    return f"""
        select case
                    WHEN "Подразделение" = 'ГП №3' THEN 'ГП №3'
                    WHEN "Подразделение" = 'ОАПП №1' THEN 'ГП №3'
                    WHEN "Подразделение" = 'ОАПП №2' THEN 'ГП №3'
                    WHEN "Подразделение" = 'ГП №11' THEN 'ГП №11'
                    ELSE '-' end as Корпус,
               sum(CASE when "Цель" = 'ДВ4' then 1 else 0 end) as ДВ4,
               sum(CASE when "Цель" = 'ДВ2' then 1 else 0  end) as ДВ2,
               sum(CASE when "Цель" = 'ОПВ' then 1 else 0  end) as ОПВ,
               sum(CASE when "Цель" = 'УД1' then 1 else 0  end) as УД1,
               sum(CASE when "Цель" = 'УД2' then 1 else 0  end) as УД2
        
        from oms.oms_data
        where "Отчетный период выгрузки" IN ({sql_cond})
                AND "Статус" IN :status_list
                AND "Цель" in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2')
                AND "Подразделение" in ('ГП №11', 'ГП №3', 'ОАПП №1', 'ОАПП №2')
                AND "Тариф" != '0'
                and "Код СМО" like '360%'
                AND "Санкции" is null
            group by ROLLUP(Корпус);
    """