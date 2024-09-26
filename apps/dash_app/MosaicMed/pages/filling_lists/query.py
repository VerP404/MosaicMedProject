sql_query_df_from_sql = """
with nas as (
    select people_data."FIO",
           people_data."DR",
           people_data."ENP",
           people_data."LPUUCH",
           area_data."Корпус"
    from iszl.people_data left join info.area_data on people_data."LPUUCH"=area_data."Участок"

),
    pepl as (
        select  naselenie_data."Фамилия",
                naselenie_data."Имя",
                naselenie_data."Отчество",
                naselenie_data."Дата рождения",
                naselenie_data."Пол",
                naselenie_data."ЕНП",
                COALESCE(nas."LPUUCH", 'не прикреплен') AS "Участок",
                COALESCE(nas."Корпус", 'не прикреплен') AS "Корпус",
                naselenie_data."Телефон Квазар",
                naselenie_data."Телефон МИС КАУЗ",
                naselenie_data."Адрес Квазар",
                naselenie_data."Адрес МИС КАУЗ 1" as "Адрес МИС КАУЗ",
                naselenie_data."Адрес ИСЗЛ"

        from info.naselenie_data left join nas on naselenie_data."ЕНП" =  nas."ENP"
    )
SELECT * FROM pepl
"""