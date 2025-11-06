# File: apps/analytical_app/pages/economist/goal_groups_report/page.py

import json
from datetime import datetime
from dash import html, dcc, Input, Output, State, exceptions, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import (
    filter_years, update_buttons, get_current_reporting_month,
    filter_inogorod
)
from apps.analytical_app.pages.economist.goal_groups_report.query import sql_query_goal_groups_report
from apps.analytical_app.query_executor import engine

type_page = "econ-goal-groups-report"


# Вспомогательная функция сортировки
def sort_key(x):
    return (0, int(x)) if x.isdigit() else (1, x.lower())


# Функция для загрузки списка конфигураций из БД
def load_configs():
    return pd.read_sql(
        text("""
            SELECT id, name, groups::text AS groups_json, created_at
            FROM plan_goalgroupconfig
            ORDER BY created_at DESC
        """),
        engine
    )


# Глобальный словарь групп целей (будет обновляться в колбэке)
GOAL_GROUPS = {}


# --- Layout как функция, чтобы при каждом заходе подтягивались свежие настройки ---
def economist_goal_groups_report_def():
    # Загружаем конфигурации
    df_configs = load_configs()
    config_options = [
        {
            "label": f"{row['name']} ({row['created_at'].strftime('%Y-%m-%d')})",
            "value": row["id"]
        }
        for _, row in df_configs.iterrows()
    ]
    # По умолчанию не выбираем конфигурацию
    default_config = None
    
    # Получаем текущий отчетный месяц
    current_month_num, current_month_name = get_current_reporting_month()
    
    # Опции для выбора отчетного месяца
    month_options = [
        {"label": "Январь", "value": 1},
        {"label": "Февраль", "value": 2},
        {"label": "Март", "value": 3},
        {"label": "Апрель", "value": 4},
        {"label": "Май", "value": 5},
        {"label": "Июнь", "value": 6},
        {"label": "Июль", "value": 7},
        {"label": "Август", "value": 8},
        {"label": "Сентябрь", "value": 9},
        {"label": "Октябрь", "value": 10},
        {"label": "Ноябрь", "value": 11},
        {"label": "Декабрь", "value": 12},
    ]

    return html.Div([
        # Выбор конфигурации
        dbc.Row([
            dbc.Col([
                html.Label("Конфигурация групп целей:", className="me-2"),
                html.Div([
                    dcc.Dropdown(
                        id=f"dropdown-config-{type_page}",
                        options=config_options,
                        value=default_config,
                        placeholder="Выберите конфигурацию",
                        clearable=True,
                        style={"width": "360px", "flex": "0 0 auto"}
                    ),
                    dbc.Button(
                        "Показать все группы и цели",
                        id=f"open-offcanvas-{type_page}",
                        color="secondary",
                        n_clicks=0,
                        className="ms-2",
                        style={"flex": "0 0 auto"}
                    ),
                ],
                    style={"display": "flex", "alignItems": "center"})
            ]),
        ], className="mb-3"),
        
        dbc.Offcanvas(
            children=[
                html.Div(id=f"offcanvas-body-{type_page}"),
                dbc.Button(
                    "Закрыть",
                    id=f"close-offcanvas-{type_page}",
                    color="outline-secondary",
                    n_clicks=0,
                    className="mt-4"
                ),
            ],
            id=f"offcanvas-goals-{type_page}",
            title="Группы и их цели",
            is_open=False,
            scrollable=True,
            backdrop=True,
            placement="end",
            className="shadow",
            style={"maxWidth": "520px"},
        ),
        
        # Фильтры
        dbc.Card(
            dbc.CardBody([
                dbc.CardHeader([
                    html.H5("Фильтры", className="mb-0 fw-bold")
                ], className="bg-primary text-white"),
                
                # Первая строка: кнопка обновления, год, отчетный месяц
                dbc.Row([
                    dbc.Col(
                        dcc.Loading(
                            id=f'loading-button-{type_page}',
                            type="circle",
                            children=html.Div(update_buttons(type_page))
                        ), width=1
                    ),
                    dbc.Col([
                        dbc.Label("Год:", className="fw-bold mb-1"),
                        filter_years(type_page)
                    ], width=1),
                    dbc.Col([
                        dbc.Label("Текущий отчетный месяц:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id=f"dropdown-reporting-month-{type_page}",
                            options=month_options,
                            value=current_month_num,
                            clearable=False,
                            style={"width": "100%"}
                        ),
                        html.Small(
                            f"По умолчанию: {current_month_name}",
                            className="text-muted d-block mt-1"
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Иногородние:", className="fw-bold mb-1"),
                        filter_inogorod(type_page)
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Санкции:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id=f'dropdown-sanction-{type_page}',
                            options=[
                                {'label': 'Без санкций', 'value': '1'},
                                {'label': 'Санкции', 'value': '2'},
                                {'label': 'Все', 'value': '3'}
                            ],
                            value='1',  # По умолчанию "Без санкций"
                            clearable=False,
                            style={"width": "100%"}
                        )
                    ], width=2),
                ], align="end", className="mb-3 mt-3"),
                
                # Вторая строка: выбор целей
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Режим выбора целей:", className="mt-2 fw-bold"),
                        dbc.RadioItems(
                            id=f"goals-selection-mode-{type_page}",
                            options=[
                                {"label": "Группы", "value": "group"},
                                {"label": "Отдельные", "value": "individual"}
                            ],
                            value="individual",
                            inline=True,
                            className="mb-3"
                        ),
                        
                        # Дропдаун групп целей (скрыт по умолчанию)
                        html.Div(
                            [
                                dbc.Label("Выберите группы целей:", className="mb-2"),
                                dcc.Dropdown(id=f"dropdown-goal-groups-{type_page}", multi=True)
                            ],
                            id=f"goal-groups-container-{type_page}",
                            style={'display': 'none'}
                        ),
                        
                        # Превью выбранных групп/целей
                        html.Div(
                            id=f"preview-goals-{type_page}",
                            className="mt-2 mb-3 p-2 bg-light rounded",
                            style={"fontStyle": "italic", "whiteSpace": "pre-line", "minHeight": "50px"}
                        ),
                        
                        # Дропдаун отдельных целей
                        html.Div(
                            [
                                dbc.Label("Выберите цели:", className="mb-2"),
                                dcc.Dropdown(id=f"dropdown-goals-{type_page}", multi=True)
                            ],
                            id=f"goals-individual-container-{type_page}"
                        ),
                        
                        # Чекбокс для детализации по целям внутри групп
                        html.Div([
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Checkbox(
                                                id=f"show-goals-detail-{type_page}",
                                                label="",
                                                value=False,
                                                className="me-2"
                                            )
                                        ], width="auto"),
                                        dbc.Col([
                                            html.Label(
                                                "Показывать детализацию по целям внутри групп",
                                                className="fw-bold mb-0",
                                                htmlFor=f"show-goals-detail-{type_page}",
                                                style={"cursor": "pointer"}
                                            )
                                        ], width=True)
                                    ], align="center", className="g-0")
                                ], className="py-2")
                            ], className="mt-3 border-primary", style={"borderWidth": "2px"})
                        ], id=f"goals-detail-container-{type_page}", style={'display': 'none'})
                    ], width=12),
                ], className="mb-3"),
                
                # Информация о фильтрах по статусам
                dbc.Alert(
                    [
                        html.H6("Фильтрация по статусам:", className="alert-heading fw-bold"),
                        html.P("• Для текущего отчетного месяца: статусы 2, 3", className="mb-1"),
                        html.P("• Для всех предыдущих месяцев: статус 3", className="mb-0"),
                    ],
                    color="info",
                    className="mb-0"
                ),
                
            ])
        , className="mb-3 shadow-sm", style={"borderRadius": "8px"}),

        # Результаты: таблица
        dcc.Loading(
            id=f'loading-table-{type_page}',
            type="default",
            children=html.Div(id=f'result-table-container-{type_page}')
        ),
        
        # Скрытое хранилище для обновления GOAL_GROUPS
        dcc.Store(id=f"dummy-store-{type_page}", data={})

    ], style={"padding": "0rem"})


economist_goal_groups_report = economist_goal_groups_report_def()


# колбэк для открытия/закрытия Offcanvas
@app.callback(
    Output(f"offcanvas-goals-{type_page}", "is_open"),
    Input(f"open-offcanvas-{type_page}", "n_clicks"),
    Input(f"close-offcanvas-{type_page}", "n_clicks"),
    State(f"offcanvas-goals-{type_page}", "is_open"),
)
def toggle_offcanvas(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open


# колбэк для наполнения Offcanvas по выбранной конфигурации
@app.callback(
    Output(f"offcanvas-body-{type_page}", "children"),
    Input(f"dropdown-config-{type_page}", "value")
)
def update_offcanvas_body(config_id):
    if not config_id:
        return html.Div("Конфигурация не выбрана.", className="text-muted")
    df = load_configs()
    row = df[df["id"] == config_id].iloc[0]
    groups = json.loads(row["groups_json"])

    # строим список: заголовок группы + ul-лист целей
    content = []
    for grp, goals in sorted(groups.items(), key=lambda x: x[0].lower()):
        content.append(html.H6(grp, className="mt-3 mb-1"))
        content.append(
            html.Ul([html.Li(g) for g in sorted(goals, key=sort_key)])
        )
    return content


# При смене конфигурации — обновляем список групп
@app.callback(
    Output(f"dropdown-config-{type_page}", "options"),
    Input(f"dropdown-config-{type_page}", "value")
)
def update_config_options(config_id):
    df_configs = load_configs()
    config_options = [
        {
            "label": f"{row['name']} ({row['created_at'].strftime('%Y-%m-%d')})",
            "value": row["id"]
        }
        for _, row in df_configs.iterrows()
    ]
    return config_options


# При смене конфигурации — обновляем список групп и переключаем режим
@app.callback(
    Output(f"dropdown-goal-groups-{type_page}", "options"),
    Output(f"dropdown-goal-groups-{type_page}", "value"),
    Output(f"goals-selection-mode-{type_page}", "value"),
    Output(f"dummy-store-{type_page}", "data"),
    Input(f"dropdown-config-{type_page}", "value")
)
def apply_config(config_id):
    global GOAL_GROUPS
    if not config_id:
        GOAL_GROUPS = {}
        return [], [], "individual", {}
    
    df = load_configs()
    row = df[df["id"] == config_id].iloc[0]
    groups_dict = json.loads(row["groups_json"])
    GOAL_GROUPS = groups_dict
    
    grp_opts = [
        {"label": grp, "value": grp}
        for grp in sorted(groups_dict.keys(), key=lambda x: x.lower())
    ]
    # По умолчанию выбираем все группы конфигурации и переключаем в режим "Группы"
    return grp_opts, [opt["value"] for opt in grp_opts], "group", groups_dict


# В зависимости от режима «Группы»/«Отдельные» наполняем дроп-целей
@app.callback(
    Output(f"dropdown-goals-{type_page}", "options"),
    Output(f"dropdown-goals-{type_page}", "value"),
    Input(f"goals-selection-mode-{type_page}", "value"),
    Input(f"dropdown-config-{type_page}", "value"),
)
def update_goals_options(mode, config_id):
    # Режим «Группы» → все цели из GOAL_GROUPS
    if mode == "group" and GOAL_GROUPS:
        all_goals = sorted(
            {g for lst in GOAL_GROUPS.values() for g in lst},
            key=sort_key
        )
        opts = [{"label": g, "value": g} for g in all_goals]
        return opts, []
    
    # Режим «Отдельные» → берём все уникальные цели напрямую из таблицы
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT DISTINCT goal "
            "FROM data_loader_omsdata "
            "WHERE goal IS NOT NULL AND goal <> '-'"
        )).fetchall()
    goals = sorted([r[0] for r in rows], key=sort_key)
    opts = [{"label": g, "value": g} for g in goals]
    return opts, []


# Превью целей по выбранным группам
@app.callback(
    Output(f"preview-goals-{type_page}", "children"),
    Input(f"dropdown-goal-groups-{type_page}", "value")
)
def _preview_goals(selected_groups):
    if not selected_groups:
        return ""
    lines = []
    for grp in selected_groups:
        items = GOAL_GROUPS.get(grp, [])
        if items:
            lines.append(f"{grp}: {', '.join(items)}")
    return "\n".join(lines)


# Toggle между группами и отдельными целями
@app.callback(
    Output(f'goal-groups-container-{type_page}', 'style'),
    Output(f'goals-individual-container-{type_page}', 'style'),
    Output(f'goals-detail-container-{type_page}', 'style'),
    Input(f'goals-selection-mode-{type_page}', 'value')
)
def toggle_goals(mode):
    if mode == 'group':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'block'}
    else:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}




# Таблица с отчетом
@app.callback(
    Output(f'result-table-container-{type_page}', 'children'),
    Input(f'update-button-{type_page}', 'n_clicks'),
    State(f'dropdown-year-{type_page}', 'value'),
    State(f'dropdown-config-{type_page}', 'value'),
    State(f'dropdown-reporting-month-{type_page}', 'value'),
    State(f'dropdown-inogorodniy-{type_page}', 'value'),
    State(f'dropdown-sanction-{type_page}', 'value'),
    State(f'goals-selection-mode-{type_page}', 'value'),
    State(f'dropdown-goals-{type_page}', 'value'),
    State(f'dropdown-goal-groups-{type_page}', 'value'),
    State(f'show-goals-detail-{type_page}', 'value'),
)
def update_table_goal_groups_report(
        n, year, config_id, reporting_month, inogorod, sanction,
        goal_mode, indiv_goals, grp_goals, show_goals_detail
):
    if not n:
        raise exceptions.PreventUpdate
    
    # Группы и цели
    if goal_mode == 'group' and grp_goals:
        group_mapping = {g: GOAL_GROUPS.get(g, []) for g in grp_goals}
        goals = [item for g in grp_goals for item in GOAL_GROUPS.get(g, [])]
    elif goal_mode == 'individual' and indiv_goals:
        group_mapping = {}
        goals = indiv_goals
    else:
        # Если ничего не выбрано, проверяем конфигурацию
        if not config_id:
            return html.Div([
                dbc.Alert([
                    html.H5("Конфигурация не выбрана", className="alert-heading"),
                    html.P("Пожалуйста, выберите конфигурацию групп целей для формирования отчета."),
                ], color="warning", className="mt-3")
            ])
        
        df = load_configs()
        row = df[df["id"] == config_id].iloc[0]
        group_mapping = json.loads(row["groups_json"])
        
        if not group_mapping:
            return html.Div([
                dbc.Alert([
                    html.H5("Конфигурация пуста", className="alert-heading"),
                    html.P("Выбранная конфигурация не содержит групп целей."),
                ], color="warning", className="mt-3")
            ])
        
        # Берем все цели из конфигурации
        goals = [item for lst in group_mapping.values() for item in lst]
    
    goals = sorted(dict.fromkeys(goals), key=sort_key)
    
    # Генерируем SQL-запрос
    sql = sql_query_goal_groups_report(
        selected_year=year,
        current_reporting_month=reporting_month,
        group_mapping=group_mapping,
        inogorodniy=inogorod,
        sanction=sanction,
        show_goals_detail=show_goals_detail if goal_mode == 'group' else False,
    )
    
    try:
        cols, data = TableUpdater.query_to_df(engine, sql)
        df_result = pd.DataFrame(data)
    except Exception as e:
        return html.Div([
            dbc.Alert([
                html.H5("Ошибка при выполнении запроса", className="alert-heading"),
                html.P(f"Произошла ошибка: {str(e)}"),
            ], color="danger", className="mt-3")
        ])
    
    # Проверяем, пустая ли таблица
    if df_result.empty:
        return html.Div([
            dbc.Alert([
                html.H5("Данные не найдены", className="alert-heading"),
                html.P("По выбранным условиям не найдено ни одной записи."),
                html.Hr(),
                html.H6("💡 Попробуйте изменить условия:"),
                html.Ul([
                    html.Li("Проверьте выбранный год"),
                    html.Li("Проверьте выбранный отчетный месяц"),
                    html.Li("Убедитесь, что конфигурация содержит правильные группы целей"),
                ]),
            ], color="info", className="mt-3")
        ])
    
    # Формируем иерархическую структуру данных для отображения
    result_rows = []
    
    # Проверяем, есть ли колонка goal (детализация по целям)
    has_goal_column = 'goal' in df_result.columns
    
    # Получаем уникальные группы
    unique_groups = sorted(df_result['group_name'].unique())
    
    for group_name in unique_groups:
        group_df = df_result[df_result['group_name'] == group_name]
        
        # Добавляем строку с названием группы (итоговая строка)
        group_total = group_df.sum(numeric_only=True)
        group_row = {
            'group_name': group_name,
            'building': group_name,  # Итоговая строка с названием группы
        }
        if has_goal_column:
            group_row['goal'] = ''  # Пустое значение для итоговой строки группы
        
        # Безопасно преобразуем числовые колонки в int
        for col in df_result.columns:
            if col not in ['group_name', 'building', 'goal']:
                value = group_total.get(col, 0)
                try:
                    if pd.notna(value) and value != '':
                        group_row[col] = int(float(value))
                    else:
                        group_row[col] = 0
                except (ValueError, TypeError):
                    group_row[col] = value
        result_rows.append(group_row)
        
        # Если есть детализация по целям, группируем по целям
        if has_goal_column and show_goals_detail:
            unique_goals = sorted(group_df['goal'].dropna().unique())
            for goal in unique_goals:
                goal_df = group_df[group_df['goal'] == goal]
                
                # Добавляем строку с названием цели (итоговая строка для цели)
                goal_total = goal_df.sum(numeric_only=True)
                goal_row = {
                    'group_name': group_name,
                    'goal': goal,
                    'building': goal,  # Итоговая строка с названием цели
                }
                for col in df_result.columns:
                    if col not in ['group_name', 'building', 'goal']:
                        value = goal_total.get(col, 0)
                        try:
                            if pd.notna(value) and value != '':
                                goal_row[col] = int(float(value))
                            else:
                                goal_row[col] = 0
                        except (ValueError, TypeError):
                            goal_row[col] = value
                result_rows.append(goal_row)
                
                # Добавляем строки с подразделениями для этой цели
                for _, row in goal_df.iterrows():
                    dept_row = row.to_dict()
                    for col in df_result.columns:
                        if col not in ['group_name', 'building', 'goal']:
                            value = dept_row.get(col, 0)
                            try:
                                if pd.notna(value) and value != '':
                                    dept_row[col] = int(float(value))
                                else:
                                    dept_row[col] = 0
                            except (ValueError, TypeError):
                                dept_row[col] = value
                    result_rows.append(dept_row)
        else:
            # Без детализации по целям - просто добавляем строки с подразделениями
            for _, row in group_df.iterrows():
                dept_row = row.to_dict()
                if has_goal_column:
                    dept_row['goal'] = ''  # Пустое значение, если детализация не нужна
                for col in df_result.columns:
                    if col not in ['group_name', 'building', 'goal']:
                        value = dept_row.get(col, 0)
                        try:
                            if pd.notna(value) and value != '':
                                dept_row[col] = int(float(value))
                            else:
                                dept_row[col] = 0
                        except (ValueError, TypeError):
                            dept_row[col] = value
                result_rows.append(dept_row)
    
    # Создаем DataFrame из результата
    df_display = pd.DataFrame(result_rows)
    
    # Формируем колонки для таблицы
    table_columns = [
        {
            "name": "Группа целей",
            "id": "group_name",
            "type": "text"
        }
    ]
    
    # Добавляем колонку "Цель", если есть детализация
    if show_goals_detail and 'goal' in df_display.columns:
        table_columns.append({
            "name": "Цель",
            "id": "goal",
            "type": "text"
        })
    
    table_columns.append({
        "name": "Подразделение",
        "id": "building",
        "type": "text"
    })
    
    # Добавляем колонки для месяцев
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
        7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    for month_num in range(1, 13):
        month_name = month_names[month_num]
        if month_name in df_display.columns:
            table_columns.append({
                "name": month_name,
                "id": month_name,
                "type": "numeric",
                "format": {"specifier": ",.0f"}
            })
    
    # Добавляем колонку "Общий итог"
    if "Общий итог" in df_display.columns:
        table_columns.append({
            "name": "Общий итог",
            "id": "Общий итог",
            "type": "numeric",
            "format": {"specifier": ",.0f"}
        })
    
    # Формируем стили для таблицы
    style_data_conditional = []
    
    # Выделяем итоговые строки (где building совпадает с group_name или goal)
    # Используем условие на основе индекса строки
    for idx, row in df_display.iterrows():
        is_total_row = False
        if show_goals_detail and 'goal' in df_display.columns:
            # Итоговая строка группы или цели
            goal_val = row.get('goal', '')
            building_val = row.get('building', '')
            group_val = row.get('group_name', '')
            is_total_row = (group_val == building_val) or (pd.notna(goal_val) and goal_val != '' and goal_val == building_val)
        else:
            # Итоговая строка группы
            is_total_row = row.get('group_name', '') == row.get('building', '')
        
        if is_total_row:
            style_data_conditional.append({
                'if': {'row_index': idx},
                'backgroundColor': '#e3f2fd',
                'fontWeight': 'bold'
            })
    
    # Рендерим DataTable
    return html.Div([
        dash_table.DataTable(
            id=f"table-{type_page}",
            columns=table_columns,
            data=df_display.to_dict('records'),
            page_size=50,
            sort_action="native",
            filter_action="native",
            export_format="xlsx",
            style_table={"overflowX": "auto"},
            style_data_conditional=style_data_conditional,
            style_cell={
                'textAlign': 'left',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold'
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto'
            },
        )
    ])

