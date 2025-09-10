# -*- coding: utf-8 -*-
"""
АНАЛИЗ ШКОЛ ЗДОРОВЬЯ
Dash-приложение для анализа школ здоровья пациентов
Отслеживание плановых явок по группам заболеваний
"""

import pandas as pd
from datetime import datetime, date, timedelta
from dash import html, dcc, Input, Output, State, callback_context, dash_table, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.query_executor import execute_query

type_page = "health_schools"

# Определение групп заболеваний
DISEASE_GROUPS = {
    'I1%': 'Артериальная гипертония',
    'I5%': 'Сердечная недостаточность', 
    'J4%': 'Бронхиальная астма',
    'E1%': 'Сахарный диабет'
}

def get_health_schools_data():
    """Получает данные школ здоровья из базы данных"""
    query = """
    SELECT 
        enp,
        patient,
        birth_date,
        treatment_end,
        main_diagnosis_code,
        goal,
        department,
        doctor,
        specialty
    FROM load_data_oms_data 
    WHERE goal = '307'
    ORDER BY enp, treatment_end DESC
    """
    
    try:
        result = execute_query(query)
        
        if not result:
            return pd.DataFrame()
        
        # Преобразуем результат в DataFrame
        columns = ['enp', 'patient', 'birth_date', 'treatment_end', 'main_diagnosis_code', 
                  'goal', 'department', 'doctor', 'specialty']
        df = pd.DataFrame(result, columns=columns)
        
        # Преобразуем даты
        df['treatment_end'] = pd.to_datetime(df['treatment_end'], errors='coerce')
        df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
        
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
    
    # Группируем по ЕНП и группе заболевания
    result_data = []
    
    for (enp, disease_group), group_df in df_filtered.groupby(['enp', 'disease_group']):
        # Берем последнюю запись для каждого пациента в каждой группе
        latest_record = group_df.iloc[0]
        
        # Вычисляем плановую дату следующей явки (через год)
        last_visit = latest_record['treatment_end']
        if pd.notna(last_visit):
            planned_visit = last_visit + timedelta(days=365)
            days_until_planned = (planned_visit.date() - date.today()).days
        else:
            planned_visit = None
            days_until_planned = None
        
        result_data.append({
            'enp': enp,
            'patient': latest_record['patient'],
            'birth_date': latest_record['birth_date'].strftime('%d.%m.%Y') if pd.notna(latest_record['birth_date']) else '',
            'disease_group': disease_group,
            'last_visit': last_visit.strftime('%d.%m.%Y') if pd.notna(last_visit) else '',
            'planned_visit': planned_visit.strftime('%d.%m.%Y') if planned_visit else '',
            'days_until_planned': days_until_planned,
            'department': latest_record['department'],
            'doctor': latest_record['doctor'],
            'specialty': latest_record['specialty'],
            'status': 'Просрочено' if days_until_planned and days_until_planned < 0 else 
                     'Скоро' if days_until_planned and days_until_planned <= 30 else 
                     'В срок' if days_until_planned else 'Не определено'
        })
    
    return pd.DataFrame(result_data)

def build_search_card():
    """Создает карточку поиска пациентов"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("🔍 Поиск пациентов", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Поиск по ФИО или ЕНП:", style={"font-weight": "bold"}),
                    dbc.InputGroup([
                        dbc.Input(
                            id=f"search-input-{type_page}",
                            placeholder="Введите ФИО или ЕНП...",
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
            dbc.Row([
                dbc.Col([
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
                        clearable=False
                    )
                ], width=12, md=6),
                dbc.Col([
                    dbc.Button(
                        "Показать записи",
                        id=f"show-records-button-{type_page}",
                        color="success",
                        className="mt-4"
                    )
                ], width=12, md=6)
            ])
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

def build_patients_list(patients_df):
    """Создает список найденных пациентов"""
    if patients_df.empty:
        return dbc.Alert("Пациенты не найдены", color="info")
    
    # Группируем по ЕНП и берем уникальных пациентов
    unique_patients = patients_df.groupby('enp').first().reset_index()
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5(f"👥 Найдено пациентов: {len(unique_patients)}", className="mb-0")
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
            {"name": "Последняя явка", "id": "last_visit", "type": "text"},
            {"name": "Плановая явка", "id": "planned_visit", "type": "text"},
            {"name": "Дней до явки", "id": "days_until_planned", "type": "numeric"},
            {"name": "Статус", "id": "status", "type": "text"},
            {"name": "Отделение", "id": "department", "type": "text"},
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
    
    # Карточка выбора пациента
    dbc.Row([
        dbc.Col([
            build_patient_selection_card()
        ], width=12)
    ], className="px-3"),
    
    # Карточка фильтрации записей
    dbc.Row([
        dbc.Col([
            build_records_filter_card()
        ], width=12)
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
    ], className="px-3")
])

# Callback для поиска пациентов
@app.callback(
    Output(f"patients-list-container-{type_page}", "children"),
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
    
    # Поиск пациентов
    if trigger_id == f"search-patients-button-{type_page}":
        if not search_term or len(search_term.strip()) < 2:
            return dbc.Alert("Введите минимум 2 символа для поиска", color="warning")
        
        # Получаем данные
        df_raw = get_health_schools_data()
        if df_raw.empty:
            return dbc.Alert("Данные не найдены в базе данных", color="info")
        
        df_processed = process_health_schools_data(df_raw)
        if df_processed.empty:
            return dbc.Alert("Нет данных по школам здоровья", color="info")
        
        # Поиск по ФИО или ЕНП
        search_term_lower = search_term.lower()
        mask = (
            df_processed['patient'].str.lower().str.contains(search_term_lower, na=False) |
            df_processed['enp'].str.contains(search_term, na=False)
        )
        found_patients = df_processed[mask]
        
        if found_patients.empty:
            return dbc.Alert("Пациенты не найдены", color="info")
        
        # Строим список пациентов
        patients_list = build_patients_list(found_patients)
        
        return patients_list
    
    return no_update

# Callback для показа записей выбранного пациента
@app.callback(
    Output(f"patient-records-container-{type_page}", "children"),
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
            return dbc.Alert("Сначала выберите пациента из списка", color="warning")
        
        # Получаем данные выбранного пациента
        selected_patient = patients_data[selected_rows[0]]
        selected_enp = selected_patient['enp']
        
        # Получаем все данные
        df_raw = get_health_schools_data()
        if df_raw.empty:
            return dbc.Alert("Данные не найдены", color="info")
        
        df_processed = process_health_schools_data(df_raw)
        if df_processed.empty:
            return dbc.Alert("Нет данных по школам здоровья", color="info")
        
        # Фильтруем по выбранному пациенту
        patient_records = df_processed[df_processed['enp'] == selected_enp]
        
        if patient_records.empty:
            return dbc.Alert(f"Записи для пациента {selected_patient['patient']} не найдены", color="info")
        
        # Применяем фильтр по группе заболевания
        if disease_filter != 'all':
            patient_records = patient_records[patient_records['disease_group'] == DISEASE_GROUPS[disease_filter]]
        
        if patient_records.empty:
            return dbc.Alert(f"Записи для пациента {selected_patient['patient']} в группе {DISEASE_GROUPS[disease_filter]} не найдены", color="info")
        
        # Строим таблицу записей
        records_table = build_patient_records_table(patient_records)
        
        return html.Div([
            html.H6(f"Пациент: {selected_patient['patient']} (ЕНП: {selected_enp})", className="mb-3"),
            records_table
        ])
    
    return no_update

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
