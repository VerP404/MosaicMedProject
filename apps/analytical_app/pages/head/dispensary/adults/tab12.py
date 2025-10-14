from datetime import datetime
from dash import html, dcc, Output, Input, State, exceptions
import traceback
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.components.filters import filter_years, date_picker, update_buttons
from sqlalchemy import text
from apps.analytical_app.query_executor import engine
from apps.analytical_app.pages.head.dispensary.adults.query import sql_query_adults_appointments_not_passed


type_page = "tab12-da"


adults_dv12 = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.CardHeader("Фильтры"),
            dbc.Row([
                dbc.Col(update_buttons(type_page), width=2),
                dbc.Col(filter_years(type_page), width=2),
                dbc.Col(html.Div([html.Label("Даты приема (журнал)")]), width="auto"),
                dbc.Col(date_picker(type_page), width=3),
                dbc.Col(
                    html.Div([
                        html.Label("Исключить подразделения"),
                        dcc.Dropdown(
                            id=f'dropdown-exclude-dept-{type_page}', 
                            options=[], 
                            multi=True, 
                            placeholder="Выберите подразделения",
                            style={'minHeight': '60px'},
                            optionHeight=50
                        )
                    ]), width=6
                ),
            ], align="center"),
        ]),
        style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)", "border-radius": "10px"}
    ),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    html.Div(id=f'stat-block-{type_page}', className='filters-label'),
    card_table(f'result-table-{type_page}', "Записаны, но нет ДВ4/ОПВ в году", page_size=10),
    html.Details([
        html.Summary("Отладка (показать/скрыть)"),
        html.Pre(id=f'debug-info-{type_page}', style={"whiteSpace": "pre-wrap"})
    ], open=False)
])


@app.callback(
    Output(f'dropdown-exclude-dept-{type_page}', 'options'),
    [Input(f'dropdown-year-{type_page}', 'value')]
)
def load_departments(year_value):
    # Берем уникальные значения подразделений из журнала обращений
    sql = text("""
        SELECT DISTINCT department
        FROM load_data_journal_appeals
        WHERE COALESCE(NULLIF(department, '-'), '') <> ''
        ORDER BY department
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [{'label': r[0], 'value': r[0]} for r in rows]
    except Exception:
        return []


@app.callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'stat-block-{type_page}', 'children'),
        Output(f'debug-info-{type_page}', 'children'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     State(f'date-picker-range-{type_page}', 'start_date'),
     State(f'date-picker-range-{type_page}', 'end_date'),
     State(f'dropdown-exclude-dept-{type_page}', 'value')]
)
def update_table(n_clicks, year_value, start_date, end_date, exclude_depts):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    if not year_value or not start_date or not end_date:
        return [], [], '', '', html.Div([dcc.Loading(type="default")])

    # Преобразуем формат дат YYYY-MM-DD из DatePickerRange
    start_date_sql = start_date.split('T')[0]
    end_date_sql = end_date.split('T')[0]

    exclude_depts = exclude_depts or []
    query = sql_query_adults_appointments_not_passed(int(year_value), start_date_sql, end_date_sql, exclude_depts)
    try:
        columns, data = TableUpdater.query_to_df(engine, query)
    except Exception as e:
        err = f"Ошибка выполнения основного запроса: {e}\n\nSQL:\n{query}\n\n{traceback.format_exc()}"
        return [], [], 'Ошибка загрузки', err, html.Div([dcc.Loading(type="default")])
    # Статистика: всего записей и уникальных пациентов
    total_rows = len(data)
    unique_enp = len({row.get('ЕНП') for row in data}) if data else 0
    stat_text = f"Записей: {total_rows} | Уникальных пациентов: {unique_enp}"

    # Отладочная информация: промежуточные количества
    q_apps_cnt = f"""
WITH appointments AS (
    SELECT regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
           COALESCE(
             CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
             CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}' THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI') END,
             CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' THEN to_date(acceptance_date, 'DD.MM.YYYY')::timestamp END,
             CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
             CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' THEN to_date(record_date, 'DD.MM.YYYY')::timestamp END
           ) AS appointment_ts
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
), apps AS (
    SELECT * FROM appointments WHERE appointment_ts::date BETWEEN DATE '{start_date_sql}' AND DATE '{end_date_sql}'
)
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT enp_norm) AS uniq_enp,
       to_char(min(appointment_ts), 'YYYY-MM-DD HH24:MI') AS min_ts,
       to_char(max(appointment_ts), 'YYYY-MM-DD HH24:MI') AS max_ts
FROM apps;
"""

    q_adults_cnt = f"""
WITH adults AS (
    SELECT regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
           COALESCE(
             CASE WHEN dr ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
             CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
           ) AS dr_date
    FROM data_loader_iszlpeople
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
)
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT enp_norm) AS uniq_enp
FROM (
  SELECT enp_norm,
         DATE_PART('year', AGE(make_date({int(year_value)}, 12, 31), dr_date))::INT AS age_years
  FROM adults
) t
WHERE age_years >= 18;
"""

    q_join_cnt = f"""
WITH appointments AS (
    SELECT regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
           COALESCE(
             CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
             CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}' THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI') END,
             CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' THEN to_date(acceptance_date, 'DD.MM.YYYY')::timestamp END,
             CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
             CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' THEN to_date(record_date, 'DD.MM.YYYY')::timestamp END
           ) AS appointment_ts
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
), apps AS (
    SELECT * FROM appointments WHERE appointment_ts::date BETWEEN DATE '{start_date_sql}' AND DATE '{end_date_sql}'
), adults AS (
    SELECT regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
           COALESCE(
             CASE WHEN dr ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
             CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
           ) AS dr_date
    FROM data_loader_iszlpeople
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
)
SELECT COUNT(*) AS joined_rows, COUNT(DISTINCT a.enp_norm) AS joined_uniq
FROM (
  SELECT enp_norm,
         DATE_PART('year', AGE(make_date({int(year_value)}, 12, 31), dr_date))::INT AS age_years
  FROM adults
) a
JOIN apps ap ON a.enp_norm = ap.enp_norm
WHERE a.age_years >= 18;
"""

    q_final_cnt = f"""
WITH appointments AS (
    SELECT regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
           COALESCE(
             CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
             CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}' THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI') END,
             CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' THEN to_date(acceptance_date, 'DD.MM.YYYY')::timestamp END,
             CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD')::timestamp END,
             CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' THEN to_date(record_date, 'DD.MM.YYYY')::timestamp END
           ) AS appointment_ts
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
), apps AS (
    SELECT * FROM appointments WHERE appointment_ts::date BETWEEN DATE '{start_date_sql}' AND DATE '{end_date_sql}'
), adults AS (
    SELECT regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
           COALESCE(
             CASE WHEN dr ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
             CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
           ) AS dr_date
    FROM data_loader_iszlpeople
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
)
SELECT COUNT(*) AS final_rows, COUNT(DISTINCT a.enp_norm) AS final_uniq
FROM (
  SELECT enp_norm,
         DATE_PART('year', AGE(make_date({int(year_value)}, 12, 31), dr_date))::INT AS age_years
  FROM adults
) a
JOIN apps ap ON a.enp_norm = ap.enp_norm
WHERE a.age_years >= 18
  AND NOT EXISTS (
        SELECT 1 FROM load_data_oms_data o
        WHERE regexp_replace(o.enp, '\\D', '', 'g') = a.enp_norm
          AND o.goal IN ('ДВ4','ОПВ') AND o.report_year = {int(year_value)}
  );
"""

    # Выполняем count-запросы
    try:
        _, apps_cnt = TableUpdater.query_to_df(engine, q_apps_cnt)
        _, adults_cnt = TableUpdater.query_to_df(engine, q_adults_cnt)
        _, join_cnt = TableUpdater.query_to_df(engine, q_join_cnt)
        _, final_cnt = TableUpdater.query_to_df(engine, q_final_cnt)
    except Exception as e:
        err = (
            f"Ошибка выполнения отладочных запросов: {e}\n\n"
            f"apps_cnt SQL:\n{q_apps_cnt}\n\n"
            f"adults_cnt SQL:\n{q_adults_cnt}\n\n"
            f"join_cnt SQL:\n{q_join_cnt}\n\n"
            f"final_cnt SQL:\n{q_final_cnt}\n\n{traceback.format_exc()}"
        )
        return columns, data, stat_text, err, html.Div([dcc.Loading(type="default")])

    def first_row_val(rows, key):
        if rows and isinstance(rows, list):
            return rows[0].get(key)
        return None

    dbg = []
    dbg.append(f"Год: {year_value}; Даты: {start_date_sql} .. {end_date_sql}")
    dbg.append(f"apps (журнал после парсинга) — rows: {first_row_val(apps_cnt,'total_rows')}, uniq ENP: {first_row_val(apps_cnt,'uniq_enp')}, диапазон: {first_row_val(apps_cnt,'min_ts')} .. {first_row_val(apps_cnt,'max_ts')}")
    dbg.append(f"adults (18+) — rows: {first_row_val(adults_cnt,'total_rows')}, uniq ENP: {first_row_val(adults_cnt,'uniq_enp')}")
    dbg.append(f"join (adults∩apps) — rows: {first_row_val(join_cnt,'joined_rows')}, uniq ENP: {first_row_val(join_cnt,'joined_uniq')}")
    dbg.append(f"final (без ДВ4/ОПВ {int(year_value)}) — rows: {first_row_val(final_cnt,'final_rows')}, uniq ENP: {first_row_val(final_cnt,'final_uniq')} — должно совпадать с таблицей: {total_rows}")
    debug_text = "\n".join(dbg)

    return columns, data, stat_text, debug_text, html.Div([dcc.Loading(type="default")])


