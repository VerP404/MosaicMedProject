from apps.analytical_app.pages.SQL_query.query import base_query, columns_by_status_oms

AMB_GOALS = (
    "'1', '3', '5', '7', '9', '10', '13', '14', '140', "
    "'22', '30', '301', '305', '307', '64', '640', '32'"
)
DD_GOALS = "'ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ПН1', 'ДС2'"
DD_GOALS_ADULT = "'ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2'"
DD_GOALS_CHILD = "'ПН1', 'ДС2'"


def _sql_num(col):
    return (
        f"CASE WHEN TRIM(COALESCE({col}, '')) ~ '^-?[0-9]+(\\.[0-9]+)?$' "
        f"THEN CAST(TRIM({col}) AS numeric) ELSE 0 END"
    )


VISITS_TALON_SQL = _sql_num("visits")
HOME_VISITS_SQL = _sql_num("home_visits")
VISITS_ACCOUNT_SQL = f"""
CASE
    WHEN goal IN ({AMB_GOALS}) THEN {VISITS_TALON_SQL}
    WHEN goal IN ({DD_GOALS}) THEN 1
    WHEN goal = 'В дневном стационаре' THEN 0
    ELSE {VISITS_TALON_SQL}
END
"""

GROUP_SQL = """
CASE
    WHEN target_categories LIKE '%Диспансерное наблюдение%' THEN 'Диспансерное наблюдение'
    WHEN target_categories LIKE '%Дневной стационар, Стационар%' THEN 'Стационар - дневной'
    WHEN target_categories LIKE '%Стационарно, Стационар%' THEN 'Стационар - стационарно'
    WHEN target_categories LIKE '%Стационар на дому, Стационар%' THEN 'Стационар - на дому'
    ELSE COALESCE(NULLIF(TRIM(target_categories), ''), 'Без группы')
END
"""

UNIQUE_SQL = "COUNT(DISTINCT NULLIF(TRIM(enp), ''))"


# Отчет по посещениям
sql_query_visits = f"""
SELECT Тип,
       SUM("Количество талонов") as "Общее количество талонов",
       SUM("Количество посещений") as "Общее количество посещений",
       SUM("Уникальные пациенты") as "Общее количество уникальных пациентов"
FROM (
    SELECT 'Взрослые' as Тип,
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    FROM (
        SELECT SUM(CASE WHEN department NOT LIKE '%ДП%' THEN 1 ELSE 0 END) as все_талоны,
               SUM(CASE WHEN goal IN ({AMB_GOALS}) THEN {VISITS_TALON_SQL} ELSE 0 END) as pos,
               SUM(CASE WHEN goal IN ({DD_GOALS_ADULT}) THEN 1 ELSE 0 END) as dd,
               SUM(CASE WHEN goal = 'В дневном стационаре' THEN {VISITS_TALON_SQL} ELSE 0 END) as stac,
               COUNT(DISTINCT policy) as Уникальные
        FROM data_loader_omsdata
        WHERE to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          AND department NOT LIKE '%ДП%'
    ) as tab1

    UNION ALL

    SELECT 'Дети' as Тип,
           все_талоны,
           pn + pos - stac as "Количество посещений",
           Уникальные_дети as "Уникальные пациенты"
    FROM (
        SELECT SUM(CASE WHEN department LIKE '%ДП%' THEN 1 ELSE 0 END) as все_талоны,
               SUM(CASE WHEN goal IN ({AMB_GOALS}) THEN {VISITS_TALON_SQL} ELSE 0 END) as pos,
               SUM(CASE WHEN goal IN ({DD_GOALS_CHILD}) THEN 1 ELSE 0 END) as pn,
               SUM(CASE WHEN goal = 'В дневном стационаре' THEN {VISITS_TALON_SQL} ELSE 0 END) as stac,
               COUNT(DISTINCT policy) as Уникальные_дети
        FROM data_loader_omsdata
        WHERE to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          AND department LIKE '%ДП%'
    ) as tab2
) as result
GROUP BY rollup(Тип)
"""
sql_query_visits_korpus = f"""
select department as Тип,
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    from (select department,
                    count(*)                    as все_талоны,
                 sum(case when goal in ({AMB_GOALS}) then {VISITS_TALON_SQL} else 0 end) as pos,
                 sum(case when goal in ({DD_GOALS}) then 1 else 0 end) as dd,
                 sum(case when goal = 'В дневном стационаре' then {VISITS_TALON_SQL} else 0 end) as stac,
                 COUNT(DISTINCT policy)                                                             as Уникальные
          from data_loader_omsdata
          where
            to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          GROUP BY ROLLUP(department)) as tab
"""

sql_query_visits_korpus_spec = f"""
select department,
            case 
            WHEN doctor_profile ~ '\\(.*\\)' THEN
                substring(doctor_profile from 1 for position('(' in doctor_profile) - 1)
            ELSE
                doctor_profile
            END                                                                        AS "Профиль",
           все_талоны as "Количество талонов",
           dd + pos - stac as "Количество посещений",
           Уникальные as "Уникальные пациенты"
    from (select department,
                doctor_profile,
                    count(*)                    as все_талоны,
                 sum(case when goal in ({AMB_GOALS}) then {VISITS_TALON_SQL} else 0 end) as pos,
                 sum(case when goal in ({DD_GOALS}) then 1 else 0 end) as dd,
                 sum(case when goal = 'В дневном стационаре' then {VISITS_TALON_SQL} else 0 end) as stac,
                 COUNT(DISTINCT policy)                                                             as Уникальные
          from data_loader_omsdata
          where
            to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
          GROUP BY ROLLUP(department, doctor_profile)) as tab
"""

sql_query_visits_pos_home = f"""
select department,
                     SUM({HOME_VISITS_SQL}) AS "Количество"
from data_loader_omsdata
where to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY ROLLUP(department)
"""


def _oms_base(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
              department=None, profile=None, doctor=None,
              input_start=None, input_end=None,
              treatment_start=None, treatment_end=None,
              status_list=None):
    return base_query(
        selected_year, months_placeholder, inogorod, sanction, amount_null,
        building, department, profile, doctor,
        input_start, input_end, treatment_start, treatment_end,
        status_list=status_list,
    )


def sql_query_visits_by_group(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
                              department=None, profile=None, doctor=None,
                              input_start=None, input_end=None,
                              treatment_start=None, treatment_end=None,
                              status_list=None):
    base = _oms_base(
        selected_year, months_placeholder, inogorod, sanction, amount_null,
        building, department, profile, doctor,
        input_start, input_end, treatment_start, treatment_end, status_list,
    )
    return f"""
    {base}
    SELECT COALESCE(grp, 'Итого') AS "Группа",
           COUNT(*) AS "Талонов",
           SUM(visits_account) AS "Посещений",
           SUM(visits_talon) AS "Посещений в талоне",
           SUM(home_visits_n) AS "На дому",
           {UNIQUE_SQL} AS "Уникальные пациенты"
    FROM (
        SELECT {GROUP_SQL} AS grp,
               enp,
               {VISITS_ACCOUNT_SQL} AS visits_account,
               {VISITS_TALON_SQL} AS visits_talon,
               {HOME_VISITS_SQL} AS home_visits_n
        FROM oms
    ) t
    GROUP BY ROLLUP(grp)
    ORDER BY CASE WHEN grp IS NULL THEN 1 ELSE 0 END, "Талонов" DESC, "Группа"
    """


def sql_query_visits_by_goal(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
                             department=None, profile=None, doctor=None,
                             input_start=None, input_end=None,
                             treatment_start=None, treatment_end=None,
                             status_list=None):
    base = _oms_base(
        selected_year, months_placeholder, inogorod, sanction, amount_null,
        building, department, profile, doctor,
        input_start, input_end, treatment_start, treatment_end, status_list,
    )
    return f"""
    {base}
    SELECT COALESCE(goal_name, 'Итого') AS "Цель",
           COUNT(*) AS "Талонов",
           SUM(visits_account) AS "Посещений",
           SUM(visits_talon) AS "Посещений в талоне",
           SUM(home_visits_n) AS "На дому",
           {UNIQUE_SQL} AS "Уникальные пациенты"
    FROM (
        SELECT COALESCE(NULLIF(TRIM(goal), ''), 'Без цели') AS goal_name,
               enp,
               {VISITS_ACCOUNT_SQL} AS visits_account,
               {VISITS_TALON_SQL} AS visits_talon,
               {HOME_VISITS_SQL} AS home_visits_n
        FROM oms
    ) t
    GROUP BY ROLLUP(goal_name)
    ORDER BY CASE WHEN goal_name IS NULL THEN 1 ELSE 0 END, "Талонов" DESC, "Цель"
    """


def sql_query_visits_by_goal_status(selected_year, months_placeholder, inogorod, sanction, amount_null, building=None,
                                    department=None, profile=None, doctor=None,
                                    input_start=None, input_end=None,
                                    treatment_start=None, treatment_end=None,
                                    status_list=None):
    base = _oms_base(
        selected_year, months_placeholder, inogorod, sanction, amount_null,
        building, department, profile, doctor,
        input_start, input_end, treatment_start, treatment_end, status_list,
    )
    return f"""
    {base}
    SELECT COALESCE(goal_name, 'Итого') AS "Цель",
           {columns_by_status_oms()}
    FROM (
        SELECT COALESCE(NULLIF(TRIM(goal), ''), 'Без цели') AS goal_name,
               status
        FROM oms
    ) t
    GROUP BY ROLLUP(goal_name)
    ORDER BY CASE WHEN goal_name IS NULL THEN 1 ELSE 0 END, 2 DESC, "Цель"
    """
