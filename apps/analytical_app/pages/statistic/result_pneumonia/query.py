# Все пневмонии в талонах (оптимизировано: вычисления через CTE, без ведущих wildcard)
sql_query_pneumonia_in_talon = """
with t as (
    select
        to_date(treatment_end, 'DD-MM-YYYY') as dt,
        split_part(main_diagnosis, ' ', 1) as code,
        case_code
    from data_loader_omsdata
    where to_date(treatment_end, 'DD-MM-YYYY') between to_date(:start_date, 'DD-MM-YYYY')
                                                   and to_date(:end_date,   'DD-MM-YYYY')
)
select 'Первичные' as "Случаи",
       sum(case when code like 'J12%' then 1 else 0 end) as "J12",
       sum(case when code like 'J13%' then 1 else 0 end) as "J13",
       sum(case when code like 'J14%' then 1 else 0 end) as "J14",
       sum(case when code like 'J15%' then 1 else 0 end) as "J15",
       sum(case when code like 'J16%' then 1 else 0 end) as "J16",
       sum(case when code like 'J18%' then 1 else 0 end) as "J18",
       sum(case when code like 'J12%' or code like 'J13%' or code like 'J14%'
                 or code like 'J15%' or code like 'J16%' or code like 'J18%'
                then 1 else 0 end) as "Всего"
from t
where case_code = 'Первичный'

union all
select 'Повторные' as "Случаи",
       sum(case when code like 'J12%' then 1 else 0 end) as "J12",
       sum(case when code like 'J13%' then 1 else 0 end) as "J13",
       sum(case when code like 'J14%' then 1 else 0 end) as "J14",
       sum(case when code like 'J15%' then 1 else 0 end) as "J15",
       sum(case when code like 'J16%' then 1 else 0 end) as "J16",
       sum(case when code like 'J18%' then 1 else 0 end) as "J18",
       sum(case when code like 'J12%' or code like 'J13%' or code like 'J14%'
                 or code like 'J15%' or code like 'J16%' or code like 'J18%'
                then 1 else 0 end) as "Всего"
from t
where case_code = 'Повторный'
"""

sql_query_pneumonia_in_talon_korpus_first = """
with t as (
    select
        department,
        split_part(main_diagnosis, ' ', 1) as code,
        to_date(treatment_end, 'DD-MM-YYYY') as dt
    from data_loader_omsdata
    where case_code = 'Первичный'
      and to_date(treatment_end, 'DD-MM-YYYY') between to_date(:start_date, 'DD-MM-YYYY')
                                                   and to_date(:end_date,   'DD-MM-YYYY')
)
select department as "Корпус",
       sum(case when code like 'J12%' then 1 else 0 end) as "J12",
       sum(case when code like 'J13%' then 1 else 0 end) as "J13",
       sum(case when code like 'J14%' then 1 else 0 end) as "J14",
       sum(case when code like 'J15%' then 1 else 0 end) as "J15",
       sum(case when code like 'J16%' then 1 else 0 end) as "J16",
       sum(case when code like 'J18%' then 1 else 0 end) as "J18",
       sum(case when code like 'J12%' or code like 'J13%' or code like 'J14%'
                 or code like 'J15%' or code like 'J16%' or code like 'J18%'
                then 1 else 0 end) as "Всего"
from t
group by department
"""

sql_query_pneumonia_in_talon_korpus_second = """
with t as (
    select
        department,
        split_part(main_diagnosis, ' ', 1) as code,
        to_date(treatment_end, 'DD-MM-YYYY') as dt
    from data_loader_omsdata
    where case_code = 'Повторный'
      and to_date(treatment_end, 'DD-MM-YYYY') between to_date(:start_date, 'DD-MM-YYYY')
                                                   and to_date(:end_date,   'DD-MM-YYYY')
)
select department as "Корпус",
       sum(case when code like 'J12%' then 1 else 0 end) as "J12",
       sum(case when code like 'J13%' then 1 else 0 end) as "J13",
       sum(case when code like 'J14%' then 1 else 0 end) as "J14",
       sum(case when code like 'J15%' then 1 else 0 end) as "J15",
       sum(case when code like 'J16%' then 1 else 0 end) as "J16",
       sum(case when code like 'J18%' then 1 else 0 end) as "J18",
       sum(case when code like 'J12%' or code like 'J13%' or code like 'J14%'
                 or code like 'J15%' or code like 'J16%' or code like 'J18%'
                then 1 else 0 end) as "Всего"
from t
group by department
"""
