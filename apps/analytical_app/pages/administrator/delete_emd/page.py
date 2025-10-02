from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import requests
import json
from datetime import datetime, date
import os
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import io
import base64

from apps.analytical_app.app import app, DJANGO_API_BASE
from flask import request


def format_date_for_display(date_str):
    """Конвертирует дату из формата YYYY-MM-DD в DD.MM.YYYY"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date_obj = date_str
        return date_obj.strftime('%d.%m.%Y')
    except:
        return date_str


def format_date_for_api(date_str):
    """Конвертирует дату из формата DD.MM.YYYY в YYYY-MM-DD"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str) and '.' in date_str:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        else:
            date_obj = date_str
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str


# Универсальный конвертер в date для DatePickerSingle
def to_date_obj(value):
    """Принимает строки 'YYYY-MM-DD' или 'DD.MM.YYYY', а также date/None -> возвращает date или None"""
    if not value:
        return None
    try:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            if '.' in value:
                return datetime.strptime(value, '%d.%m.%Y').date()
            return datetime.strptime(value, '%Y-%m-%d').date()
        return value
    except:
        return None

# API функции
def resolve_api_base() -> str:
    """Определяет базовый URL Django API универсально.
    Приоритет:
    1) Явная переменная окружения DJANGO_API_BASE
    2) Текущий хост из запроса (X-Forwarded-Host/Proto учитываются) + порт из DJANGO_API_PORT (по умолчанию 8000)
    """
    explicit_base = os.getenv('DJANGO_API_BASE') or DJANGO_API_BASE
    if explicit_base:
        return explicit_base.rstrip('/')

    try:
        scheme = request.headers.get('X-Forwarded-Proto') or getattr(request, 'scheme', 'http') or 'http'
        host_header = request.headers.get('X-Forwarded-Host') or getattr(request, 'host', '')
        hostname = host_header.split(':')[0] if host_header else '127.0.0.1'
    except Exception:
        scheme = 'http'
        hostname = '127.0.0.1'

    api_port = os.getenv('DJANGO_API_PORT', '8000')
    return f"{scheme}://{hostname}:{api_port}"
def get_api_data(endpoint):
    """Получение данных через API"""
    try:
        # Убираем лишний слеш в конце endpoint
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        base = resolve_api_base()
        url = f'{base}/reports/api/{endpoint}/'
        print(f"DEBUG: Запрашиваем данные с {url}")
        response = requests.get(url)
        print(f"DEBUG: Статус ответа: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG: Получены данные: {len(data) if data else 0} записей")
            return data
        else:
            print(f"DEBUG: Ошибка API: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"DEBUG: Исключение при запросе к API: {e}")
        return []

def post_api_data(endpoint, data):
    """Отправка данных через API"""
    try:
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        base = resolve_api_base()
        response = requests.post(f'{base}/reports/api/{endpoint}/', json=data, timeout=15)
        return response.status_code == 201, response.json() if response.status_code == 201 else response.text
    except Exception as e:
        return False, f'EXC: {e}'

def put_api_data(endpoint, id, data):
    """Обновление данных через API"""
    try:
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]
        base = resolve_api_base()
        response = requests.put(f'{base}/reports/api/{endpoint}/{id}/', json=data, timeout=15)
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, f'EXC: {e}'

def delete_api_data(endpoint, id):
    """Удаление данных через API"""
    try:
        base = resolve_api_base()
        response = requests.delete(f'{base}/reports/api/{endpoint}/{id}/')
        return response.status_code == 204
    except:
        return False


def create_excel_export(record_data):
    """Создание CSV файла для экспорта записи"""
    try:
        # Создаем простой CSV файл
        headers = [
            "OID Медицинской организации",
            "OID документа", 
            "Дата создания",
            "Дата регистрации",
            "Номер в реестре РЭМД",
            "Локальный идентификатор",
            "Причина скрытия ЭМД",
            "Номер документа, оформленного взамен"
        ]
        
        # Получаем данные для экспорта
        # Для экспорта берем OID медицинской организации
        oid_medical_org = record_data.get('oid_medical_organization_oid', '') \
            or record_data.get('oid_medical_organization', '')
        oid_document = record_data.get('oid_document', '')
        creation_date = format_date_for_display(record_data.get('creation_date', ''))
        registration_date = format_date_for_display(record_data.get('registration_date', ''))
        reestr_number = record_data.get('reestr_number', '')
        local_identifier = record_data.get('local_identifier', '')
        reason_text = record_data.get('reason_not_actual_text', '') or record_data.get('reason_not_actual', '')
        document_number = record_data.get('document_number', '') or ''
        
        # Создаем CSV содержимое с правильной кодировкой (разделитель ; для Excel RU)
        csv_content = []
        csv_content.append(';'.join(headers))
        csv_content.append(';'.join([
            str(oid_medical_org),
            str(oid_document),
            str(creation_date),
            str(registration_date),
            str(reestr_number),
            str(local_identifier),
            str(reason_text),
            str(document_number)
        ]))
        
        csv_text = '\n'.join(csv_content)
        print(f"DEBUG: CSV содержимое: {csv_text}")
        
        # Возвращаем текст напрямую - Dash сам обработает кодировку
        return csv_text
    except Exception as e:
        print(f"DEBUG: Ошибка при создании файла: {e}")
        raise e


admin_delete_emd = dbc.Container([
           # Скрытый компонент для инициализации
           dcc.Store(id='init-trigger', data=0),
           # Скрытое поле для хранения ID редактируемой записи
           dcc.Store(id='edit-record-id', data=None),
           
           # Заголовок и навигация
           dbc.Row([
               dbc.Col([
                   html.H2("🗑️ Управление заявками на удаление ЭМД", className="mb-4"),
                   dbc.ButtonGroup([
                       dbc.Button("➕ Создать заявку", id="btn-create", color="success", size="sm"),
                       dbc.Button("✏️ Редактировать", id="btn-edit", color="primary", size="sm", disabled=True),
                       dbc.Button("📊 Экспорт в CSV", id="btn-export", color="info", size="sm", disabled=True)
                   ], className="mb-3")
               ])
           ]),
    
    # Фильтры и поиск
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.InputGroupText("🔍"),
                                dbc.Input(id="search-input", placeholder="Поиск по пациенту, ЕНП...", type="text")
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Select(
                                id="status-filter",
                                options=[
                                    {"label": "Все статусы", "value": "all"},
                                    {"label": "Черновик", "value": "draft"},
                                    {"label": "Отправлен", "value": "sent"},
                                    {"label": "Обработан", "value": "processed"},
                                    {"label": "Отклонен", "value": "rejected"}
                                ],
                                value="all"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Button("🔄 Обновить", id="btn-refresh", color="secondary", size="sm")
                        ], width=3)
                    ])
                ])
            ])
        ])
    ], className="mb-3"),
    
    # Таблица заявок
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("📊 Список заявок", className="mb-0"),
                    html.Small("Выберите заявку для просмотра или редактирования", className="text-muted")
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='delete-emd-table',
                        columns=[
                                   {'name': 'Пациент', 'id': 'patient'},
                                   {'name': 'ЕНП', 'id': 'enp'},
                                   {'name': 'Номер в реестре РЭМД', 'id': 'reestr_number'},
                                   {'name': 'Дата создания', 'id': 'creation_date'},
                                   {'name': 'Дата регистрации', 'id': 'registration_date'},
                                   {'name': 'Дата отправки в МЗ', 'id': 'sent_to_mz_date'},
                                   {'name': 'Статус', 'id': 'status_display'},
                                   {'name': 'Ответственный', 'id': 'responsible'}
                               ],
                        data=[],
                        sort_action="native",
                        filter_action="native",
                        page_action="native",
                        page_current=0,
                        page_size=20,
                        row_selectable="single",
                        selected_rows=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '8px'},
                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{status} = draft'},
                                'backgroundColor': '#fff3cd',
                                'color': 'black',
                            },
                            {
                                'if': {'filter_query': '{status} = sent'},
                                'backgroundColor': '#d1ecf1',
                                'color': 'black',
                            },
                            {
                                'if': {'filter_query': '{status} = processed'},
                                'backgroundColor': '#d4edda',
                                'color': 'black',
                            },
                            {
                                'if': {'filter_query': '{status} = rejected'},
                                'backgroundColor': '#f8d7da',
                                'color': 'black',
                            }
                        ],
                    )
                ])
            ])
                ])
            ]),
    
    # Модальное окно для создания/редактирования
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([
            dbc.Tabs([
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("OID документа *"),
                            dbc.Input(id="modal-oid-document", type="text", required=True),
                            dbc.FormText("Первые цифры Номера в реестре РЭМД - до точки")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Дата создания *"),
                            dcc.DatePickerSingle(id="modal-creation-date", date=datetime.now().date(), display_format="DD.MM.YYYY")
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Дата регистрации *"),
                            dcc.DatePickerSingle(id="modal-registration-date", date=datetime.now().date(), display_format="DD.MM.YYYY")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Номер в реестре РЭМД *"),
                            dbc.Input(id="modal-reestr-number", type="text", required=True),
                            dbc.FormText("Журнал ЭМД: Регистрационный номер")
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Локальный идентификатор *"),
                            dbc.Input(id="modal-local-identifier", type="text", required=True),
                            dbc.FormText("Журнал ЭМД: имя xml-файла при сохранении, напр.: 3e765e5d-acfc-4e44-b834-7a876acbe40c")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Причина аннулирования *"),
                            dcc.Dropdown(id="modal-reason-dropdown", options=[])
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Номер документа взамен"),
                            dbc.Input(id="modal-document-number", type="text")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Медицинская организация *"),
                            dcc.Dropdown(id="modal-medical-org-dropdown", options=[])
                        ], width=6)
                    ], className="mb-3")
                ], label="Основная информация", tab_id="tab-basic"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Пациент *"),
                            dbc.Input(id="modal-patient", type="text", required=True)
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Дата рождения *"),
                            dcc.DatePickerSingle(id="modal-date-of-birth", date=datetime.now().date(), display_format="DD.MM.YYYY")
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("ЕНП *"),
                            dbc.Input(id="modal-enp", type="text", required=True)
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Цель ОМС *"),
                            dbc.Input(id="modal-goal-input", type="text", required=True)
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Окончание лечения *"),
                            dcc.DatePickerSingle(id="modal-treatment-end", date=datetime.now().date(), display_format="DD.MM.YYYY")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Ответственный *"),
                            dbc.Input(id="modal-responsible-input", type="text", required=True),
                            dbc.FormText("Текстовое поле: укажите ФИО ответственного")
                        ], width=6)
                    ], className="mb-3")
                ], label="Данные пациента", tab_id="tab-patient"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Статус *"),
                            dcc.Dropdown(
                                id="modal-status-dropdown",
                                options=[
                                    {"label": "Черновик", "value": "draft"},
                                    {"label": "Отправлен", "value": "sent"},
                                    {"label": "Обработан", "value": "processed"},
                                    {"label": "Отклонен", "value": "rejected"}
                                ],
                                value="draft"
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Дата отправки в МЗ"),
                            dcc.DatePickerSingle(id="modal-sent-to-mz-date", date=None, display_format="DD.MM.YYYY")
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Комментарий"),
                            dbc.Textarea(id="modal-comment", placeholder="Дополнительные комментарии...")
                        ], width=12)
                    ], className="mb-3")
                ], label="Управление", tab_id="tab-management")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("❌ Отмена", id="modal-cancel", color="secondary", className="me-2"),
            dbc.Button("💾 Сохранить", id="modal-save", color="primary")
        ])
    ], id="modal-edit", is_open=False, size="xl"),
    
    # Скрытый компонент для скачивания файлов
    dcc.Download(id="download-excel"),
    
    # Уведомления
    dbc.Toast(
        id="toast-notification",
        header="Уведомление",
        is_open=False,
        dismissable=True,
        icon="success",
        duration=4000,
        style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 99999}
    )
], fluid=True)


# Callback для загрузки данных таблицы
@app.callback(
    Output('delete-emd-table', 'data'),
    [Input('btn-refresh', 'n_clicks'),
     Input('search-input', 'value'),
     Input('status-filter', 'value'),
     Input('btn-create', 'n_clicks'),
     Input('init-trigger', 'data')],
    prevent_initial_call=False
)
def update_table_data(btn_refresh, search_value, status_filter, btn_create, init_data):
    # Всегда загружаем все заявки
    data = get_api_data('delete-emd/')
    
    # Отладочная информация
    print(f"DEBUG: Получены данные из API: {len(data) if data else 0} записей")
    if data:
        print(f"DEBUG: Первая запись ID: {data[0].get('id', 'N/A') if data else 'Нет данных'}")
    
    # Если данных нет, возвращаем пустой список
    if not data:
        print("DEBUG: Данных нет, возвращаем пустой список")
        return []

    # Фильтрация по статусу
    if status_filter and status_filter != 'all':
        data = [item for item in data if item.get('status') == status_filter]

    # Поиск
    if search_value:
        search_lower = search_value.lower()
        data = [item for item in data if
                search_lower in item.get('patient', '').lower() or
                search_lower in item.get('enp', '').lower()]

    # Форматирование дат для отображения
    for item in data:
        if 'creation_date' in item:
            item['creation_date'] = format_date_for_display(item.get('creation_date'))
        if 'registration_date' in item:
            item['registration_date'] = format_date_for_display(item.get('registration_date'))
        if 'sent_to_mz_date' in item:
            item['sent_to_mz_date'] = format_date_for_display(item.get('sent_to_mz_date'))

    print(f"DEBUG: Возвращаем {len(data)} записей")
    return data


# Callback для загрузки справочников в модальное окно (только для оставшихся dropdown'ов)
@app.callback(
    [Output('modal-reason-dropdown', 'options'),
     Output('modal-medical-org-dropdown', 'options')],
    [Input('btn-create', 'n_clicks'),
     Input('delete-emd-table', 'selected_rows'),
     Input('modal-edit', 'is_open')]
)
def load_modal_data(btn_create, selected_rows, modal_is_open):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Загружаем справочники при создании, редактировании или открытии модального окна
    if trigger_id in ['btn-create', 'delete-emd-table', 'modal-edit']:
        print("DEBUG: Загружаем справочники...")
        reasons = get_api_data('invalidation-reasons/')
        medical_orgs = get_api_data('medical-organizations/')
        
        print(f"DEBUG: Загружено - причины: {len(reasons)}, мед.орг: {len(medical_orgs)}")

        reason_options = [{'label': item['reason_text'], 'value': item['id']} for item in reasons]
        medical_org_options = [{'label': item['name'], 'value': item['id']} for item in medical_orgs]
        
        print(f"DEBUG: Опции причин: {len(reason_options)} шт.")
        print(f"DEBUG: Опции мед.орг: {len(medical_org_options)} шт.")

        return (reason_options, medical_org_options)
    
    raise PreventUpdate


# Callback для активации кнопок "Редактировать" и "Экспорт"
@app.callback(
    [Output('btn-edit', 'disabled'),
     Output('btn-export', 'disabled')],
    [Input('delete-emd-table', 'selected_rows')],
    prevent_initial_call=True
)
def toggle_buttons(selected_rows):
    is_disabled = len(selected_rows) == 0
    return is_disabled, is_disabled


# Callback для открытия модального окна
@app.callback(
    [Output('modal-edit', 'is_open'),
     Output('modal-title', 'children'),
     Output('modal-oid-document', 'value'),
     Output('modal-creation-date', 'date'),
     Output('modal-registration-date', 'date'),
     Output('modal-reestr-number', 'value'),
     Output('modal-local-identifier', 'value'),
     Output('modal-reason-dropdown', 'value'),
     Output('modal-document-number', 'value'),
     Output('modal-medical-org-dropdown', 'value'),
     Output('modal-patient', 'value'),
     Output('modal-date-of-birth', 'date'),
     Output('modal-enp', 'value'),
     Output('modal-goal-input', 'value'),
     Output('modal-treatment-end', 'date'),
     Output('modal-responsible-input', 'value'),
     Output('modal-status-dropdown', 'value'),
            Output('modal-sent-to-mz-date', 'date'),
     Output('modal-comment', 'value'),
     Output('edit-record-id', 'data')],
    [Input('btn-create', 'n_clicks'),
     Input('btn-edit', 'n_clicks'),
     Input('modal-cancel', 'n_clicks')],
    [State('delete-emd-table', 'data'),
     State('delete-emd-table', 'selected_rows')]
)
def toggle_modal(btn_create, btn_edit, btn_cancel, table_data, selected_rows):
    ctx = callback_context
    if not ctx.triggered:
        return False, "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", None, "", None

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'btn-create':
        today = datetime.now().date()
        return True, "➕ Создать новую заявку", "", today, today, "", "", "", "", "", "", today, "", "", today, "", "draft", None, "", None
    elif trigger_id == 'btn-edit' and selected_rows:
        # Редактирование через кнопку "Редактировать"
        row_idx = selected_rows[0]
        if row_idx < len(table_data):
            item = table_data[row_idx]
            print(f"DEBUG: Редактирование записи {item['id']} через кнопку")
            print(f"DEBUG: Данные записи: {item.get('id', 'N/A')} - {item.get('patient', 'N/A')}")
            
            # Конвертируем даты в объекты datetime для DatePickerSingle
            creation_date = to_date_obj(item.get('creation_date', ''))
            registration_date = to_date_obj(item.get('registration_date', ''))
            date_of_birth = to_date_obj(item.get('date_of_birth', ''))
            treatment_end = to_date_obj(item.get('treatment_end', ''))
            sent_to_mz_date = to_date_obj(item.get('sent_to_mz_date', ''))
            
            # уже конвертировано функцией to_date_obj
            
            # Получаем текстовые значения для отображения
            goal_text = item.get('goal_name', '') or item.get('goal', '')
            responsible_text = item.get('responsible_name', '') or item.get('responsible', '')
            
            return True, f"✏️ Редактировать заявку #{item['id']}", \
                   item.get('oid_document', ''), \
                   creation_date, \
                   registration_date, \
                   item.get('reestr_number', ''), \
                   item.get('local_identifier', ''), \
                   item.get('reason_not_actual', ''), \
                   item.get('document_number', ''), \
                   item.get('oid_medical_organization', ''), \
                   item.get('patient', ''), \
                   date_of_birth, \
                   item.get('enp', ''), \
                   goal_text, \
                   treatment_end, \
                   responsible_text, \
                   item.get('status', 'draft'), \
                   sent_to_mz_date, \
                   item.get('comment', ''), \
                   item['id']
    elif trigger_id == 'modal-cancel':
        return False, "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", None, "", None

    return False, "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", None, "", None


# Callback для сохранения данных
@app.callback(
    [Output('modal-edit', 'is_open', allow_duplicate=True),
     Output('toast-notification', 'is_open'),
     Output('toast-notification', 'children'),
     Output('toast-notification', 'icon'),
     Output('delete-emd-table', 'data', allow_duplicate=True)],
    [Input('modal-save', 'n_clicks')],
    [State('modal-oid-document', 'value'),
     State('modal-creation-date', 'date'),
     State('modal-registration-date', 'date'),
     State('modal-reestr-number', 'value'),
     State('modal-local-identifier', 'value'),
     State('modal-reason-dropdown', 'value'),
     State('modal-document-number', 'value'),
     State('modal-medical-org-dropdown', 'value'),
     State('modal-patient', 'value'),
     State('modal-date-of-birth', 'date'),
     State('modal-enp', 'value'),
     State('modal-goal-input', 'value'),
     State('modal-treatment-end', 'date'),
     State('modal-responsible-input', 'value'),
     State('modal-status-dropdown', 'value'),
     State('modal-sent-to-mz-date', 'date'),
     State('modal-comment', 'value'),
     State('edit-record-id', 'data')],
    prevent_initial_call=True
)
def save_data(n_clicks, oid_document, creation_date, registration_date, reestr_number, 
             local_identifier, reason, document_number, medical_org, patient, 
             date_of_birth, enp, goal, treatment_end, responsible, status, sent_to_mz_date, comment, edit_id):
    
    if not n_clicks:
        raise PreventUpdate
    
    # Подготовка данных
    data = {
        'oid_document': oid_document,
        'creation_date': format_date_for_api(creation_date),
        'registration_date': format_date_for_api(registration_date),
        'reestr_number': reestr_number,
        'local_identifier': local_identifier,
        'reason_not_actual': reason,
        'document_number': document_number,
        'oid_medical_organization': medical_org,
        'patient': patient,
        'date_of_birth': format_date_for_api(date_of_birth),
        'enp': enp,
        'goal': goal,  # Теперь это текстовое поле
        'treatment_end': format_date_for_api(treatment_end),
        'responsible': responsible,  # Теперь это текстовое поле
        'status': status,
        'sent_to_mz_date': format_date_for_api(sent_to_mz_date),
        'comment': comment
    }
    
    # При обновлении исключаем поля, которые не должны изменяться
    if edit_id:
        # Исключаем системные поля при обновлении
        data.pop('created_by', None)  # Убираем created_by из обновления
        data.pop('added_date', None)  # Убираем added_date из обновления
    
    # Сохранение через API
    print(f"DEBUG: Сохранение данных для записи: {edit_id or 'новая'}")
    print(f"DEBUG: ID записи: {edit_id}")
    
    if edit_id:
        # Редактирование существующей записи
        print(f"DEBUG: Обновление записи {edit_id}")
        success, result = put_api_data('delete-emd', edit_id, data)
        print(f"DEBUG: Результат обновления: success={success}, result={result}")
        if success:
            # Обновляем данные таблицы после успешного сохранения
            updated_data = get_api_data('delete-emd/')
            return False, True, f"✅ Заявка #{edit_id} успешно обновлена!", "success", updated_data
        else:
            return True, True, f"❌ Ошибка при обновлении: {result}", "danger", []
    else:
        # Создание новой записи
        print("DEBUG: Создание новой записи")
        success, result = post_api_data('delete-emd/', data)
        print(f"DEBUG: Результат создания: success={success}, result={result}")
        if success:
            # Обновляем данные таблицы после успешного создания
            updated_data = get_api_data('delete-emd/')
            return False, True, "✅ Заявка успешно создана!", "success", updated_data
        else:
            return True, True, f"❌ Ошибка при создании: {result}", "danger", []


# Callback для экспорта в Excel
@app.callback(
    [Output('download-excel', 'data'),
     Output('toast-notification', 'is_open', allow_duplicate=True),
     Output('toast-notification', 'children', allow_duplicate=True),
     Output('toast-notification', 'icon', allow_duplicate=True)],
    [Input('btn-export', 'n_clicks')],
    [State('delete-emd-table', 'selected_rows'),
     State('delete-emd-table', 'data')],
    prevent_initial_call=True
)
def export_to_excel(n_clicks, selected_rows, table_data):
    if not n_clicks or not selected_rows:
        raise PreventUpdate
    
    try:
        # Получаем выбранную запись
        row_idx = selected_rows[0]
        if row_idx < len(table_data):
            record = table_data[row_idx]
            print(f"DEBUG: Экспорт записи {record.get('id', 'unknown')}")
            print(f"DEBUG: Данные записи: {record.get('patient', 'N/A')}")
            
            # Создаем CSV файл
            csv_text = create_excel_export(record)
            print(f"DEBUG: CSV файл создан, размер: {len(csv_text)} символов")
            print(f"DEBUG: CSV содержимое: {csv_text}")
            
            # Добавляем BOM и отдаем ТЕКСТ напрямую без base64
            csv_text_with_bom = '\ufeff' + csv_text
            
            # Создаем имя файла
            filename = f"delete_emd_export_{record.get('id', 'unknown')}.csv"
            
            # Возвращаем файл для скачивания и уведомление
            return {
                "content": csv_text_with_bom,
                "filename": filename,
                "type": "text/csv;charset=utf-8"
            }, True, f"✅ CSV файл '{filename}' готов к скачиванию!", "success"
        else:
            return None, True, "❌ Ошибка: запись не найдена", "danger"
    except Exception as e:
        print(f"DEBUG: Ошибка при экспорте: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return None, True, f"❌ Ошибка при экспорте: {str(e)}", "danger"

