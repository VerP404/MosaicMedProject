import pandas as pd
from sqlalchemy import text
from database.db_conn import engine
import dash_bootstrap_components as dbc
from dash import html, dash_table, dcc


# Получаем список диагнозов приказа 168н
def list_for_check(eng):
    with eng.connect() as conn:
        sql_query = """
            with nas as (select
            "FIO" as "ФИО",
            "DR" as "ДР",
            EXTRACT(YEAR FROM CURRENT_DATE) - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст",
            case when EXTRACT(YEAR FROM CURRENT_DATE) - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) <18 then 'дети'
            else 'взрослые' end as "Категория",
            "ENP" as "ЕНП_",
            "SMO" as "СМО",
            "LPUUCH" as "Временный участок"
            from iszl.people_data
            where "LPUUCH" in ('111_360025', '111_360026')
            order by "ФИО"),
                pep as (select *
                        from nas left join info.naselenie_data on nas."ЕНП_" = info.naselenie_data."ЕНП")
            
            select "ФИО",
                   "ДР",
                   "Возраст",
                   "Категория",
                   "ЕНП_",
                   "Временный участок",
                   "Адрес Квазар",
                   "Адрес МИС КАУЗ 1",
                   "Адрес МИС КАУЗ 2",
                   "Адрес ИСЗЛ"
            from pep
        """
        query = text(sql_query)
        result = conn.execute(query)
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=columns)


df = list_for_check(engine)
alert_text1 = """Список пациентов для простановки корректного участка
"""
type_page = 'people_iszl_tab3'

tab3_layout_people_iszl = html.Div(
    [
        dbc.Alert(dcc.Markdown(alert_text1), color="danger", style={'padding': '0 0 0 10px'}),
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

