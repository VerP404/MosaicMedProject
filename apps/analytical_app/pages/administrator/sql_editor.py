import os
import django

# Настройка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mosaic_med.settings')
django.setup()

from dash import html, dcc, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from sqlalchemy import text
import fdb
from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine
from apps.analytical_app.elements import card_table
from apps.sql_manager.models import SavedQuery
from apps.home.models import MainSettings
from django.contrib.auth.models import User

type_page = 'sql_editor'
main_link = 'admin'
label = 'SQL Редактор'

# Функция для проверки доступности библиотеки Firebird
def is_firebird_available():
    """Проверяет доступность библиотеки Firebird"""
    try:
        import fdb
        # Пробуем создать тестовое подключение
        fdb.connect()
        return True
    except Exception:
        return False

# Функция для проверки подключения к Firebird
def check_firebird_connection():
    try:
        settings = MainSettings.objects.first()
        if not settings:
            return False, "Настройки подключения к КАУЗ не найдены"
        
        # Проверяем, что все необходимые настройки заполнены
        if not all([settings.kauz_server_ip, settings.kauz_database_path, 
                   settings.kauz_user, settings.kauz_password]):
            return False, "Не все настройки подключения заполнены"
        
        dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"
        
        # Пробуем подключиться
        con = fdb.connect(
            dsn=dsn,
            user=settings.kauz_user,
            password=settings.kauz_password,
            charset='WIN1251',
            port=settings.kauz_port
        )
        
        # Проверяем, что подключение действительно работает
        cursor = con.cursor()
        cursor.execute("SELECT 1 FROM RDB$DATABASE")
        cursor.fetchone()
        cursor.close()
        con.close()
        
        return True, "Подключение доступно"
    except fdb.Error as e:
        error_msg = str(e)
        if "SQLCODE: -902" in error_msg:
            return False, "Сервер Firebird недоступен или база данных заблокирована"
        elif "SQLCODE: -902" in error_msg and "connection shutdown" in error_msg:
            return False, "Соединение с сервером прервано"
        else:
            return False, f"Ошибка Firebird: {error_msg}"
    except Exception as e:
        return False, f"Ошибка подключения: {str(e)}"

# Основной layout
sql_editor_layout = html.Div([
    dbc.Breadcrumb(
        id=f"breadcrumb-{type_page}",
        items=[
            {"label": "Администратор", "href": f"/{main_link}"},
            {"label": label, "active": True}
        ]
    ),
    html.Hr(),
    
    # SQL редактор
    dbc.Card([
        dbc.CardHeader("SQL Редактор"),
        dbc.CardBody([
            # Переключатель баз данных
            dbc.Row([
                dbc.Col([
                    dbc.Label("База данных:"),
                    dcc.RadioItems(
                        id=f'database-selector-{type_page}',
                        options=[
                            {'label': 'PostgreSQL', 'value': 'postgresql'},
                            {'label': 'Firebird (КАУЗ)', 'value': 'firebird'}
                        ] if is_firebird_available() else [
                            {'label': 'PostgreSQL', 'value': 'postgresql'}
                        ],
                        value='postgresql',
                        inline=True,
                        className='mb-3'
                    )
                ], width=6),
                dbc.Col([
                    html.Div(id=f'connection-status-{type_page}', className='mt-4')
                ], width=6)
            ]),
            
            # Выпадающий список сохраненных запросов
            dbc.Row([
                dbc.Col([
                    dbc.Label("Сохраненные запросы:"),
                    dcc.Dropdown(
                        id=f'saved-queries-{type_page}',
                        options=[],  # Будет заполнено через callback
                        placeholder="Выберите сохраненный запрос...",
                        className='mb-3'
                    )
                ], width=6),
                dbc.Col([
                    dbc.Button(
                        "Удалить запрос",
                        id=f'delete-query-{type_page}',
                        color="danger",
                        className="mt-4"
                    )
                ], width=6)
            ]),
            
            # Текстовое поле для SQL запроса
            dcc.Textarea(
                id=f'sql-query-{type_page}',
                placeholder='Введите SQL запрос (только SELECT)...',
                style={'width': '100%', 'height': '150px', 'fontFamily': 'monospace'},
                className='mb-3'
            ),
            
            # Кнопки управления
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Выполнить запрос",
                        id=f'execute-query-{type_page}',
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Сохранить запрос",
                        id=f'save-query-{type_page}',
                        color="success",
                        className="me-2"
                    )
                ])
            ], className="mb-3"),
            
            # Модальное окно для сохранения запроса
            dbc.Modal([
                dbc.ModalHeader("Сохранение запроса"),
                dbc.ModalBody([
                    dbc.Input(
                        id=f'query-name-{type_page}',
                        placeholder="Название запроса",
                        className="mb-3"
                    ),
                    dbc.Textarea(
                        id=f'query-description-{type_page}',
                        placeholder="Описание запроса (необязательно)",
                        className="mb-3"
                    ),
                    dbc.Checkbox(
                        id=f'query-public-{type_page}',
                        label="Сделать запрос публичным",
                        className="mb-3"
                    )
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Сохранить",
                        id=f'save-query-confirm-{type_page}',
                        color="success",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Отмена",
                        id=f'save-query-cancel-{type_page}',
                        color="secondary"
                    )
                ])
            ], id=f'save-query-modal-{type_page}'),
            
            # Модальное окно для подтверждения удаления
            dbc.Modal([
                dbc.ModalHeader("Подтверждение удаления"),
                dbc.ModalBody([
                    dbc.Input(
                        id=f'delete-pincode-{type_page}',
                        type="password",
                        placeholder="Введите пинкод",
                        className="mb-3"
                    ),
                    html.Div(id=f'delete-error-{type_page}', className='text-danger mb-3')
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Удалить",
                        id=f'delete-confirm-{type_page}',
                        color="danger",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Отмена",
                        id=f'delete-cancel-{type_page}',
                        color="secondary"
                    )
                ])
            ], id=f'delete-modal-{type_page}'),
            
            # Сообщение об ошибке
            html.Div(id=f'error-message-{type_page}', className='text-danger mb-3'),
            
            # Индикатор загрузки и результаты запроса
            dcc.Loading(
                id=f'loading-{type_page}',
                type="circle",
                children=[
                    html.Div(id=f'query-results-{type_page}')
                ]
            )
        ])
    ])
])

# Функция для проверки безопасности SQL запроса
def is_safe_query(query):
    dangerous_keywords = [
        'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT',
        'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'MERGE', 'UPSERT'
    ]
    query_upper = query.upper()
    return all(keyword not in query_upper for keyword in dangerous_keywords)

# Callback для отображения статуса подключения
@app.callback(
    Output(f'connection-status-{type_page}', 'children'),
    Input(f'database-selector-{type_page}', 'value')
)
def update_connection_status(database_type):
    if database_type == 'firebird':
        is_available, message = check_firebird_connection()
        if is_available:
            return dbc.Alert("✅ Firebird доступен", color="success", className="mb-0")
        else:
            return dbc.Alert(f"❌ {message}", color="danger", className="mb-0")
    else:
        return dbc.Alert("✅ PostgreSQL доступен", color="success", className="mb-0")

# Callback для загрузки сохраненных запросов
@app.callback(
    Output(f'saved-queries-{type_page}', 'options'),
    Input(f'execute-query-{type_page}', 'n_clicks'),
    Input(f'save-query-confirm-{type_page}', 'n_clicks'),
    Input(f'delete-query-{type_page}', 'n_clicks')
)
def load_saved_queries(*args):
    queries = SavedQuery.objects.filter(is_public=True) | SavedQuery.objects.filter(created_by=User.objects.first())  # Временно используем первого пользователя
    return [{'label': q.name, 'value': q.id} for q in queries]

# Callback для загрузки выбранного запроса
@app.callback(
    Output(f'sql-query-{type_page}', 'value'),
    Input(f'saved-queries-{type_page}', 'value')
)
def load_query(query_id):
    if not query_id:
        raise PreventUpdate
    query = SavedQuery.objects.get(id=query_id)
    return query.query

# Callback для открытия/закрытия модальных окон
@app.callback(
    [Output(f'save-query-modal-{type_page}', 'is_open'),
     Output(f'delete-modal-{type_page}', 'is_open')],
    [Input(f'save-query-{type_page}', 'n_clicks'),
     Input(f'save-query-confirm-{type_page}', 'n_clicks'),
     Input(f'save-query-cancel-{type_page}', 'n_clicks'),
     Input(f'delete-query-{type_page}', 'n_clicks'),
     Input(f'delete-confirm-{type_page}', 'n_clicks'),
     Input(f'delete-cancel-{type_page}', 'n_clicks')],
    [State(f'save-query-modal-{type_page}', 'is_open'),
     State(f'delete-modal-{type_page}', 'is_open')],
    prevent_initial_call=True
)
def toggle_modals(n1, n2, n3, n4, n5, n6, save_modal_open, delete_modal_open):
    ctx = callback_context
    if not ctx.triggered:
        return save_modal_open, delete_modal_open
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == f'save-query-{type_page}':
        return True, delete_modal_open
    elif button_id in [f'save-query-confirm-{type_page}', f'save-query-cancel-{type_page}']:
        return False, delete_modal_open
    elif button_id == f'delete-query-{type_page}':
        return save_modal_open, True
    elif button_id in [f'delete-confirm-{type_page}', f'delete-cancel-{type_page}']:
        return save_modal_open, False
    
    return save_modal_open, delete_modal_open

# Callback для проверки пинкода и удаления запроса
@app.callback(
    [Output(f'delete-error-{type_page}', 'children'),
     Output(f'error-message-{type_page}', 'children', allow_duplicate=True)],
    [Input(f'delete-confirm-{type_page}', 'n_clicks')],
    [State(f'delete-pincode-{type_page}', 'value'),
     State(f'saved-queries-{type_page}', 'value')],
    prevent_initial_call=True
)
def confirm_delete(n_clicks, pincode, query_id):
    if not query_id:
        return "", "Выберите запрос для удаления"
    
    if pincode != "0000":
        return "Неверный пинкод", ""
    
    try:
        query = SavedQuery.objects.get(id=query_id)
        query.delete()
        return "", "Запрос успешно удален"
    except Exception as e:
        return "", f"Ошибка при удалении запроса: {str(e)}"

# Callback для сохранения запроса
@app.callback(
    Output(f'error-message-{type_page}', 'children', allow_duplicate=True),
    [Input(f'save-query-confirm-{type_page}', 'n_clicks')],
    [State(f'sql-query-{type_page}', 'value'),
     State(f'query-name-{type_page}', 'value'),
     State(f'query-description-{type_page}', 'value'),
     State(f'query-public-{type_page}', 'value')],
    prevent_initial_call=True
)
def save_query(n_clicks, query, name, description, is_public):
    if not query or not name:
        return "Введите название и SQL запрос"
    
    # Проверяем безопасность запроса
    if not is_safe_query(query):
        return "Запрос содержит опасные команды. Разрешены только SELECT запросы"
    
    try:
        SavedQuery.objects.create(
            name=name,
            query=query,
            description=description,
            created_by=User.objects.first(),  # Временно используем первого пользователя
            is_public=bool(is_public)
        )
        return "Запрос успешно сохранен"
    except Exception as e:
        return f"Ошибка при сохранении запроса: {str(e)}"

# Callback для выполнения запроса
@app.callback(
    [Output(f'query-results-{type_page}', 'children'),
     Output(f'error-message-{type_page}', 'children', allow_duplicate=True)],
    [Input(f'execute-query-{type_page}', 'n_clicks')],
    [State(f'sql-query-{type_page}', 'value'),
     State(f'database-selector-{type_page}', 'value')],
    prevent_initial_call=True
)
def execute_query(n_clicks, query, database_type):
    if not query:
        return None, "Введите SQL запрос"
    if not is_safe_query(query):
        return None, "Запрос содержит опасные команды. Разрешены только SELECT запросы"
    
    try:
        if database_type == 'firebird':
            # Проверяем доступность Firebird перед выполнением запроса
            is_available, message = check_firebird_connection()
            if not is_available:
                return None, f"Firebird недоступен: {message}"
            
            # Выполнение запроса к Firebird
            settings = MainSettings.objects.first()
            if not settings:
                return None, "Настройки подключения к КАУЗ не найдены"
            
            dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"
            con = fdb.connect(
                dsn=dsn,
                user=settings.kauz_user,
                password=settings.kauz_password,
                charset='WIN1251',
                port=settings.kauz_port
            )
            
            cursor = con.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            con.close()
            
            # Преобразуем результаты в DataFrame
            df = pd.DataFrame(results, columns=columns)
        else:
            # Выполнение запроса к PostgreSQL
            df = pd.read_sql(text(query), engine)
        
        # Проверяем, что есть данные
        if df.empty:
            return dbc.Alert("Запрос выполнен успешно, но данных не найдено", color="warning"), ""
        
        # Создаем таблицу с результатами
        columns = [{"name": col, "id": col} for col in df.columns]
        data = df.to_dict('records')
        table = dash_table.DataTable(
            id=f'result-table-{type_page}',
            columns=columns,
            data=data,
            page_size=15,
            filter_action="native",
            sort_action="native",
            export_format="xlsx",
            export_headers="display",
            style_table={'overflowX': 'auto'},
            style_cell={'minWidth': '0px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
        )
        card = dbc.Card([
            dbc.CardHeader(f"Результаты запроса ({database_type.upper()}) - {len(data)} записей"),
            dbc.CardBody([table])
        ])
        return card, ""
    except fdb.Error as e:
        error_msg = str(e)
        if "SQLCODE: -902" in error_msg:
            return None, "Сервер Firebird недоступен или база данных заблокирована. Попробуйте позже."
        elif "connection shutdown" in error_msg:
            return None, "Соединение с сервером Firebird прервано. Проверьте настройки подключения."
        else:
            return None, f"Ошибка Firebird: {error_msg}"
    except Exception as e:
        return None, f"Ошибка выполнения запроса: {str(e)}" 