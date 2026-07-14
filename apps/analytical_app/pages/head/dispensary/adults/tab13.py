from dash import html, dcc, Output, Input, State, exceptions
import traceback
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.elements import card_table
from apps.analytical_app.components.filters import filter_years, update_buttons
from apps.analytical_app.query_executor import engine, execute_query
from apps.analytical_app.pages.head.dispensary.adults.query import (
    sql_query_attached_disp_list,
    sql_query_attached_disp_analytics,
)


type_page = "tab13-da"

_PASS_STATUS_LABELS = {
    "all": "Все",
    "passed": "Прошедшие",
    "not_passed": "Не прошедшие",
}


def filter_lpuuch(type_page):
    """Создает мультиселект дропдаун для выбора участков, отсортированных по последним 3 цифрам"""
    query = """
        SELECT DISTINCT lpuuch
        FROM data_loader_iszlpeople
        WHERE COALESCE(NULLIF(lpuuch, '-'), '') <> ''
    """
    try:
        lpuuch_list = [row[0] for row in execute_query(query) if row[0]]

        def get_sort_key(lpu):
            if '_' in lpu:
                parts = lpu.split('_')
                if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) >= 3:
                    return parts[1][-3:]
                return lpu[-3:] if len(lpu) >= 3 else lpu
            return lpu[-3:] if len(lpu) >= 3 else lpu

        sorted_lpuuch = sorted(lpuuch_list, key=lambda x: (get_sort_key(x), x))
        options = [{'label': lpu, 'value': lpu} for lpu in sorted_lpuuch]
    except Exception:
        options = []

    return html.Div([
        html.Label("Участки"),
        dcc.Dropdown(
            id=f'dropdown-lpuuch-{type_page}',
            options=options,
            value=[],
            multi=True,
            clearable=True,
            placeholder="Выберите участки...",
            searchable=True
        )
    ])


adults_dv13 = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.CardHeader("Фильтры"),
            dbc.Row([
                dbc.Col(update_buttons(type_page), width=2),
                dbc.Col(filter_years(type_page), width=2),
                dbc.Col(
                    html.Div([
                        html.Label("Статус"),
                        dcc.Dropdown(
                            id=f'dropdown-pass-status-{type_page}',
                            options=[
                                {'label': 'Все', 'value': 'all'},
                                {'label': 'Прошедшие', 'value': 'passed'},
                                {'label': 'Не прошедшие', 'value': 'not_passed'},
                            ],
                            value='not_passed',
                            placeholder="Статус диспансеризации",
                        )
                    ]), width=2
                ),
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
                    ]), width=1
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
                    ]), width=1
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
            dbc.Row([
                dbc.Col(filter_lpuuch(type_page), width=4),
            ], align="center", className="mt-2"),
        ]),
        style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)", "border-radius": "10px"}
    ),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    dbc.Tabs([
        dbc.Tab(label="Список", tab_id="list", children=[
            html.Div(id=f'stat-block-{type_page}', className='filters-label', style={'marginTop': '12px'}),
            card_table(f'result-table-{type_page}', "Прикреплённые пациенты", page_size=20),
        ]),
        dbc.Tab(label="Аналитика", tab_id="analytics", children=[
            card_table(
                f'analytics-table-{type_page}',
                "Разбивка по возрастам (прикреплено / прошли / не прошли)",
                page_size=30,
            ),
        ]),
    ], id=f'tabs-{type_page}', active_tab="list"),
    html.Details([
        html.Summary("Отладка (показать/скрыть)"),
        html.Pre(id=f'debug-info-{type_page}', style={"whiteSpace": "pre-wrap"})
    ], open=False)
])


def _normalize_age_bounds(age_from, age_to):
    if age_from is None:
        age_from = 18
    if age_to is None:
        age_to = 120
    if age_from > age_to:
        age_from, age_to = age_to, age_from
    return int(age_from), int(age_to)


@app.callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'analytics-table-{type_page}', 'columns'),
        Output(f'analytics-table-{type_page}', 'data'),
        Output(f'stat-block-{type_page}', 'children'),
        Output(f'debug-info-{type_page}', 'children'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [
        State(f'dropdown-year-{type_page}', 'value'),
        State(f'dropdown-pass-status-{type_page}', 'value'),
        State(f'dropdown-gender-{type_page}', 'value'),
        State(f'input-age-from-{type_page}', 'value'),
        State(f'input-age-to-{type_page}', 'value'),
        State(f'dropdown-disp-type-{type_page}', 'value'),
        State(f'dropdown-lpuuch-{type_page}', 'value'),
    ]
)
def update_table(n_clicks, year_value, pass_status, gender_value, age_from, age_to,
                 disp_type, lpuuch_values):
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading = html.Div([dcc.Loading(type="default")])
    empty = ([], [], [], [], '', '', loading)

    if not year_value:
        return empty

    age_from, age_to = _normalize_age_bounds(age_from, age_to)
    pass_status = pass_status or 'not_passed'
    lpuuch_values = lpuuch_values or []

    list_query = sql_query_attached_disp_list(
        int(year_value),
        pass_status,
        gender_value,
        age_from,
        age_to,
        disp_type,
        lpuuch_values,
    )
    analytics_query = sql_query_attached_disp_analytics(
        int(year_value),
        gender_value,
        age_from,
        age_to,
        disp_type,
        lpuuch_values,
    )

    try:
        columns, data = TableUpdater.query_to_df(engine, list_query)
        analytics_columns, analytics_data = TableUpdater.query_to_df(engine, analytics_query)
    except Exception as e:
        err = (
            f"Ошибка выполнения запроса: {e}\n\n"
            f"SQL (список):\n{list_query}\n\n"
            f"SQL (аналитика):\n{analytics_query}\n\n"
            f"{traceback.format_exc()}"
        )
        return [], [], [], [], 'Ошибка загрузки', err, loading

    total_rows = len(data)
    unique_enp = len({row.get('ЕНП') for row in data}) if data else 0
    male_count = sum(1 for row in data if row.get('Пол') == 'М') if data else 0
    female_count = sum(1 for row in data if row.get('Пол') == 'Ж') if data else 0
    passed_count = sum(1 for row in data if row.get('Статус') == 'Прошёл') if data else 0
    not_passed_count = sum(1 for row in data if row.get('Статус') == 'Не прошёл') if data else 0
    dv4_count = sum(1 for row in data if row.get('Требуемый тип') == 'ДВ4') if data else 0
    opv_count = sum(1 for row in data if row.get('Требуемый тип') == 'ОПВ') if data else 0

    stat_text = (
        f"Статус: {_PASS_STATUS_LABELS.get(pass_status, pass_status)} | "
        f"Всего: {total_rows} | Уникальных: {unique_enp} | "
        f"Прошли: {passed_count} | Не прошли: {not_passed_count} | "
        f"М: {male_count} | Ж: {female_count} | ДВ4: {dv4_count} | ОПВ: {opv_count}"
    )

    debug_info = f"""
Год: {year_value}
Статус: {_PASS_STATUS_LABELS.get(pass_status, pass_status)}
Пол: {gender_value if gender_value != 'all' else 'Все'}
Возраст: {age_from}-{age_to}
Тип диспансеризации: {disp_type if disp_type != 'all' else 'Все'}
Участки: {', '.join(lpuuch_values) if lpuuch_values else 'Все'}
Строк аналитики: {len(analytics_data)}
"""

    return columns, data, analytics_columns, analytics_data, stat_text, debug_info, loading
