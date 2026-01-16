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


type_page = "tab13-da"


adults_dv13 = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.CardHeader("Фильтры"),
            dbc.Row([
                dbc.Col(update_buttons(type_page), width=2),
                dbc.Col(filter_years(type_page), width=2),
                dbc.Col(
                    html.Div([
                        html.Label("Пол"),
                        dcc.Dropdown(
                            id=f'dropdown-gender-{type_page}',
                            options=[
                                {'label': 'Все', 'value': 'all'},
                                {'label': 'Мужской', 'value': 'М'},
                                {'label': 'Женский', 'value': 'Ж'}
                            ],
                            value='all',
                            placeholder="Выберите пол"
                        )
                    ]), width=2
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Возраст от"),
                        dcc.Input(
                            id=f'input-age-from-{type_page}',
                            type='number',
                            placeholder='18',
                            min=0,
                            max=120,
                            value=18
                        )
                    ]), width=2
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Возраст до"),
                        dcc.Input(
                            id=f'input-age-to-{type_page}',
                            type='number',
                            placeholder='120',
                            min=0,
                            max=120,
                            value=120
                        )
                    ]), width=2
                ),
                dbc.Col(
                    html.Div([
                        html.Label("Тип диспансеризации"),
                        dcc.Dropdown(
                            id=f'dropdown-disp-type-{type_page}',
                            options=[
                                {'label': 'Все', 'value': 'all'},
                                {'label': 'ДВ4', 'value': 'ДВ4'},
                                {'label': 'ОПВ', 'value': 'ОПВ'}
                            ],
                            value='all',
                            placeholder="Выберите тип"
                        )
                    ]), width=2
                ),
            ], align="center"),
        ]),
        style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)", "border-radius": "10px"}
    ),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    html.Div(id=f'stat-block-{type_page}', className='filters-label'),
    card_table(f'result-table-{type_page}', "Прикрепленные не прошедшие диспансеризацию", page_size=20),
    html.Details([
        html.Summary("Отладка (показать/скрыть)"),
        html.Pre(id=f'debug-info-{type_page}', style={"whiteSpace": "pre-wrap"})
    ], open=False)
])


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
     State(f'dropdown-gender-{type_page}', 'value'),
     State(f'input-age-from-{type_page}', 'value'),
     State(f'input-age-to-{type_page}', 'value'),
     State(f'dropdown-disp-type-{type_page}', 'value')]
)
def update_table(n_clicks, year_value, gender_value, age_from, age_to, disp_type):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    if not year_value:
        return [], [], '', '', html.Div([dcc.Loading(type="default")])

    # Валидация возраста
    if age_from is None:
        age_from = 18
    if age_to is None:
        age_to = 120
    if age_from > age_to:
        age_from, age_to = age_to, age_from

    # Формируем условия фильтрации
    gender_condition = ""
    if gender_value and gender_value != 'all':
        gender_condition = f"AND a.gender = '{gender_value}'"

    age_condition = f"AND a.age_years >= {age_from} AND a.age_years <= {age_to}"

    disp_condition = ""
    if disp_type and disp_type != 'all':
        disp_condition = f"AND o.goal = '{disp_type}'"

    query = f"""
WITH attached_patients AS (
    SELECT 
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        fio,
        dr,
        CASE 
            WHEN LOWER("fio") LIKE '%ович%' THEN 'М'
            WHEN LOWER("fio") LIKE '%евич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%овна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%евна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ична%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%инична%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%овна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%евна%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ична%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%инична%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%ья%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%иа%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%йя%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%инич%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ус%' THEN 'М'
            WHEN LOWER("fio") LIKE '%ия%' THEN 'Ж'
            WHEN LOWER("fio") LIKE '%джонзода%' THEN 'М'
            WHEN LOWER("fio") LIKE '%мохаммед%' THEN 'М'
            WHEN RIGHT(LOWER("fio"), 1) IN ('а', 'я', 'и', 'е', 'о', 'у', 'э', 'ю') THEN 'Ж'
            ELSE 'М'
        END AS gender,
        lpuuch,
        COALESCE(
            CASE WHEN dr ~ '^[0-9]{{2}}[.][0-9]{{2}}[.][0-9]{{4}}' THEN to_date(dr, 'DD.MM.YYYY') END,
            CASE WHEN dr ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN to_date(dr, 'YYYY-MM-DD') END
        ) AS dr_date
    FROM data_loader_iszlpeople
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND COALESCE(NULLIF(fio, '-'), '') <> ''
),
adults AS (
    SELECT 
        enp_norm,
        fio,
        dr,
        gender,
        lpuuch,
        dr_date,
        DATE_PART('year', AGE(make_date({int(year_value)}, 12, 31), dr_date))::INT AS age_years
    FROM attached_patients
    WHERE dr_date IS NOT NULL
),
patients_without_disp AS (
    SELECT 
        a.enp_norm,
        a.fio,
        a.dr,
        a.gender,
        a.lpuuch,
        a.age_years,
        CASE 
            WHEN a.age_years IN (19,20,22,23,25,26,28,29,31,32,34,35,37,38) THEN 'ОПВ' 
            ELSE 'ДВ4' 
        END AS required_disp_type
    FROM adults a
    WHERE a.age_years >= 18
      {gender_condition}
      {age_condition}
      AND NOT EXISTS (
            SELECT 1 
            FROM load_data_oms_data o
            WHERE regexp_replace(o.enp, '\\D', '', 'g') = a.enp_norm
              AND o.goal IN ('ДВ4', 'ОПВ')
              AND o.report_year = {int(year_value)}
              {disp_condition}
        )
),
patient_phones AS (
    SELECT DISTINCT ON (regexp_replace(enp, '\\D', '', 'g'))
        regexp_replace(enp, '\\D', '', 'g') AS enp_norm,
        phone
    FROM load_data_journal_appeals
    WHERE COALESCE(NULLIF(enp, '-'), '') <> ''
      AND COALESCE(NULLIF(phone, '-'), '') <> ''
    ORDER BY regexp_replace(enp, '\\D', '', 'g'), 
             COALESCE(
                 CASE WHEN acceptance_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' 
                      THEN to_date(SUBSTRING(acceptance_date FROM 1 FOR 10), 'YYYY-MM-DD') END,
                 CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}[ ]+[0-9]{{2}}:[0-9]{{2}}' 
                      THEN to_timestamp(acceptance_date, 'DD.MM.YYYY HH24:MI')::date END,
                 CASE WHEN acceptance_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' 
                      THEN to_date(acceptance_date, 'DD.MM.YYYY') END,
                 CASE WHEN record_date ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' 
                      THEN to_date(SUBSTRING(record_date FROM 1 FOR 10), 'YYYY-MM-DD') END,
                 CASE WHEN record_date ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}}$' 
                      THEN to_date(record_date, 'DD.MM.YYYY') END
             ) DESC NULLS LAST,
             id DESC
)
SELECT 
    p.fio AS "ФИО",
    p.dr AS "ДР",
    p.enp_norm AS "ЕНП",
    p.gender AS "Пол",
    p.lpuuch AS "Участок",
    p.age_years AS "Возраст",
    p.required_disp_type AS "Требуемый тип",
    COALESCE(ph.phone, '') AS "Телефон"
FROM patients_without_disp p
LEFT JOIN patient_phones ph ON p.enp_norm = ph.enp_norm
ORDER BY p.lpuuch, p.fio
"""

    try:
        columns, data = TableUpdater.query_to_df(engine, query)
    except Exception as e:
        err = f"Ошибка выполнения запроса: {e}\n\nSQL:\n{query}\n\n{traceback.format_exc()}"
        return [], [], 'Ошибка загрузки', err, html.Div([dcc.Loading(type="default")])

    # Статистика
    total_rows = len(data)
    unique_enp = len({row.get('ЕНП') for row in data}) if data else 0
    
    # Подсчет по полу
    male_count = sum(1 for row in data if row.get('Пол') == 'М') if data else 0
    female_count = sum(1 for row in data if row.get('Пол') == 'Ж') if data else 0
    
    # Подсчет по типу диспансеризации
    dv4_count = sum(1 for row in data if row.get('Требуемый тип') == 'ДВ4') if data else 0
    opv_count = sum(1 for row in data if row.get('Требуемый тип') == 'ОПВ') if data else 0

    stat_text = f"Всего: {total_rows} | Уникальных: {unique_enp} | М: {male_count} | Ж: {female_count} | ДВ4: {dv4_count} | ОПВ: {opv_count}"

    # Отладочная информация
    debug_info = f"""
Год: {year_value}
Пол: {gender_value if gender_value != 'all' else 'Все'}
Возраст: {age_from}-{age_to}
Тип диспансеризации: {disp_type if disp_type != 'all' else 'Все'}

SQL условия:
- Пол: {gender_condition or 'Не указано'}
- Возраст: {age_condition}
- Тип диспансеризации: {disp_condition or 'Не указано'}
"""

    return columns, data, stat_text, debug_info, html.Div([dcc.Loading(type="default")])
