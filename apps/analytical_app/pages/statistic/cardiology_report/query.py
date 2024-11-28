sql_query_cardiology_report = """
with talon as (select * 
from data_loader_omsdata
where goal = '30' 
    and to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY'))

select *
from
(select '1. Зарегистрировано больных с заболеваниями всего' as Показатель,
       count(*) as "К-во"
from talon


union all


select '1.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
union all
select '1.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab


union all


select '2. Зарегистрировано больных с болезнями системы кровообращения (I00-I99) всего' as Показатель,
       count(*)
from talon
where main_diagnosis like 'I%'
union all
select '2.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
    and main_diagnosis like 'I%'
union all
select '2.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab
where DS like 'I%'


union all


select '3. Зарегистрировано больных с АГ (I10-I13) всего' as Показатель,
       count(*)
from talon
where main_diagnosis like ANY (array ['I10%', 'I11%', 'I12%', 'I13%'])
union all
select '3.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
    and main_diagnosis like ANY (array ['I10%', 'I11%', 'I12%', 'I13%'])
union all
select '3.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab
where DS like ANY (array ['I10%', 'I11%', 'I12%', 'I13%'])


union all

select '4. Зарегистрировано больных с ИБС (I20-I25) всего' as Показатель,
       count(*)
from talon
where  main_diagnosis like ANY (array ['I20%', 'I21%', 'I22%', 'I23%', 'I24%', 'I25%'])
union all
select '4.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
    and main_diagnosis like ANY (array ['I20%', 'I21%', 'I22%', 'I23%', 'I24%', 'I25%'])
union all
select '4.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab
where DS like ANY (array ['I20%', 'I21%', 'I22%', 'I23%', 'I24%', 'I25%'])


union all


select '5. Зарегистрировано больных с нестаб. стенокардией (I20.0) всего' as Показатель,
       count(*)
from talon
where main_diagnosis like 'I20.0%'
union all
select '5.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
    and main_diagnosis like 'I20.0%'
union all
select '5.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab
where DS  like 'I20.0%'


union all


select '6. Зарегистрировано больных с ОИМ (I21-I22) всего' as Показатель,
       count(*)
from talon
where  main_diagnosis like ANY (array ['I21%', 'I22%'])
union all
select '6.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
    and main_diagnosis like ANY (array ['I21%', 'I22%'])
union all
select '6.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab
where DS like ANY (array ['I21%', 'I22%'])


union all


select '7. Зарегистрировано больных с постинфарктным кардиосклерозом (I25.8) всего' as Показатель,
       count(*)
from talon
where main_diagnosis like 'I25.8%'
union all
select '7.1 в том числе с диагнозом, установленным впервые в жизни',
       count(*)
from talon
where main_disease_character = '2'
    and main_diagnosis like 'I25.8%'
union all
select '7.2 Под диспансерным наблюдением',
       COUNT(DISTINCT ldwID)
from data_loader_iszldisnab
where DS  like 'I25.8%'
) as data
order by Показатель
"""