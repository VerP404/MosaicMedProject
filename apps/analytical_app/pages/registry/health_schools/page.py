# -*- coding: utf-8 -*-
"""
АНАЛИЗ ШКОЛ ЗДОРОВЬЯ
Dash-приложение для анализа школ здоровья пациентов
Отслеживание плановых явок по группам заболеваний
"""

import pandas as pd
import time
from datetime import datetime, date, timedelta
from dash import html, dcc, Input, Output, State, callback_context, dash_table, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.query_executor import execute_query

type_page = "health_schools"

# Кэш для оптимизации
_talons_cache = {}
_df_processed_cache = None
_last_data_load_time = 0

# Определение групп заболеваний
DISEASE_GROUPS = {
    'I1%': 'Артериальная гипертония',
    'I5%': 'Сердечная недостаточность', 
    'J4%': 'Бронхиальная астма',
    'E1%': 'Сахарный диабет'
}

def get_health_schools_data(limit=5000):
    """Получает данные школ здоровья из базы данных с ограничением"""
    query = """
    SELECT 
        enp,
        patient,
        birth_date,
        treatment_end,
        main_diagnosis_code,
        goal,
        building,
        doctor,
        specialty,
        talon,
        status,
        treatment_start
    FROM load_data_oms_data 
    WHERE goal = '307'
    ORDER BY treatment_end DESC
    LIMIT {}
    """.format(limit)
    
    try:
        result = execute_query(query)
        
        if not result:
            return pd.DataFrame()
        
        # Преобразуем результат в DataFrame
        columns = ['enp', 'patient', 'birth_date', 'treatment_end', 'main_diagnosis_code', 
                  'goal', 'building', 'doctor', 'specialty', 'talon', 'status', 'treatment_start']
        df = pd.DataFrame(result, columns=columns)
        
        # Преобразуем даты
        df['treatment_end'] = pd.to_datetime(df['treatment_end'], errors='coerce')
        df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
        df['treatment_start'] = pd.to_datetime(df['treatment_start'], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return pd.DataFrame()

def determine_disease_group(diagnosis_code):
    """Определяет группу заболевания по коду диагноза"""
    if pd.isna(diagnosis_code):
        return None
    
    diagnosis_str = str(diagnosis_code)
    for pattern, group_name in DISEASE_GROUPS.items():
        if diagnosis_str.startswith(pattern.replace('%', '')):
            return group_name
    
    return None

def process_health_schools_data(df):
    """Обрабатывает данные школ здоровья и группирует по пациентам"""
    if df.empty:
        return pd.DataFrame()
    
    # Добавляем группу заболевания
    df['disease_group'] = df['main_diagnosis_code'].apply(determine_disease_group)
    
    # Фильтруем только записи с определенными группами заболеваний
    df_filtered = df[df['disease_group'].notna()].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Группируем данные для обработки
    
    # Группируем по ЕНП и группе заболевания
    result_data = []
    
    for (enp, disease_group), group_df in df_filtered.groupby(['enp', 'disease_group']):
        # Фильтруем только оплаченные талоны (статус 3)
        paid_talons = group_df[group_df['status'] == '3'].copy()
        
        if paid_talons.empty:
            # Если нет оплаченных талонов, берем последнюю запись
            latest_record = group_df.iloc[0]
            last_paid_visit = None
            planned_visit = None
            days_until_planned = None
            status = 'Нет оплаченных талонов'
        else:
            # Сортируем оплаченные талоны по дате окончания лечения
            paid_talons = paid_talons.sort_values('treatment_end', ascending=False)
            latest_paid_record = paid_talons.iloc[0]
            
            # Вычисляем плановую дату следующей явки (через год после последней оплаченной)
            last_paid_visit = latest_paid_record['treatment_end']
            if pd.notna(last_paid_visit):
                planned_visit = last_paid_visit + timedelta(days=365)
                days_until_planned = (planned_visit.date() - date.today()).days
                
                # Определяем статус
                if days_until_planned < 0:
                    status = 'Просрочено'
                elif days_until_planned <= 30:
                    status = 'Скоро'
                else:
                    status = 'В срок'
            else:
                planned_visit = None
                days_until_planned = None
                status = 'Дата не определена'
            
            # Берем последнюю запись для отображения основной информации
            latest_record = group_df.iloc[0]
        
        result_data.append({
            'enp': enp,
            'patient': latest_record['patient'],
            'birth_date': latest_record['birth_date'].strftime('%d.%m.%Y') if pd.notna(latest_record['birth_date']) else '',
            'disease_group': disease_group,
            'diagnosis_code': latest_record['main_diagnosis_code'],
            'last_paid_visit': last_paid_visit.strftime('%d.%m.%Y') if pd.notna(last_paid_visit) else 'Нет оплаченных',
            'planned_visit': planned_visit.strftime('%d.%m.%Y') if planned_visit else '',
            'days_until_planned': days_until_planned,
            'building': latest_record['building'],
            'doctor': latest_record['doctor'],
            'specialty': latest_record['specialty'],
            'talon': latest_record['talon'],
            'status': status
        })
    
    return pd.DataFrame(result_data)

def fast_search_patients(df, search_term):
    """Оптимизированный поиск пациентов"""
    if not search_term or len(search_term.strip()) < 2:
        return df.head(0)  # Пустой результат для коротких запросов
    
    search_term = search_term.strip()
    search_term_lower = search_term.lower()
    
    # Создаем временные поля для поиска
    df_search = df.copy()
    df_search['enp_str'] = df_search['enp'].astype(str)
    df_search['talon_str'] = df_search['talon'].astype(str)
    df_search['patient_lower'] = df_search['patient'].str.lower()
    
    # Сначала ищем точное совпадение по ЕНП
    enp_mask = df_search['enp_str'].str.contains(search_term, na=False)
    if enp_mask.any():
        return df[enp_mask].head(50)  # Ограничиваем результат
    
    # Потом по номеру талона
    talon_mask = df_search['talon_str'].str.contains(search_term, na=False)
    if talon_mask.any():
        return df[talon_mask].head(50)
    
    # В конце по ФИО (только если больше 2 символов)
    if len(search_term) >= 3:
        patient_mask = df_search['patient_lower'].str.contains(search_term_lower, na=False)
        if patient_mask.any():
            return df[patient_mask].head(50)
    
    return df.head(0)

def get_talons_cached(enp, disease_group, diagnosis_code):
    """Получает талоны с кэшированием"""
    cache_key = f"{enp}_{diagnosis_code}"
    
    if cache_key in _talons_cache:
        return _talons_cache[cache_key]
    
    talons_df = get_talons_by_direction(enp, disease_group, diagnosis_code)
    _talons_cache[cache_key] = talons_df
    
    # Ограничиваем размер кэша
    if len(_talons_cache) > 100:
        # Удаляем самые старые записи
        oldest_key = next(iter(_talons_cache))
        del _talons_cache[oldest_key]
    
    return talons_df

def update_data():
    """Обновляет данные школ здоровья с кэшированием"""
    global _df_processed_cache, _last_data_load_time
    
    current_time = time.time()
    
    # Кэшируем данные на 5 минут
    if (_df_processed_cache is not None and 
        current_time - _last_data_load_time < 300):  # 5 минут
        return _df_processed_cache
    
    try:
        df_raw = get_health_schools_data()
        if df_raw.empty:
            _df_processed_cache = pd.DataFrame()
            return _df_processed_cache
        
        _df_processed_cache = process_health_schools_data(df_raw)
        _last_data_load_time = current_time
        return _df_processed_cache
    except Exception as e:
        print(f"Ошибка обновления данных: {e}")
        _df_processed_cache = pd.DataFrame()
        return _df_processed_cache

def build_search_card():
    """Создает карточку поиска пациентов"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("🔍 Поиск пациентов", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Поиск по ФИО, ЕНП или номеру талона:", style={"font-weight": "bold"}),
                    dbc.InputGroup([
                        dbc.Input(
                            id=f"search-input-{type_page}",
                            placeholder="Введите ФИО, ЕНП или номер талона...",
                            type="text"
                        ),
                        dbc.Button(
                            "Найти пациентов",
                            id=f"search-patients-button-{type_page}",
                            color="primary",
                            n_clicks=0
                        )
                    ])
                ], width=12, md=8),
                dbc.Col([
                    dbc.Button(
                        "Очистить поиск",
                        id=f"clear-button-{type_page}",
                        color="secondary",
                        outline=True,
                        className="mt-4"
                    )
                ], width=12, md=4)
            ], className="mb-3")
        ])
    ], className="mb-4")

def build_patient_selection_card():
    """Создает карточку выбора пациента"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("👥 Выберите пациента", className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id=f"patients-list-container-{type_page}")
        ])
    ], className="mb-4")

def build_records_filter_card():
    """Создает карточку фильтрации записей"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("🏥 Фильтр записей по школам здоровья", className="mb-0")
        ]),
        dbc.CardBody([
            html.Label("Группа заболевания:", style={"font-weight": "bold"}),
            dcc.Dropdown(
                id=f"disease-group-filter-{type_page}",
                options=[
                    {'label': 'Все группы', 'value': 'all'},
                    {'label': 'Артериальная гипертония', 'value': 'I1%'},
                    {'label': 'Сердечная недостаточность', 'value': 'I5%'},
                    {'label': 'Бронхиальная астма', 'value': 'J4%'},
                    {'label': 'Сахарный диабет', 'value': 'E1%'}
                ],
                value='all',
                clearable=False,
                className="mb-3"
            ),
            dbc.Button(
                "Показать записи",
                id=f"show-records-button-{type_page}",
                color="success",
                size="lg",
                className="w-100"
            )
        ])
    ], className="mb-4")

def build_stats_cards(df):
    """Создает карточки со статистикой"""
    if df.empty:
        return html.Div()
    
    total_patients = df['enp'].nunique()
    overdue_count = len(df[df['status'] == 'Просрочено'])
    soon_count = len(df[df['status'] == 'Скоро'])
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_patients, className="text-primary mb-0"),
                    html.P("Всего пациентов", className="text-muted mb-0")
                ])
            ], className="text-center")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(overdue_count, className="text-danger mb-0"),
                    html.P("Просрочено явок", className="text-muted mb-0")
                ])
            ], className="text-center")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(soon_count, className="text-warning mb-0"),
                    html.P("Скоро явка", className="text-muted mb-0")
                ])
            ], className="text-center")
        ], width=4)
    ], className="mb-4")

def build_patients_list(patients_df, search_term=""):
    """Создает список найденных пациентов"""
    if patients_df.empty:
        return dbc.Alert([
            html.I(className="fas fa-search me-2"),
            f"По запросу '{search_term}' пациенты не найдены. Попробуйте изменить поисковый запрос."
        ], color="warning", className="text-center")
    
    # Группируем по ЕНП и берем уникальных пациентов
    unique_patients = patients_df.groupby('enp').first().reset_index()
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-users me-2"),
                f"Найдено пациентов: {len(unique_patients)}"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dash_table.DataTable(
                id=f"patients-list-{type_page}",
                data=unique_patients[['patient', 'enp', 'birth_date']].to_dict('records'),
                columns=[
                    {"name": "ФИО", "id": "patient", "type": "text"},
                    {"name": "ЕНП", "id": "enp", "type": "text"},
                    {"name": "Дата рождения", "id": "birth_date", "type": "text"}
                ],
                page_size=10,
                sort_action="native",
                style_cell={
                    "textAlign": "left",
                    "minWidth": "150px",
                    "whiteSpace": "normal",
                    "fontSize": "12px"
                },
                style_header={
                    "fontWeight": "bold",
                    "backgroundColor": "#f8f9fa"
                },
                row_selectable="single",
                selected_rows=[],
                style_data_conditional=[
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#e3f2fd',
                        'border': '1px solid #2196f3'
                    }
                ]
            )
        ])
    ], className="mb-4")

def build_patient_records_table(records_df):
    """Создает таблицу с записями выбранного пациента"""
    if records_df.empty:
        return dbc.Alert("Записи не найдены", color="info")
    
    # Сортируем по статусу и дате плановой явки
    records_df_sorted = records_df.sort_values(['status', 'planned_visit'], ascending=[True, True])
    
    return dash_table.DataTable(
        id=f"patient-records-table-{type_page}",
        data=records_df_sorted.to_dict('records'),
        columns=[
            {"name": "Группа заболевания", "id": "disease_group", "type": "text"},
            {"name": "Последняя оплаченная явка", "id": "last_paid_visit", "type": "text"},
            {"name": "Плановая явка", "id": "planned_visit", "type": "text"},
            {"name": "Дней до явки", "id": "days_until_planned", "type": "numeric"},
            {"name": "Статус", "id": "status", "type": "text"},
            {"name": "Корпус", "id": "building", "type": "text"},
            {"name": "Врач", "id": "doctor", "type": "text"},
            {"name": "Специальность", "id": "specialty", "type": "text"}
        ],
        page_size=20,
        sort_action="native",
        filter_action="native",
        style_cell={
            "textAlign": "left",
            "minWidth": "120px",
            "maxWidth": "200px",
            "whiteSpace": "normal",
            "fontSize": "12px"
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#f8f9fa"
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{status} = Просрочено'},
                'backgroundColor': '#ffebee',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{status} = Скоро'},
                'backgroundColor': '#fff3e0',
                'color': 'black',
            }
        ],
        export_format="xlsx",
        style_table={
            "height": "400px",
            "overflowY": "auto",
            "overflowX": "auto",
            "border": "1px solid #dee2e6",
            "borderRadius": "0.375rem"
        },
        fixed_rows={"headers": True}
    )

def get_talons_by_direction(enp, disease_group, diagnosis_code):
    """Получает все талоны по направлению для конкретного пациента"""
    query = """
    SELECT 
        talon,
        treatment_start,
        treatment_end,
        main_diagnosis_code,
        status,
        building,
        doctor,
        specialty
    FROM load_data_oms_data 
    WHERE enp = '{}' AND goal = '307' AND main_diagnosis_code = '{}'
    ORDER BY treatment_end DESC
    """
    
    try:
        # Формируем запрос с конкретным диагнозом
        formatted_query = query.format(enp, diagnosis_code)
        result = execute_query(formatted_query)
        
        if not result:
            return pd.DataFrame()
        
        columns = ['talon', 'treatment_start', 'treatment_end', 'main_diagnosis_code', 
                  'status', 'building', 'doctor', 'specialty']
        df = pd.DataFrame(result, columns=columns)
        
        # Преобразуем даты
        df['treatment_start'] = pd.to_datetime(df['treatment_start'], errors='coerce')
        df['treatment_end'] = pd.to_datetime(df['treatment_end'], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Ошибка получения талонов: {e}")
        return pd.DataFrame()

def build_talons_table(talons_df):
    """Создает таблицу с талонами"""
    if talons_df.empty:
        return dbc.Alert("Талонов не найдено", color="info")
    
    # Форматируем даты
    talons_df = talons_df.copy()
    talons_df['treatment_start'] = talons_df['treatment_start'].dt.strftime('%d.%m.%Y') if not talons_df['treatment_start'].isna().all() else ''
    talons_df['treatment_end'] = talons_df['treatment_end'].dt.strftime('%d.%m.%Y') if not talons_df['treatment_end'].isna().all() else ''
    
    return dash_table.DataTable(
        id=f"talons-table-{type_page}",
        data=talons_df.to_dict('records'),
        columns=[
            {"name": "Номер талона", "id": "talon", "type": "text"},
            {"name": "Дата начала лечения", "id": "treatment_start", "type": "text"},
            {"name": "Дата окончания лечения", "id": "treatment_end", "type": "text"},
            {"name": "Диагноз", "id": "main_diagnosis_code", "type": "text"},
            {"name": "Статус", "id": "status", "type": "text"},
            {"name": "Корпус", "id": "building", "type": "text"},
            {"name": "Врач", "id": "doctor", "type": "text"},
            {"name": "Специальность", "id": "specialty", "type": "text"}
        ],
        page_size=10,
        sort_action="native",
        style_cell={
            "textAlign": "left",
            "minWidth": "120px",
            "maxWidth": "200px",
            "whiteSpace": "normal",
            "fontSize": "12px"
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#f8f9fa"
        },
        style_table={
            "height": "300px",
            "overflowY": "auto",
            "overflowX": "auto",
            "border": "1px solid #dee2e6",
            "borderRadius": "0.375rem"
        },
        fixed_rows={"headers": True}
    )

# Layout страницы
health_schools_page = html.Div([
    # Заголовок
    dbc.Row([
        dbc.Col([
            html.H2("🏥 Анализ школ здоровья", className="mb-4"),
            html.P("Система отслеживания плановых явок пациентов в школах здоровья", 
                   className="text-muted mb-4")
        ], width=12)
    ], className="px-3"),
    
    # Карточка поиска
    dbc.Row([
        dbc.Col([
            build_search_card()
        ], width=12)
    ], className="px-3"),
    
    # Карточка выбора пациента и фильтрации записей
    dbc.Row([
        dbc.Col([
            build_patient_selection_card()
        ], width=12, md=6),
        dbc.Col([
            build_records_filter_card()
        ], width=12, md=6)
    ], className="px-3"),
    
    # Записи выбранного пациента
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("📋 Записи выбранного пациента", className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id=f"patient-records-container-{type_page}")
                ])
            ])
        ], width=12)
    ], className="px-3"),
    
    # Талоны по выбранной записи
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🎫 Талоны по выбранному направлению", className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id=f"talons-container-{type_page}")
                ])
            ])
        ], width=12)
    ], className="px-3")
])

# Callback для показа спиннера при поиске
@app.callback(
    Output(f"patients-list-container-{type_page}", "children"),
    Input(f"search-patients-button-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def show_search_loading(n_clicks):
    if n_clicks:
        return dbc.Card([
            dbc.CardBody([
                dbc.Spinner(
                    html.Div([
                        html.I(className="fas fa-search me-2"),
                        "Поиск пациентов...",
                        html.Br(),
                        html.Small("Пожалуйста, подождите", className="text-muted")
                    ], className="text-center"),
                    size="lg",
                    color="primary"
                )
            ])
        ], className="mb-4")
    raise PreventUpdate

# Callback для поиска пациентов
@app.callback(
    Output(f"patients-list-container-{type_page}", "children", allow_duplicate=True),
    Input(f"search-patients-button-{type_page}", "n_clicks"),
    Input(f"clear-button-{type_page}", "n_clicks"),
    State(f"search-input-{type_page}", "value"),
    prevent_initial_call=True
)
def search_patients(search_clicks, clear_clicks, search_term):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Очистка поиска
    if trigger_id == f"clear-button-{type_page}":
        return html.Div()
    
    # Поиск пациентов только по кнопке
    if trigger_id == f"search-patients-button-{type_page}":
        if not search_term or len(search_term.strip()) < 2:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Введите минимум 2 символа для поиска"
            ], color="warning", className="text-center")
        
        try:
            # Получаем данные с кэшированием
            df_processed = update_data()
            if df_processed.empty:
                return dbc.Alert([
                    html.I(className="fas fa-database me-2"),
                    "Данные не найдены в базе данных"
                ], color="danger", className="text-center")
            
            # Оптимизированный поиск
            found_patients = fast_search_patients(df_processed, search_term)
            
            # Строим список пациентов с передачей поискового запроса
            patients_list = build_patients_list(found_patients, search_term)
            
            return patients_list
            
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Ошибка при поиске: {str(e)}"
            ], color="danger", className="text-center")
    
    return no_update

# Callback для показа спиннера при загрузке записей
@app.callback(
    Output(f"patient-records-container-{type_page}", "children"),
    Input(f"show-records-button-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def show_records_loading(n_clicks):
    if n_clicks:
        return dbc.Card([
            dbc.CardBody([
                dbc.Spinner(
                    html.Div([
                        html.I(className="fas fa-file-medical me-2"),
                        "Загрузка записей пациента...",
                        html.Br(),
                        html.Small("Пожалуйста, подождите", className="text-muted")
                    ], className="text-center"),
                    size="lg",
                    color="success"
                )
            ])
        ])
    raise PreventUpdate

# Callback для показа записей выбранного пациента
@app.callback(
    Output(f"patient-records-container-{type_page}", "children", allow_duplicate=True),
    Output(f"talons-container-{type_page}", "children"),
    Input(f"show-records-button-{type_page}", "n_clicks"),
    Input(f"patients-list-{type_page}", "selected_rows"),
    State(f"patients-list-{type_page}", "data"),
    State(f"disease-group-filter-{type_page}", "value"),
    prevent_initial_call=True
)
def show_patient_records(show_clicks, selected_rows, patients_data, disease_filter):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Если нажата кнопка "Показать записи"
    if trigger_id == f"show-records-button-{type_page}":
        if not selected_rows or not patients_data:
            return dbc.Alert([
                html.I(className="fas fa-user-plus me-2"),
                "Сначала выберите пациента из списка выше"
            ], color="warning", className="text-center"), html.Div()
        
        try:
            # Получаем данные выбранного пациента
            selected_patient = patients_data[selected_rows[0]]
            selected_enp = selected_patient['enp']
            
            # Получаем все данные
            df_processed = update_data()
            if df_processed.empty:
                return dbc.Alert([
                    html.I(className="fas fa-database me-2"),
                    "Данные не найдены в базе данных"
                ], color="danger", className="text-center"), html.Div()
            
            # Фильтруем по выбранному пациенту
            patient_records = df_processed[df_processed['enp'] == selected_enp]
            
            if patient_records.empty:
                return dbc.Alert([
                    html.I(className="fas fa-user-times me-2"),
                    f"Записи для пациента {selected_patient['patient']} не найдены"
                ], color="info", className="text-center"), html.Div()
            
            # Применяем фильтр по группе заболевания
            if disease_filter != 'all':
                patient_records = patient_records[patient_records['disease_group'] == DISEASE_GROUPS[disease_filter]]
            
            if patient_records.empty:
                return dbc.Alert([
                    html.I(className="fas fa-filter me-2"),
                    f"Записи для пациента {selected_patient['patient']} в группе '{DISEASE_GROUPS[disease_filter]}' не найдены"
                ], color="info", className="text-center"), html.Div()
            
            # Строим таблицу записей
            records_table = build_patient_records_table(patient_records)
            
            return html.Div([
                html.H6([
                    html.I(className="fas fa-user me-2"),
                    f"Пациент: {selected_patient['patient']} (ЕНП: {selected_enp})"
                ], className="mb-3"),
                records_table
            ]), html.Div()
            
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Ошибка при загрузке записей: {str(e)}"
            ], color="danger", className="text-center"), html.Div()
    
    return no_update, no_update

# Callback для показа талонов при клике на запись
@app.callback(
    Output(f"talons-container-{type_page}", "children", allow_duplicate=True),
    Input(f"patient-records-table-{type_page}", "active_cell"),
    State(f"patient-records-table-{type_page}", "data"),
    State(f"patients-list-{type_page}", "selected_rows"),
    State(f"patients-list-{type_page}", "data"),
    prevent_initial_call=True
)
def show_talons_for_record(active_cell, records_data, selected_patient_rows, patients_data):
    if not active_cell or not records_data or not selected_patient_rows or not patients_data:
        return html.Div()
    
    # Получаем данные выбранного пациента
    selected_patient = patients_data[selected_patient_rows[0]]
    selected_enp = selected_patient['enp']
    
    # Получаем выбранную запись
    selected_record = records_data[active_cell['row']]
    disease_group = selected_record['disease_group']
    diagnosis_code = selected_record['diagnosis_code']
    
    # Получаем талоны по направлению с кэшированием
    talons_df = get_talons_cached(selected_enp, disease_group, diagnosis_code)
    
    if talons_df.empty:
        return dbc.Alert([
            html.I(className="fas fa-file-medical-alt me-2"),
            f"Талонов по направлению '{disease_group}' не найдено"
        ], color="info", className="text-center")
    
    # Строим таблицу талонов
    talons_table = build_talons_table(talons_df)
    
    return html.Div([
        html.H6([
            html.I(className="fas fa-ticket-alt me-2"),
            f"Талоны по направлению: {disease_group}"
        ], className="mb-3"),
        talons_table
    ])

# Callback для очистки поля поиска
@app.callback(
    Output(f"search-input-{type_page}", "value"),
    Input(f"clear-button-{type_page}", "n_clicks"),
    prevent_initial_call=True
)
def clear_search(clear_clicks):
    if clear_clicks:
        return ""
    raise PreventUpdate
