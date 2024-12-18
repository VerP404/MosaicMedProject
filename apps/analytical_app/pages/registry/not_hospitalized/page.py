from dash import dcc, html, Output, Input, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import requests
from apps.analytical_app.app import app
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import execute_query


# URL API


def get_api_url():
    query = "SELECT main_app_ip, main_app_port FROM home_mainsettings LIMIT 1"
    result = execute_query(query)
    if result:
        ip, port = result[0]
        return f"http://{ip}:{port}/api/patient_registry/"
    return "#"


# Функция для получения данных из API
def fetch_data():
    try:
        response = requests.get(get_api_url(), timeout=10)
        response.raise_for_status()  # Проверка успешности запроса
        data = response.json()

        if isinstance(data, list) and data:  # Проверка на непустой список
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()  # Возвращаем пустой DataFrame
    except Exception as e:
        return pd.DataFrame()  # Возвращаем пустой DataFrame при ошибке


# Функция для получения уникальных значений из столбцов
def get_unique_values(column_name):
    df = fetch_data()
    if column_name in df.columns:  # Проверяем наличие столбца
        return [{"label": val, "value": val} for val in df[column_name].dropna().unique()]
    return []  # Возвращаем пустой список, если столбца нет


# Тип страницы
type_page = "registry-nothospitalized"

# Layout страницы
not_hospitalized_page = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),

                            # Фильтры: МО, Наименование стационара, Причина отказа, Способ обращения
                            dbc.Row([
                                dbc.Col(html.Label("Прикрепление к МО:"), width=2),
                                dbc.Col(dcc.Dropdown(
                                    id='filter-medical-organization',
                                    options=get_unique_values('medical_organization'),
                                    placeholder="Выберите МО"
                                ), width=4),

                                dbc.Col(html.Label("Наименование стационара:"), width=2),
                                dbc.Col(dcc.Dropdown(
                                    id='filter-hospital-name',
                                    options=get_unique_values('hospital_name'),
                                    placeholder="Выберите стационар"
                                ), width=4),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col(html.Label("Причина отказа:"), width=2),
                                dbc.Col(dcc.Dropdown(
                                    id='filter-reason',
                                    options=[
                                        {"label": "Нет показаний для госпитализации",
                                         "value": "Нет показаний для госпитализации"},
                                        {"label": "Отказ пациента", "value": "Отказ пациента (законного представителя)"}
                                    ],
                                    placeholder="Выберите причину отказа"
                                ), width=4),

                                dbc.Col(html.Label("Способ обращения:"), width=2),
                                dbc.Col(dcc.Dropdown(
                                    id='filter-method',
                                    options=[
                                        {"label": "ССМП", "value": "ССМП"},
                                        {"label": "Самообращение", "value": "Самообращение"}
                                    ],
                                    placeholder="Выберите способ обращения"
                                ), width=4),
                            ], className="mb-3"),

                            # Периоды поступления и отказа
                            dbc.Row([
                                dbc.Col(html.Label("Период поступления:"), width=2),
                                dbc.Col(dcc.DatePickerRange(
                                    id='filter-admission-date',
                                    display_format="YYYY-MM-DD",
                                    start_date_placeholder_text="Начало",
                                    end_date_placeholder_text="Конец",
                                ), width=4),

                                dbc.Col(html.Label("Период отказа:"), width=2),
                                dbc.Col(dcc.DatePickerRange(
                                    id='filter-refusal-date',
                                    display_format="YYYY-MM-DD",
                                    start_date_placeholder_text="Начало",
                                    end_date_placeholder_text="Конец",
                                ), width=4),
                            ], className="mb-3"),

                            # Кнопки фильтров
                            dbc.Row([
                                dbc.Col(html.Button("Применить фильтры", id='apply-filters', n_clicks=0,
                                                    className="btn btn-primary"), width=2),
                                dbc.Col(html.Button("Очистить фильтры", id='clear-filters', n_clicks=0,
                                                    className="btn btn-secondary"), width=2),
                            ], className="mb-3"),
                        ]
                    )
                ), width=12
            )
        ),
        card_table(f'result-table-{type_page}', "Регистр не госпитализированных пациентов", page_size=15),
        dcc.Loading(id='loading-nothospitalized', type='default'),
    ],
    style={"padding": "20px"}
)


# Callback для обновления таблицы и очистки фильтров
@app.callback(
    Output(f'result-table-{type_page}', 'data'),
    Output(f'result-table-{type_page}', 'columns'),
    Output('filter-medical-organization', 'value'),
    Output('filter-hospital-name', 'value'),
    Output('filter-reason', 'value'),
    Output('filter-method', 'value'),
    Output('filter-admission-date', 'start_date'),
    Output('filter-admission-date', 'end_date'),
    Output('filter-refusal-date', 'start_date'),
    Output('filter-refusal-date', 'end_date'),
    Input('apply-filters', 'n_clicks'),
    Input('clear-filters', 'n_clicks'),
    State('filter-medical-organization', 'value'),
    State('filter-hospital-name', 'value'),
    State('filter-reason', 'value'),
    State('filter-method', 'value'),
    State('filter-admission-date', 'start_date'),
    State('filter-admission-date', 'end_date'),
    State('filter-refusal-date', 'start_date'),
    State('filter-refusal-date', 'end_date'),
)
def update_table(apply_clicks, clear_clicks, medical_org, hospital_name, reason, method,
                 admission_start, admission_end, refusal_start, refusal_end):
    triggered_id = ctx.triggered_id  # Определяем, какая кнопка нажата

    # Если нажата кнопка "Очистить фильтры", сбрасываем все значения
    if triggered_id == 'clear-filters':
        return [], [], None, None, None, None, None, None, None, None

    # В противном случае применяем фильтры
    df = fetch_data()

    if not df.empty:
        if medical_org:
            df = df[df['medical_organization'] == medical_org]
        if hospital_name:
            df = df[df['hospital_name'] == hospital_name]
        if reason:
            df = df[df['refusal_reason'] == reason]
        if method:
            df = df[df['referral_method'] == method]
        if admission_start and admission_end:
            df = df[(df['admission_date'] >= admission_start) & (df['admission_date'] <= admission_end)]
        if refusal_start and refusal_end:
            df = df[(df['refusal_date'] >= refusal_start) & (df['refusal_date'] <= refusal_end)]

        # Переименовываем столбцы
        rename_columns = {
            "number": "№",
            "full_name": "ФИО",
            "date_of_birth": "Дата рождения",
            "address": "Адрес",
            "phone": "Телефон",
            "medical_organization": "Прикрепление к МО",
            "hospital_name": "Наименование стационара",
            "admission_date": "Дата обращения",
            "referral_method": "Способ обращения",
            "admission_diagnosis": "Диагноз при поступлении",
            "refusal_date": "Дата отказа",
            "refusal_reason": "Причина отказа",
        }

        df = df.drop(columns=['id'], errors='ignore')  # Удаляем поле id
        df.rename(columns=rename_columns, inplace=True)

    columns = [{"name": col, "id": col} for col in df.columns]
    # Возвращаем текущие значения фильтров
    return (
        df.to_dict('records'),
        columns,
        medical_org,
        hospital_name,
        reason,
        method,
        admission_start,
        admission_end,
        refusal_start,
        refusal_end
    )
