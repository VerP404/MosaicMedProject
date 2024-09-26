import pandas as pd
from sqlalchemy import text
import dash_bootstrap_components as dbc
from database.db_conn import engine
from dash import html, dash_table

from services.MosaicMed.pages.economic_reports.volumes_indicators.query import sql_query_pgg_amb, sql_query_pgg_dd, sql_query_pgg_ds


def pgg_amb(eng, sql_query):
    with eng.connect() as conn:
        query = text(sql_query)
        result = conn.execute(query)
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=columns)


df_amb = pgg_amb(engine, sql_query_pgg_amb)
df_dd = pgg_amb(engine, sql_query_pgg_dd)
df_ds = pgg_amb(engine, sql_query_pgg_ds)

app_pgg_amb = html.Div(
    [
        dbc.Alert("Объемные показатели помесячно по оплаченным", color="info"),
        dbc.Alert("Амбулаторная помощь", color="primary"),
        dash_table.DataTable(id='table1',
                             columns=[{'name': col, 'id': col} for col in df_amb.columns],
                             data=df_amb.to_dict('records'),
                             export_format='xlsx',
                             export_headers='display',
                             editable=True,
                             filter_action="native",
                             sort_action="native",
                             sort_mode='multi',
                             ),
        dbc.Alert("Диспансеризация", color="primary"),
        dash_table.DataTable(id='table2',
                             columns=[{'name': col, 'id': col} for col in df_dd.columns],
                             data=df_dd.to_dict('records'),
                             export_format='xlsx',
                             export_headers='display',
                             editable=True,
                             filter_action="native",
                             sort_action="native",
                             sort_mode='multi',
                             ),
        dbc.Alert("Стационарозамещающая помощь", color="primary"),
        dash_table.DataTable(id='table3',
                             columns=[{'name': col, 'id': col} for col in df_ds.columns],  # Определение столбцов таблицы
                             data=df_ds.to_dict('records'),
                             export_format='xlsx',
                             export_headers='display',
                             editable=True,
                             filter_action="native",
                             sort_action="native",
                             sort_mode='multi',
                             )
    ]
)
