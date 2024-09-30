import pandas as pd
from sqlalchemy import text
from database.db_conn import engine
from services.MosaicMed.app import app
import dash_bootstrap_components as dbc
from dash import html, dash_table, dcc, Output, Input, exceptions, callback_context


# Получаем список диагнозов приказа 168н
def list_for_iszl(eng):
    with eng.connect() as conn:
        sql_query = """
            with people_uch_is_null as (select iszl.people_data.*,
                                               EXTRACT(YEAR FROM CURRENT_DATE) - CAST(substring("DR" FROM LENGTH("DR") - 3) AS integer) as "Возраст"
                                        from iszl.people_data
                                                 left join info.area_data on iszl.people_data."LPUUCH" = area_data."Участок"
                                        where "Корпус" is null)
            select "PID",
                   "FIO",
                   "DR",
                   "SMO",
                   '`'||"ENP" as "ENP",
                   "LPU",
                   CASE WHEN "Возраст" < 18 THEN '`14804383159' ELSE '`14804383159' END as "SS_DOCTOR",
                   CASE WHEN "Возраст" < 18 THEN '111_360026' ELSE '111_360025' END as "LPUUCH",
                   "Upd",
                   "CLOSED"
            from people_uch_is_null
        """
        query = text(sql_query)
        result = conn.execute(query)
        columns = [desc[0] for desc in result.cursor.description]
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=columns)


df = list_for_iszl(engine)
alert_text1 = """выгружаем файл и подгружаем csv в ИСЗЛ (Прикрепление к МО ВО - Экспорт/Импорт)
"""
type_page = 'people_iszl_tab2'

tab2_layout_people_iszl = html.Div(
    [
        dbc.Alert(dcc.Markdown(alert_text1), color="danger", style={'padding': '0 0 0 10px'}),
        dash_table.DataTable(id=f'table-{type_page}',
                             columns=[{'name': col, 'id': col} for col in df.columns],
                             data=df.to_dict('records'),
                             editable=True,
                             filter_action="native",
                             sort_action="native",
                             sort_mode='multi',
                             ),
        html.Button("Download CSV", id=f"download-btn-{type_page}"),
        dcc.Download(id=f"download-csv-{type_page}")
    ]
)


@app.callback(
    Output(f"download-csv-{type_page}", "data"),
    Input(f"download-btn-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def update_csv(n_clicks):
    if n_clicks is None:
        return [], [], html.Div(), html.Div()
    # Получить контекст вызова
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == f"download-btn-{type_page}":
        # Преобразование данных в DataFrame
        df_export = pd.DataFrame(df.to_dict('records'))

        # Создание строки CSV
        csv_string = df_export.to_csv(sep=';', index=False)

        # Подготовка данных для скачивания
        return dict(content=csv_string, filename="exported_data.csv")

