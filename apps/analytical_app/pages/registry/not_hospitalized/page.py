from dash import dcc, html, Output, Input, State, ctx, no_update
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
        if ip in ["127.0.0.1", "localhost", "0.0.0.0"]:
            return f"http://127.0.0.1:{port}/api/patient_registry/"
        return f"http://{ip}:{port}/api/patient_registry/"
    return "#"


def get_update_url():
    query = "SELECT main_app_ip, main_app_port FROM home_mainsettings LIMIT 1"
    result = execute_query(query)
    if result:
        ip, port = result[0]
        return f"http://{ip}:{port}/api/update_registry/"
    return "#"


def fetch_data():
    try:
        api_url = get_api_url()
        response = requests.get(api_url, proxies={"http": None, "https": None})
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_unique_values(column_name):
    df = fetch_data()
    if column_name in df.columns:
        return [{"label": val, "value": val} for val in df[column_name].dropna().unique()]
    return []


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
                            dbc.Row([
                                dbc.Col(html.Label("Прикрепление к МО:"), width=2),
                                dbc.Col(dcc.Dropdown(id='filter-medical-organization', placeholder="Выберите МО"),
                                        width=4),
                                dbc.Col(html.Label("Наименование стационара:"), width=2),
                                dbc.Col(dcc.Dropdown(id='filter-hospital-name', placeholder="Выберите стационар"),
                                        width=4),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col(html.Label("Причина отказа:"), width=2),
                                dbc.Col(dcc.Dropdown(id='filter-reason', placeholder="Выберите причину отказа"),
                                        width=4),
                                dbc.Col(html.Label("Способ обращения:"), width=2),
                                dbc.Col(dcc.Dropdown(id='filter-method', placeholder="Выберите способ обращения"),
                                        width=4),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col(html.Button("Применить фильтры", id='apply-filters', n_clicks=0,
                                                    className="btn btn-primary"), width=2),
                                dbc.Col(html.Button("Очистить фильтры", id='clear-filters', n_clicks=0,
                                                    className="btn btn-secondary"), width=2),
                                dbc.Col(html.Button("Обновить данные", id='refresh-data', n_clicks=0,
                                                    className="btn btn-info"), width=2),
                                dbc.Col(dbc.Alert(id='refresh-status', dismissable=True, is_open=False), width=6),
                            ], className="mb-3"),
                        ]
                    )
                ), width=12
            )
        ),
        dcc.Loading(id='loading-nothospitalized', type='circle'),
        card_table(f'result-table-{type_page}', "Регистр не госпитализированных пациентов", page_size=15),
    ],
    style={"padding": "20px"}
)


# Callback для обновления фильтров при загрузке страницы и обновлении данных
@app.callback(
    Output('filter-medical-organization', 'options'),
    Output('filter-hospital-name', 'options'),
    Output('filter-reason', 'options'),
    Output('filter-method', 'options'),
    Output('refresh-status', 'is_open'),
    Output('refresh-status', 'children'),
    Input('refresh-data', 'n_clicks'),
    prevent_initial_call=False
)
def update_filters_and_notification(refresh_clicks):
    df = fetch_data()

    medical_organizations = [{"label": val, "value": val} for val in sorted(df['medical_organization'].dropna().unique())]
    hospital_names = [{"label": val, "value": val} for val in sorted(df['hospital_name'].dropna().unique())]
    refusal_reasons = [{"label": val, "value": val} for val in sorted(df['refusal_reason'].dropna().unique())]
    referral_methods = [{"label": val, "value": val} for val in sorted(df['referral_method'].dropna().unique())]

    if refresh_clicks:
        try:
            update_url = get_update_url()
            response = requests.get(update_url, proxies={"http": None, "https": None})
            response_data = response.json()
            if response.status_code == 200 and response_data.get("status") == "success":
                return medical_organizations, hospital_names, refusal_reasons, referral_methods, True, "Данные успешно обновлены!"
            else:
                return medical_organizations, hospital_names, refusal_reasons, referral_methods, True, f"Ошибка обновления: {response_data.get('message')}"
        except requests.exceptions.RequestException as e:
            return medical_organizations, hospital_names, refusal_reasons, referral_methods, True, f"Ошибка соединения: {str(e)}"

    return medical_organizations, hospital_names, refusal_reasons, referral_methods, False, ""


# Callback для очистки таблицы и применения фильтров
@app.callback(
    Output(f'result-table-{type_page}', 'data'),
    Output(f'result-table-{type_page}', 'columns'),
    Output('filter-medical-organization', 'value'),
    Output('filter-hospital-name', 'value'),
    Output('filter-reason', 'value'),
    Output('filter-method', 'value'),
    Input('apply-filters', 'n_clicks'),
    Input('clear-filters', 'n_clicks'),
    State('filter-medical-organization', 'value'),
    State('filter-hospital-name', 'value'),
    State('filter-reason', 'value'),
    State('filter-method', 'value'),
)
def update_table(apply_clicks, clear_clicks, medical_org, hospital_name, reason, method):
    triggered_id = ctx.triggered_id

    if triggered_id == 'clear-filters':
        return [], [], None, None, None, None

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

        df.rename(columns={
            "number": "№", "full_name": "ФИО",
            "date_of_birth": "Дата рождения",
            "address": "Адрес", "phone": "Телефон",
            "medical_organization": "Прикрепление к МО",
            "hospital_name": "Наименование стационара",
            "admission_date": "Дата обращения",
            "referral_method": "Способ обращения",
            "refusal_reason": "Причина отказа"
        }, inplace=True)

    columns = [{"name": col, "id": col} for col in df.columns]
    return df.to_dict('records'), columns, medical_org, hospital_name, reason, method
