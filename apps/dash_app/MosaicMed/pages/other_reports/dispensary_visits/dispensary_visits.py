import pandas as pd
from sqlalchemy import text
import dash_bootstrap_components as dbc
from database.db_conn import engine
from dash import html, dash_table, dcc


# Получаем список диагнозов приказа 168н
def uniq_dd_visit(eng):
    with eng.connect() as conn:
        sql_query = """
            select distinct "ЕНП",
                            case when "Цель" = 'ДВ4' then 'Д' else 'П' end as "Тип",
                            case
                                when TO_DATE("Окончание лечения", 'DD-MM-YYYY') - TO_DATE("Начало лечения", 'DD-MM-YYYY') = 0
                                    then '1'
                                when TO_DATE("Окончание лечения", 'DD-MM-YYYY') - TO_DATE("Начало лечения", 'DD-MM-YYYY') in
                                     (1, 2, 3) then '2'
                                else '3' end                               as "Посещения",
                        SUBSTRING("Окончание лечения", 4, 2) AS "Месяц",
                            "Подразделение"
            from oms.oms_data
            where "Цель" in ('ДВ4', 'ОПВ') and "ЕНП" not like '0%' and "ЕНП" not like '%0'
            order by "Подразделение"
        """
        query = text(sql_query)
        result = conn.execute(query)
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=columns)


df = uniq_dd_visit(engine)
alert_text1 = """Условия:
- Если дата начала лечения и дата окончания лечения равны, то 1.
- Если между датами начала лечения и дата окончания лечения 3 дня, то 2.
- Если между датами начала лечения и дата окончания лечения больше 3х дней, то 3.
"""
alert_text2 = """Тип:
- П - Профосмотр взрослых ОПВ
- Д - Диспансеризация взрослых ДВ4

Для копирования в гугл таблицу убраны ЕНП у которых в начале или в конце 0.  
Чтобы отфильтровать данные введите в поле ***filter data*** требуемого столбца нужные данные:  
- Месяц - 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12.
- Подразделение - ГП №3, ГП №11, ОАПП №1, ОАПП №2.
"""
app_other_dd_visits = html.Div(
    [
        dbc.Alert(dcc.Markdown(alert_text1), color="danger", style={'padding': '0 0 0 10px'}),
        dbc.Alert(dcc.Markdown(alert_text2), color="warning", style={'padding': '0 0 0 10px'}),
        dbc.Alert("ЕНП, Тип, количество посещений пациентов в рамках ДВ4 и ОПВ", color="primary"),
        dash_table.DataTable(id='table1',
                             columns=[{'name': col, 'id': col} for col in df.columns],
                             data=df.to_dict('records'),
                             export_format='xlsx',
                             export_headers='display',
                             editable=True,
                             filter_action="native",
                             sort_action="native",
                             sort_mode='multi',
                             )
    ]
)
