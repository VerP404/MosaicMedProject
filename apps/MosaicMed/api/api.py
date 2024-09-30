from flask import Flask, jsonify, request
import psycopg2
import json
import socket

app = Flask(__name__)


@app.route('/', methods=['GET'])
def api_talon():
    year = request.args.get('year')
    month = request.args.get('month')
    # Установить соединение с базой данных
    if socket.gethostname() == 'KAB220':
        db_url = "dbname=it_VGP3 user=postgres password=Qaz123 host=localhost"
    elif socket.gethostname() == 'SRV-main02':
        db_url = "dbname=it_VGP3 user=postgres password=440856Mo host=localhost"
    else:
        print('Подключение к базе данных не установлено. Проверьте правильность данных')
        exit()

    conn = psycopg2.connect(db_url)
    # Создать курсор для выполнения операций с базой данных
    cur = conn.cursor()
    rep_month_01, rep_month_02, rep_month_03, rep_month_04, rep_month_05, rep_month_06, rep_month_07, rep_month_08, \
        rep_month_09, rep_month_10, rep_month_11, rep_month_12 = '', '', '', '', '', '', '', '', '', '', '', '',
    text_in_query = "or \"Номер счёта\" is null"
    match month:
        case '01':
            rep_month_01 = text_in_query
        case '02':
            rep_month_02 = text_in_query
        case '03':
            rep_month_03 = text_in_query
        case '04':
            rep_month_04 = text_in_query
        case '05':
            rep_month_05 = text_in_query
        case '06':
            rep_month_06 = text_in_query
        case '07':
            rep_month_07 = text_in_query
        case '08':
            rep_month_08 = text_in_query
        case '09':
            rep_month_09 = text_in_query
        case '10':
            rep_month_10 = text_in_query
        case '11':
            rep_month_11 = text_in_query
        case '12':
            rep_month_12 = text_in_query
    sql_query_amb = f"""    
    with data as (select *,
                         case
                             when "Цель" in ('1', '5', '7', '9', '10', '14', '140', '640') then 'Посещения'
                             when "Цель" in ('30', '301', '305') then 'Обращения'
                             when "Цель" in ('22') then 'Неотложка'
                             else 'прочие'
                             end as Группа
                  from oms_data
                  where "Цель" in ('1', '5', '7', '9', '10', '14', '140', '640', '30', '301', '305', '22') 
                    and "Тариф" != '0'
                    AND "Санкции" is null
                    and "Код СМО" like '360%'),

         plan_data as (select "Корпус",
                              "Тип",
                              "Январь"  as январь_план,
                              "Февраль" as февраль_план,
                              "Март" as март_план,
                              "Апрель" as апрель_план,
                              "Май" as май_план,
                              "Июнь" as июнь_план,
                              "Июль" as июль_план,
                              "Август" as август_план,
                              "Сентябрь" as сентябрь_план,
                              "Октябрь" as октябрь_план,
                              "Ноябрь" as ноябрь_план,
                              "Декабрь" as декабрь_план

                       from plan
                       where "Цель" = 'амбулаторка'
                         and год = 2024),

        fact_data as (select 'Амбулаторка',
                            Группа,
                           "Подразделение",
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as год_выставлено,
                           sum(case when "Статус" in ('3') then 1 else 0 end) as год_оплачено,
                           sum(case when "Статус" in ('5', '7', '12') then 1 else 0 end) as год_отказано,
                           sum(case when "Статус" in ('0', '13', '17') then 1 else 0 end) as год_отменено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then 1 else 0 end) as январь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then 1 else 0 end) as январь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then 1 else 0 end) as февраль_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then 1 else 0 end) as  февраль_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then 1 else 0 end) as март_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then 1 else 0 end) as  март_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then 1 else 0 end) as апрель_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then 1 else 0 end) as  апрель_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then 1 else 0 end) as май_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then 1 else 0 end) as  май_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then 1 else 0 end) as июнь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then 1 else 0 end) as  июнь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then 1 else 0 end) as июль_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then 1 else 0 end) as  июль_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then 1 else 0 end) as август_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then 1 else 0 end) as  август_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then 1 else 0 end) as сентябрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then 1 else 0 end) as  сентябрь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then 1 else 0 end) as октябрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then 1 else 0 end) as  октябрь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then 1 else 0 end) as ноябрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then 1 else 0 end) as  ноябрь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then 1 else 0 end) as декабрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then 1 else 0 end) as  декабрь_оплачено
                    from data
                    group by "Подразделение", Группа
                    order by Группа)
    select fact_data.*,
           plan_data.январь_план,
           plan_data.февраль_план,
           plan_data.март_план,
           plan_data.апрель_план,
           plan_data.май_план,
           plan_data.июнь_план,
           plan_data.июль_план,
           plan_data.август_план,
           plan_data.сентябрь_план,
           plan_data.октябрь_план,
           plan_data.ноябрь_план,
           plan_data.декабрь_план
    from fact_data
             left join plan_data on fact_data."Подразделение" = plan_data."Корпус" and fact_data.Группа = plan_data."Тип";
        """
    sql_query_disp_adult = f"""    
       with data as (select *,
                            case
                                when "Цель" = 'ДВ4' then 'ДВ4'
                                when "Цель" = 'ДВ2' then 'ДВ2'
                                when "Цель" = 'ОПВ' then 'ОПВ'
                                when "Цель" = 'УД1' then 'УД1'
                                when "Цель" = 'УД2' then 'УД2'
                                else 'прочие'
                                end as Группа
                     from oms_data
                     where "Цель" in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2') 
                       and "Подразделение" not like 'ДП%'
                       and "Тариф" != '0'
                    AND "Санкции" is null
                    and "Код СМО" like '360%'),

            plan_data as (select "Корпус",
                                 "Тип",
                                 "Январь"  as январь_план,
                                 "Февраль" as февраль_план,
                                 "Март" as март_план,
                                 "Апрель" as апрель_план,
                                 "Май" as май_план,
                                 "Июнь" as июнь_план,
                                 "Июль" as июль_план,
                                 "Август" as август_план,
                                 "Сентябрь" as сентябрь_план,
                                 "Октябрь" as октябрь_план,
                                 "Ноябрь" as ноябрь_план,
                                 "Декабрь" as декабрь_план

                          from plan
                          where "Цель" = 'Диспансеризация взрослых'
                            and год = 2024),

           fact_data as (select 'Диспансеризация взрослых',
                               Группа,
                              "Подразделение",
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as год_выставлено,
                              sum(case when "Статус" in ('3') then 1 else 0 end) as год_оплачено,
                              sum(case when "Статус" in ('5', '7', '12') then 1 else 0 end) as год_отказано,
                              sum(case when "Статус" in ('0', '13', '17') then 1 else 0 end) as год_отменено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then 1 else 0 end) as январь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then 1 else 0 end) as январь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then 1 else 0 end) as февраль_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then 1 else 0 end) as  февраль_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then 1 else 0 end) as март_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then 1 else 0 end) as  март_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then 1 else 0 end) as апрель_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then 1 else 0 end) as  апрель_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then 1 else 0 end) as май_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then 1 else 0 end) as  май_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then 1 else 0 end) as июнь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then 1 else 0 end) as  июнь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then 1 else 0 end) as июль_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then 1 else 0 end) as  июль_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then 1 else 0 end) as август_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then 1 else 0 end) as  август_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then 1 else 0 end) as сентябрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then 1 else 0 end) as  сентябрь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then 1 else 0 end) as октябрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then 1 else 0 end) as  октябрь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then 1 else 0 end) as ноябрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then 1 else 0 end) as  ноябрь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then 1 else 0 end) as декабрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then 1 else 0 end) as  декабрь_оплачено
                       from data
                       group by "Подразделение", Группа
                       order by Группа)
       select fact_data.*,
              plan_data.январь_план,
              plan_data.февраль_план,
              plan_data.март_план,
              plan_data.апрель_план,
              plan_data.май_план,
              plan_data.июнь_план,
              plan_data.июль_план,
              plan_data.август_план,
              plan_data.сентябрь_план,
              plan_data.октябрь_план,
              plan_data.ноябрь_план,
              plan_data.декабрь_план
       from fact_data
                left join plan_data on fact_data."Подразделение" = plan_data."Корпус" and fact_data.Группа = plan_data."Тип";


       ;
           """
    sql_query_disp_children = f"""    
       with data as (select *,
                            case
                                when "Цель" = 'ПН1' then 'ПН1'
                                when "Цель" = 'ДС2' then 'ДС2'
                                else 'прочие'
                                end as Группа
                     from oms_data
                     where "Цель" in ('ПН1', 'ДС2') 
                     and "Подразделение" like 'ДП%'
                       and "Тариф" != '0'
                    AND "Санкции" is null
                    and "Код СМО" like '360%'),

            plan_data as (select "Корпус",
                                 "Тип",
                                 "Январь"  as январь_план,
                                 "Февраль" as февраль_план,
                                 "Март" as март_план,
                                 "Апрель" as апрель_план,
                                 "Май" as май_план,
                                 "Июнь" as июнь_план,
                                 "Июль" as июль_план,
                                 "Август" as август_план,
                                 "Сентябрь" as сентябрь_план,
                                 "Октябрь" as октябрь_план,
                                 "Ноябрь" as ноябрь_план,
                                 "Декабрь" as декабрь_план

                          from plan
                          where "Цель" = 'Диспансеризация детей'
                            and год = 2024),

           fact_data as (select 'Диспансеризация детей',
                               Группа,
                              "Подразделение",
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as год_выставлено,
                              sum(case when "Статус" in ('3') then 1 else 0 end) as год_оплачено,
                              sum(case when "Статус" in ('5', '7', '12') then 1 else 0 end) as год_отказано,
                              sum(case when "Статус" in ('0', '13', '17') then 1 else 0 end) as год_отменено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then 1 else 0 end) as январь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then 1 else 0 end) as январь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then 1 else 0 end) as февраль_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then 1 else 0 end) as  февраль_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then 1 else 0 end) as март_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then 1 else 0 end) as  март_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then 1 else 0 end) as апрель_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then 1 else 0 end) as  апрель_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then 1 else 0 end) as май_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then 1 else 0 end) as  май_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then 1 else 0 end) as июнь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then 1 else 0 end) as  июнь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then 1 else 0 end) as июль_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then 1 else 0 end) as  июль_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then 1 else 0 end) as август_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then 1 else 0 end) as  август_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then 1 else 0 end) as сентябрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then 1 else 0 end) as  сентябрь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then 1 else 0 end) as октябрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then 1 else 0 end) as  октябрь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then 1 else 0 end) as ноябрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then 1 else 0 end) as  ноябрь_оплачено,
                              sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then 1 else 0 end) as декабрь_выставлено,
                              sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then 1 else 0 end) as  декабрь_оплачено
                       from data
                       group by "Подразделение", Группа
                       order by Группа)
       select fact_data.*,
              plan_data.январь_план,
              plan_data.февраль_план,
              plan_data.март_план,
              plan_data.апрель_план,
              plan_data.май_план,
              plan_data.июнь_план,
              plan_data.июль_план,
              plan_data.август_план,
              plan_data.сентябрь_план,
              plan_data.октябрь_план,
              plan_data.ноябрь_план,
              plan_data.декабрь_план
       from fact_data
                left join plan_data on fact_data."Подразделение" = plan_data."Корпус" and fact_data.Группа = plan_data."Тип";


       ;
           """
    sql_query_cel3 = f"""    
with data as (select *,
                     case
                         when "Диагноз основной (DS1)" like 'I%' then 'БСК'
                         when "Диагноз основной (DS1)" like 'C%' then 'Онкология'
                         when "Диагноз основной (DS1)" like 'E11%' then 'СД'
                         else 'прочие'
                         end as Группа
              from oms_data
              where "Цель" = '3'
                and "Тариф" != '0'
                    AND "Санкции" is null
                    and "Код СМО" like '360%'
                and "Подразделение" not like '%ДП%'),

     plan_data as (select "Корпус",
                          "Тип",
                          "Январь"  as январь_план,
                          "Февраль" as февраль_план,
                          "Март" as март_план,
                          "Апрель" as апрель_план,
                          "Май" as май_план,
                          "Июнь" as июнь_план,
                          "Июль" as июль_план,
                          "Август" as август_план,
                          "Сентябрь" as сентябрь_план,
                          "Октябрь" as октябрь_план,
                          "Ноябрь" as ноябрь_план,
                          "Декабрь" as декабрь_план

                   from plan
                   where "Цель" = 'Диспансерное наблюдение'
                     and год = 2024),

    fact_data as (select 'Диспансерное наблюдение',
                        Группа,
                       "Подразделение",
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as год_выставлено,
                       sum(case when "Статус" in ('3') then 1 else 0 end) as год_оплачено,
                       sum(case when "Статус" in ('5', '7', '12') then 1 else 0 end) as год_отказано,
                       sum(case when "Статус" in ('0', '13', '17') then 1 else 0 end) as год_отменено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then 1 else 0 end) as январь_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then 1 else 0 end) as январь_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then 1 else 0 end) as февраль_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then 1 else 0 end) as  февраль_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then 1 else 0 end) as март_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then 1 else 0 end) as  март_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then 1 else 0 end) as апрель_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then 1 else 0 end) as  апрель_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then 1 else 0 end) as май_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then 1 else 0 end) as  май_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then 1 else 0 end) as июнь_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then 1 else 0 end) as  июнь_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then 1 else 0 end) as июль_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then 1 else 0 end) as  июль_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then 1 else 0 end) as август_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then 1 else 0 end) as  август_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then 1 else 0 end) as сентябрь_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then 1 else 0 end) as  сентябрь_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then 1 else 0 end) as октябрь_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then 1 else 0 end) as  октябрь_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then 1 else 0 end) as ноябрь_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then 1 else 0 end) as  ноябрь_оплачено,
                       sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then 1 else 0 end) as декабрь_выставлено,
                       sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then 1 else 0 end) as  декабрь_оплачено
                from data
                group by "Подразделение", Группа
                order by Группа)
select fact_data.*,
       plan_data.январь_план,
       plan_data.февраль_план,
       plan_data.март_план,
       plan_data.апрель_план,
       plan_data.май_план,
       plan_data.июнь_план,
       plan_data.июль_план,
       plan_data.август_план,
       plan_data.сентябрь_план,
       plan_data.октябрь_план,
       plan_data.ноябрь_план,
       plan_data.декабрь_план
from fact_data
         left join plan_data on fact_data."Подразделение" = plan_data."Корпус" and fact_data.Группа = plan_data."Тип";


;
    """
    sql_query_stac = f"""

    with data as (select *,
                         "Цель" as Группа,
                            CASE
                                WHEN "Подразделение" = 'ГП №3' THEN "Подразделение"
                                WHEN "Подразделение" = 'ОАПП №1' THEN "Подразделение"
                                WHEN "Подразделение" = 'ГП №11' and "Врач (Профиль МП)" not in ('136 акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)') 
                                        and "Врач" not in ('11112018 Шадрин Илья Сергеевич') THEN "Подразделение"
                                WHEN "Подразделение" = 'ОАПП №2' THEN "Подразделение"
                                WHEN "Подразделение" = 'ДП №1' THEN "Подразделение"
                                WHEN "Подразделение" LIKE 'ДП №8%' THEN "Подразделение"
                                WHEN "Подразделение" = 'ГП №11' and "Врач" in ('11136001 Сорокина Татьяна Валентиновна', 
                                                                               '11136005 Карандеев Максим Анатольевич', 
                                                                               '11112018 Шадрин Илья Сергеевич') THEN 'ЦАХ'
                                WHEN "Подразделение" = 'ГП №11' and "Врач" in ('11136007 Столярова Тамара Владимировна', 
                                                                               '11136014 Войтко Валерия Александровна') THEN 'Гинекология'
                                ELSE '-'
                            END AS "Корпус",
                             "Врач"
                  from oms_data
                  where "Цель" in ('В дневном стационаре', 'На дому')
                    and "Тариф" != '0'
                    AND "Санкции" is null
                    and "Код СМО" like '360%'),

         plan_data as (select "Корпус",
                              "Тип",
                              "Январь"  as январь_план,
                              "Февраль" as февраль_план,
                              "Март" as март_план,
                              "Апрель" as апрель_план,
                              "Май" as май_план,
                              "Июнь" as июнь_план,
                              "Июль" as июль_план,
                              "Август" as август_план,
                              "Сентябрь" as сентябрь_план,
                              "Октябрь" as октябрь_план,
                              "Ноябрь" as ноябрь_план,
                              "Декабрь" as декабрь_план

                       from plan
                       where "Цель" = 'стационар'
                         and год = 2024),

        fact_data as (select 'Стационар',
                            Группа,
                           data."Корпус",
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as год_выставлено,
                           sum(case when "Статус" in ('3') then 1 else 0 end) as год_оплачено,
                           sum(case when "Статус" in ('5', '7', '12') then 1 else 0 end) as год_отказано,
                           sum(case when "Статус" in ('0', '13', '17') then 1 else 0 end) as год_отменено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then 1 else 0 end) as январь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then 1 else 0 end) as январь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then 1 else 0 end) as февраль_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then 1 else 0 end) as  февраль_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then 1 else 0 end) as март_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then 1 else 0 end) as  март_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then 1 else 0 end) as апрель_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then 1 else 0 end) as  апрель_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then 1 else 0 end) as май_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then 1 else 0 end) as  май_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then 1 else 0 end) as июнь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then 1 else 0 end) as  июнь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then 1 else 0 end) as июль_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then 1 else 0 end) as  июль_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then 1 else 0 end) as август_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then 1 else 0 end) as  август_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then 1 else 0 end) as сентябрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then 1 else 0 end) as  сентябрь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then 1 else 0 end) as октябрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then 1 else 0 end) as  октябрь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then 1 else 0 end) as ноябрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then 1 else 0 end) as  ноябрь_оплачено,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then 1 else 0 end) as декабрь_выставлено,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then 1 else 0 end) as  декабрь_оплачено
                    from data
                    group by "Корпус", Группа
                    order by Группа)
    select fact_data.*,
           plan_data.январь_план,
           plan_data.февраль_план,
           plan_data.март_план,
           plan_data.апрель_план,
           plan_data.май_план,
           plan_data.июнь_план,
           plan_data.июль_план,
           plan_data.август_план,
           plan_data.сентябрь_план,
           plan_data.октябрь_план,
           plan_data.ноябрь_план,
           plan_data.декабрь_план
    from fact_data
             left join plan_data on fact_data."Корпус" = plan_data."Корпус" and fact_data.Группа = plan_data."Тип"
            """

    # SQL запрос для извлечения данных
    cur.execute(sql_query_cel3)
    rows_cel3 = cur.fetchall()

    cur.execute(sql_query_disp_adult)
    rows_disp_adult = cur.fetchall()

    cur.execute(sql_query_disp_children)
    rows_disp_children = cur.fetchall()

    cur.execute(sql_query_stac)
    rows_stac = cur.fetchall()

    cur.execute(sql_query_amb)
    rows_amb = cur.fetchall()

    # Преобразовать результаты в JSON
    column_names = [
        'Цель',
        'Группа',
        'Подразделение',
        'year_exposed',
        'год_оплачено',
        'год_отказано',
        'год_отменено',
        'январь_выставлено',
        'январь_оплачено',
        'февраль_выставлено',
        'февраль_оплачено',
        'март_выставлено',
        'март_оплачено',
        'апрель_выставлено',
        'апрель_оплачено',
        'май_выставлено',
        'май_оплачено',
        'июнь_выставлено',
        'июнь_оплачено',
        'июль_выставлено',
        'июль_оплачено',
        'август_выставлено',
        'август_оплачено',
        'сентябрь_выставлено',
        'сентябрь_оплачено',
        'октябрь_выставлено',
        'октябрь_оплачено',
        'ноябрь_выставлено',
        'ноябрь_оплачено',
        'декабрь_выставлено',
        'декабрь_оплачено',
        'январь_план',
        'февраль_план',
        'март_план',
        'апрель_план',
        'май_план',
        'июнь_план',
        'июль_план',
        'август_план',
        'сентябрь_план',
        'октябрь_план',
        'ноябрь_план',
        'декабрь_план'
    ]

    data_disp_adult = [
        dict(zip(column_names, row))
        for row in rows_disp_adult
    ]
    data_disp_children = [
        dict(zip(column_names, row))
        for row in rows_disp_children
    ]
    data_amb = [
        dict(zip(column_names, row))
        for row in rows_amb
    ]
    data_cel3 = [
        dict(zip(column_names, row))
        for row in rows_cel3
    ]
    data_stac = [
        dict(zip(column_names, row))
        for row in rows_stac
    ]
    # Закрыть соединение
    cur.close()
    conn.close()
    template_data = data_cel3 + data_stac + data_amb + data_disp_adult + data_disp_children
    json_data = json.dumps(template_data, ensure_ascii=False)
    return json_data


@app.route('/finance/', methods=['GET'])
def api_finance():
    year = request.args.get('year')
    month = request.args.get('month')
    # Установить соединение с базой данных
    if socket.gethostname() == 'KAB220':
        db_url = "dbname=it_VGP3 user=postgres password=Qaz123 host=localhost"
    elif socket.gethostname() == 'SRV-main02':
        db_url = "dbname=it_VGP3 user=postgres password=440856Mo host=localhost"
    else:
        print('Подключение к базе данных не установлено. Проверьте правильность данных')
        exit()

    conn = psycopg2.connect(db_url)
    # Создать курсор для выполнения операций с базой данных
    cur = conn.cursor()
    rep_month_01, rep_month_02, rep_month_03, rep_month_04, rep_month_05, rep_month_06, rep_month_07, rep_month_08, \
        rep_month_09, rep_month_10, rep_month_11, rep_month_12 = '', '', '', '', '', '', '', '', '', '', '', '',
    text_in_query = "or \"Номер счёта\" is null"
    match month:
        case '01':
            rep_month_01 = text_in_query
        case '02':
            rep_month_02 = text_in_query
        case '03':
            rep_month_03 = text_in_query
        case '04':
            rep_month_04 = text_in_query
        case '05':
            rep_month_05 = text_in_query
        case '06':
            rep_month_06 = text_in_query
        case '07':
            rep_month_07 = text_in_query
        case '08':
            rep_month_08 = text_in_query
        case '09':
            rep_month_09 = text_in_query
        case '10':
            rep_month_10 = text_in_query
        case '11':
            rep_month_11 = text_in_query
        case '12':
            rep_month_12 = text_in_query

    sql_query_dn = f"""
with data as (select *,
                     case
                         when "Врач (Профиль МП)" =
                              '136 акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)'
                             then 'акушерство-гинекология'
                         when "Врач (Профиль МП)" = '29 кардиологии' then 'кардиология'
                         when "Врач (Профиль МП)" in ('97 терапии', '57 общей врачебной практике (семейной медицине)')
                             then 'терапия и воп'
                         when "Врач (Профиль МП)" = '60 онкологии' and "Диагноз основной (DS1)" like ('C44%')
                             then 'дн-1-онко(С44)'
                         when "Врач (Профиль МП)" = '60 онкологии' and "Диагноз основной (DS1)" like ('C%') and
                              "Диагноз основной (DS1)" not like ('C44%') then 'дн-1-онко(С00-С99)'
                         when "Врач (Профиль МП)" = '60 онкологии' and "Диагноз основной (DS1)" like ('D%')
                             then 'дн-1-онко(D00-D99)'
                         when "Врач (Профиль МП)" = '122 эндокринологии' then 'эндокринология'
                         when "Врач (Профиль МП)" = '162 оториноларингологии (за исключением кохлеарной имплантации)'
                             then 'оториноларингология'
                         when "Врач (Профиль МП)" = '28 инфекционным болезням' then 'инфекционист'
                         when "Врач (Профиль МП)" = '53 неврологии' then 'неврология'
                         when "Врач (Профиль МП)" = '65 офтальмологии' then 'офтальмонология'
                         when "Врач (Профиль МП)" = '100 травматологии и ортопедии' then 'травматология-ортопедия'
                         when "Врач (Профиль МП)" = '108 урологии' then 'урология'
                         when "Врач (Профиль МП)" = '112 хирургии' then 'хирургия'
                         else 'прочие'
                         end as Группа
              from oms_data
              where "Цель" = '3'
                and "Тариф" != '0'
                    AND "Санкции" is null
                    and "Код СМО" like '360%'),

         plan_data as (select "Корпус",
                          "Тип",
                          "Январь_талон"    as январь_план_талон,
                          "Январь_финанс"   as январь_план_финанс,
                          "Февраль_талон"   as февраль_план_талон,
                          "Февраль_финанс"  as февраль_план_финанс,
                          "Март_талон"      as март_план_талон,
                          "Март_финанс"     as март_план_финанс,
                          "Апрель_талон"    as апрель_план_талон,
                          "Апрель_финанс"   as апрель_план_финанс,
                          "Май_талон"       as май_план_талон,
                          "Май_финанс"      as май_план_финанс,
                          "Июнь_талон"      as июнь_план_талон,
                          "Июнь_финанс"     as июнь_план_финанс,
                          "Июль_талон"      as июль_план_талон,
                          "Июль_финанс"     as июль_план_финанс,
                          "Август_талон"    as август_план_талон,
                          "Август_финанс"   as август_план_финанс,
                          "Сентябрь_талон"  as сентябрь_план_талон,
                          "Сентябрь_финанс" as сентябрь_план_финанс,
                          "Октябрь_талон"   as октябрь_план_талон,
                          "Октябрь_финанс"  as октябрь_план_финанс,
                          "Ноябрь_талон"    as ноябрь_план_талон,
                          "Ноябрь_финанс"   as ноябрь_план_финанс,
                          "Декабрь_талон"   as декабрь_план_талон,
                          "Декабрь_финанс"  as декабрь_план_финанс
                   from plan_finance
                   where "Группа" = 'Диспансерное наблюдение'
                     and "Год" = 2024),

        fact_data as (select 'Диспансерное наблюдение',
                          Группа,
                          'БУЗ',
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then 1 else 0 end) as год_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') then "Сумма"::numeric(20, 2) else 0 end)) :: text as год_выставлено_финанс,
                           sum(case when "Статус" in ('3') then 1 else 0 end) as год_оплачено,
                           (sum(case when "Статус" in ('3') then "Сумма"::numeric(20, 2) else 0 end)) :: text as год_оплачено_финанс,
                           sum(case when "Статус" in ('5', '7', '12') then 1 else 0 end) as год_отказано,
                           (sum(case when "Статус" in ('5', '7', '12') then "Сумма"::numeric(20, 2) else 0 end)) :: text as год_отказано_финанс,
                           sum(case when "Статус" in ('0', '13', '17') then 1 else 0 end) as год_отменено,
                           (sum(case when "Статус" in ('0', '13', '17') then "Сумма"::numeric(20, 2) else 0 end)) :: text as год_отменено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then 1 else 0 end) as январь_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/01/%' {rep_month_01}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as январь_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then 1 else 0 end) as январь_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/01/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as январь_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then 1 else 0 end) as февраль_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/02/%' {rep_month_02} ) then "Сумма"::numeric(20, 2) else 0 end)) :: text as февраль_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then 1 else 0 end) as  февраль_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/02/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  февраль_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then 1 else 0 end) as март_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/03/%' {rep_month_03}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as март_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then 1 else 0 end) as  март_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/03/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  март_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then 1 else 0 end) as апрель_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/04/%'{rep_month_04}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as апрель_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then 1 else 0 end) as  апрель_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/04/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  апрель_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then 1 else 0 end) as май_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/05/%'{rep_month_05}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as май_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then 1 else 0 end) as  май_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/05/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  май_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then 1 else 0 end) as июнь_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/06/%'{rep_month_06}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as июнь_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then 1 else 0 end) as  июнь_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/06/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  июнь_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then 1 else 0 end) as июль_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/07/%'{rep_month_07}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as июль_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then 1 else 0 end) as  июль_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/07/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  июль_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then 1 else 0 end) as август_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/08/%'{rep_month_08}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as август_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then 1 else 0 end) as  август_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/08/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  август_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then 1 else 0 end) as сентябрь_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/09/%'{rep_month_09}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as сентябрь_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then 1 else 0 end) as  сентябрь_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/09/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  сентябрь_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then 1 else 0 end) as октябрь_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/10/%'{rep_month_10}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as октябрь_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then 1 else 0 end) as  октябрь_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/10/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  октябрь_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then 1 else 0 end) as ноябрь_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/11/%'{rep_month_11}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as ноябрь_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then 1 else 0 end) as  ноябрь_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/11/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  ноябрь_оплачено_финанс,
                           sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then 1 else 0 end) as декабрь_выставлено,
                           (sum(case when "Статус" in ('1', '2', '3', '4', '6', '8') and ("Номер счёта" like '%/12/%'{rep_month_12}) then "Сумма"::numeric(20, 2) else 0 end)) :: text as декабрь_выставлено_финанс,
                           sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then 1 else 0 end) as  декабрь_оплачено,
                           (sum(case when "Статус" in ('3') and "Номер счёта" like '%/12/%' then "Сумма"::numeric(20, 2) else 0 end)) :: text as  декабрь_оплачено_финанс
                    from data
                    group by Группа
                    order by Группа)
select fact_data.*,
       plan_data.январь_план_талон,
       (plan_data.январь_план_финанс) :: text,
       plan_data.февраль_план_талон,
       (plan_data.февраль_план_финанс) :: text,
       plan_data.март_план_талон,
       (plan_data.март_план_финанс) :: text,
       plan_data.апрель_план_талон,
       (plan_data.апрель_план_финанс) :: text,
       plan_data.май_план_талон,
       (plan_data.май_план_финанс) :: text,
       plan_data.июнь_план_талон,
       (plan_data.июнь_план_финанс) :: text,
       plan_data.июль_план_талон,
       (plan_data.июль_план_финанс) :: text,
       plan_data.август_план_талон,
       (plan_data.август_план_финанс) :: text,
       plan_data.сентябрь_план_талон,
       (plan_data.сентябрь_план_финанс) :: text,
       plan_data.октябрь_план_талон,
       (plan_data.октябрь_план_финанс) :: text,
       plan_data.ноябрь_план_талон,
       (plan_data.ноябрь_план_финанс) :: text,
       plan_data.декабрь_план_талон,
       (plan_data.декабрь_план_финанс) :: text

from fact_data
         left join plan_data on fact_data.Группа = plan_data."Тип"
         """

    cur.execute(sql_query_dn)
    rows_dn = cur.fetchall()

    # Преобразовать результаты в JSON
    column_names = [
        'Цель',
        'Группа',
        'Подразделение',
        'year_exposed',
        'год_выставлено_финанс',
        'год_оплачено',
        'год_оплачено_финанс',
        'год_отказано',
        'год_отказано_финанс',
        'год_отменено',
        'год_отменено_финанс',
        'январь_выставлено',
        'январь_выставлено_финанс',
        'январь_оплачено',
        'январь_оплачено_финанс',
        'февраль_выставлено',
        'февраль_выставлено_финанс',
        'февраль_оплачено',
        'февраль_оплачено_финанс',
        'март_выставлено',
        'март_выставлено_финанс',
        'март_оплачено',
        'март_оплачено_финанс',
        'апрель_выставлено',
        'апрель_выставлено_финанс',
        'апрель_оплачено',
        'апрель_оплачено_финанс',
        'май_выставлено',
        'май_выставлено_финанс',
        'май_оплачено',
        'май_оплачено_финанс',
        'июнь_выставлено',
        'июнь_выставлено_финанс',
        'июнь_оплачено',
        'июнь_оплачено_финанс',
        'июль_выставлено',
        'июль_выставлено_финанс',
        'июль_оплачено',
        'июль_оплачено_финанс',
        'август_выставлено',
        'август_выставлено_финанс',
        'август_оплачено',
        'август_оплачено_финанс',
        'сентябрь_выставлено',
        'сентябрь_выставлено_финанс',
        'сентябрь_оплачено',
        'сентябрь_оплачено_финанс',
        'октябрь_выставлено',
        'октябрь_выставлено_финанс',
        'октябрь_оплачено',
        'октябрь_оплачено_финанс',
        'ноябрь_выставлено',
        'ноябрь_выставлено_финанс',
        'ноябрь_оплачено',
        'ноябрь_оплачено_финанс',
        'декабрь_выставлено',
        'декабрь_выставлено_финанс',
        'декабрь_оплачено',
        'декабрь_оплачено_финанс',
        'январь_план',
        'январь_план_финанс',
        'февраль_план',
        'февраль_план_финанс',
        'март_план',
        'март_план_финанс',
        'апрель_план',
        'апрель_план_финанс',
        'май_план',
        'май_план_финанс',
        'июнь_план',
        'июнь_план_финанс',
        'июль_план',
        'июль_план_финанс',
        'август_план',
        'август_план_финанс',
        'сентябрь_план',
        'сентябрь_план_финанс',
        'октябрь_план',
        'октябрь_план_финанс',
        'ноябрь_план',
        'ноябрь_план_финанс',
        'декабрь_план',
        'декабрь_план_финанс'
    ]

    rows_dn = [
        dict(zip(column_names, row))
        for row in rows_dn
    ]
    cur.close()
    conn.close()
    template_data = rows_dn
    json_data = json.dumps(template_data, ensure_ascii=False)
    return json_data


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=9001)
