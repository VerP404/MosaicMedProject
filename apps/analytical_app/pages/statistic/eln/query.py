sql_eln = """
select
    status as "Статус",
    count(*) as "Количество"
from load_data_sick_leave_sheets
where to_date(issue_date::text, 'YYYY-MM-DD')
      between to_date(CAST(:start_date AS text), 'YYYY-MM-DD')
          and to_date(CAST(:end_date AS text), 'YYYY-MM-DD')
      and ( :tvsp_all OR tvsp = ANY(:tvsp) )
      and ( :first_all OR "first" = ANY(:first_list) )
      and ( :reason_all OR coalesce(incapacity_reason_code, 'По уходу') = ANY(:reason_list) )
group by status
order by "Количество" desc
"""

sql_query_eln_doctors = """
select
    issuing_doctor as "Выдавший врач",
    tvsp as "ТВСП",
    count(*) as "Количество"
from load_data_sick_leave_sheets
where to_date(issue_date::text, 'YYYY-MM-DD')
      between to_date(CAST(:start_date AS text), 'YYYY-MM-DD')
          and to_date(CAST(:end_date AS text), 'YYYY-MM-DD')
      and ( :tvsp_all OR tvsp = ANY(:tvsp) )
      and ( :status_all OR status = ANY(:status_list) )
      and ( :first_all OR "first" = ANY(:first_list) )
      and ( :reason_all OR coalesce(incapacity_reason_code, 'По уходу') = ANY(:reason_list) )
group by issuing_doctor, tvsp
order by count(*) desc;
"""

sql_query_eln_patients = """
select
    patient_last_name as "Фамилия пациента",
    patient_first_name as "Имя пациента",
    patient_middle_name as "Отчество пациента",
    birth_date as "Дата рождения",
    gender as "Пол",
    count(*) as "Количество"
from load_data_sick_leave_sheets
where to_date(issue_date::text, 'YYYY-MM-DD')
      between to_date(CAST(:start_date AS text), 'YYYY-MM-DD')
          and to_date(CAST(:end_date AS text), 'YYYY-MM-DD')
      and ( :tvsp_all OR tvsp = ANY(:tvsp) )
      and ( :status_all OR status = ANY(:status_list) )
      and ( :first_all OR "first" = ANY(:first_list) )
      and ( :reason_all OR coalesce(incapacity_reason_code, 'По уходу') = ANY(:reason_list) )
group by patient_last_name, patient_first_name, patient_middle_name, birth_date, gender
order by count(*) desc;
"""

# Годовой анализ первичных больничных (агрегация в БД)
sql_eln_yearly = """
select
    extract(year from to_date(issue_date::text, 'YYYY-MM-DD'))::int as "Год",
    count(*) as "Количество эпизодов",
    sum(coalesce(nullif(days_count, '')::numeric, 0)) as "Сумма дней",
    round(avg(nullif(days_count, '')::numeric), 2) as "Среднее дней",
    count(distinct snils) as "Уникальных пациентов"
from load_data_sick_leave_sheets
where to_date(issue_date::text, 'YYYY-MM-DD')
      between to_date(CAST(:start_date AS text), 'YYYY-MM-DD')
          and to_date(CAST(:end_date AS text), 'YYYY-MM-DD')
      and duplicate = 'нет'
      and ( :tvsp_all OR tvsp = ANY(:tvsp) )
      and ( :first_all OR "first" = ANY(:first_list) )
      and ( :reason_all OR coalesce(incapacity_reason_code, 'По уходу') = ANY(:reason_list) )
group by 1
order by 1 desc;
"""

# Помесячный анализ первичных больничных (агрегация в БД)
sql_eln_monthly = """
select
    to_char(to_date(issue_date::text, 'YYYY-MM-DD'), 'YYYY-MM') as "Месяц",
    count(*) as "Количество эпизодов",
    sum(coalesce(nullif(days_count, '')::numeric, 0)) as "Сумма дней",
    round(avg(nullif(days_count, '')::numeric), 2) as "Среднее дней",
    count(distinct snils) as "Уникальных пациентов"
from load_data_sick_leave_sheets
where to_date(issue_date::text, 'YYYY-MM-DD')
      between to_date(CAST(:start_date AS text), 'YYYY-MM-DD')
          and to_date(CAST(:end_date AS text), 'YYYY-MM-DD')
      and duplicate = 'нет'
      and ( :tvsp_all OR tvsp = ANY(:tvsp) )
      and ( :first_all OR "first" = ANY(:first_list) )
      and ( :reason_all OR coalesce(incapacity_reason_code, 'По уходу') = ANY(:reason_list) )
group by 1
order by 1 desc;
"""

