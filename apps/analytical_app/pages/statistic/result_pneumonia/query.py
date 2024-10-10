# Все пневмонии в талонах
sql_query_pneumonia_in_talon = """
select 'Первичные' as Случаи,
       sum(case when main_diagnosis like '%J12%' then 1 else 0 end) as J12,
       sum(case when main_diagnosis like '%J13%' then 1 else 0 end) as J13,
       sum(case when main_diagnosis like '%J14%' then 1 else 0 end) as J14,
       sum(case when main_diagnosis like '%J15%' then 1 else 0 end) as J15,
       sum(case when main_diagnosis like '%J16%' then 1 else 0 end) as J16,
       sum(case when main_diagnosis like '%J18%' then 1 else 0 end) as J18,
       sum(case
               when main_diagnosis like ANY (array ['%J12%','%J13%','%J14%','%J15%','%J16%','%J18%'])
                   then 1
               else 0 end)                                                         as Всего

from data_loader_omsdata
where "case" = 'Первичный' and 
to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')

UNION ALL
select 'Повторные' as Случаи,
       sum(case when main_diagnosis like '%J12%' then 1 else 0 end) as J12,
       sum(case when main_diagnosis like '%J13%' then 1 else 0 end) as J13,
       sum(case when main_diagnosis like '%J14%' then 1 else 0 end) as J14,
       sum(case when main_diagnosis like '%J15%' then 1 else 0 end) as J15,
       sum(case when main_diagnosis like '%J16%' then 1 else 0 end) as J16,
       sum(case when main_diagnosis like '%J18%' then 1 else 0 end) as J18,
       sum(case
               when main_diagnosis like ANY (array ['%J12%','%J13%','%J14%','%J15%','%J16%','%J18%'])
                   then 1
               else 0 end)                                                         as Всего

from data_loader_omsdata
where "case" = 'Повторный' and 
to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
"""

sql_query_pneumonia_in_talon_korpus_first = """
select department as Корпус,
       sum(case when main_diagnosis like '%J12%' then 1 else 0 end) as J12,
       sum(case when main_diagnosis like '%J13%' then 1 else 0 end) as J13,
       sum(case when main_diagnosis like '%J14%' then 1 else 0 end) as J14,
       sum(case when main_diagnosis like '%J15%' then 1 else 0 end) as J15,
       sum(case when main_diagnosis like '%J16%' then 1 else 0 end) as J16,
       sum(case when main_diagnosis like '%J18%' then 1 else 0 end) as J18,
       sum(case
               when main_diagnosis like ANY (array ['%J12%','%J13%','%J14%','%J15%','%J16%','%J18%'])
                   then 1
               else 0 end)                                                         as Всего

from data_loader_omsdata
where "case" = 'Первичный' and
to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
group by department
"""

sql_query_pneumonia_in_talon_korpus_second = """
select department as Корпус,
       sum(case when main_diagnosis like '%J12%' then 1 else 0 end) as J12,
       sum(case when main_diagnosis like '%J13%' then 1 else 0 end) as J13,
       sum(case when main_diagnosis like '%J14%' then 1 else 0 end) as J14,
       sum(case when main_diagnosis like '%J15%' then 1 else 0 end) as J15,
       sum(case when main_diagnosis like '%J16%' then 1 else 0 end) as J16,
       sum(case when main_diagnosis like '%J18%' then 1 else 0 end) as J18,
       sum(case
               when main_diagnosis like ANY (array ['%J12%','%J13%','%J14%','%J15%','%J16%','%J18%'])
                   then 1
               else 0 end)                                                         as Всего

from data_loader_omsdata
where "case" = 'Повторный' and 
to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
group by department
"""
