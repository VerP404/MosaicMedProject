from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from datetime import datetime

from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.administrator.digital_signatures.query import sql_query_digital_signatures
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.query_executor import engine
from apps.analytical_app.app import app

type_page = "admin-digital-signatures"


def layout():
    """Layout для страницы ЭЦП"""
    
    return html.Div([
        # Заголовок страницы
        dbc.Row([
            dbc.Col([
                html.H3("Электронные цифровые подписи (ЭЦП)", className="mb-3")
            ])
        ]),
        
        # Фильтры
        dbc.Card([
            dbc.CardHeader("Фильтры и настройки"),
            dbc.CardBody([
                dbc.Row([
                    # Фильтр по работающим
                    dbc.Col([
                        html.Label("Показывать только работающих:", className="fw-bold"),
                        dbc.Switch(
                            id=f'switch-working-only-{type_page}',
                            label="Да",
                            value=True,
                            className="mt-2"
                        )
                    ], width=3),
                    
                    # Фильтр по последним ЭЦП
                    dbc.Col([
                        html.Label("Показывать ЭЦП:", className="fw-bold"),
                        dbc.RadioItems(
                            id=f'radio-show-mode-{type_page}',
                            options=[
                                {'label': 'Только последние', 'value': 'latest'},
                                {'label': 'Все', 'value': 'all'}
                            ],
                            value='latest',
                            inline=True,
                            className="mt-2"
                        )
                    ], width=4),
                    
                    # Фильтр по статусу срока действия
                    dbc.Col([
                        html.Label("Фильтр по сроку:", className="fw-bold"),
                        dcc.Dropdown(
                            id=f'dropdown-status-filter-{type_page}',
                            options=[
                                {'label': 'Все', 'value': 'all'},
                                {'label': 'Заканчиваются в течение 60 дней', 'value': 'expiring_60'},
                                {'label': 'Заканчиваются в течение 30 дней', 'value': 'expiring_30'},
                                {'label': 'Заканчиваются в течение 7 дней', 'value': 'expiring_7'},
                                {'label': 'Просроченные', 'value': 'expired'},
                                {'label': 'Активные', 'value': 'active'},
                                {'label': 'Аннулированные', 'value': 'revoked'}
                            ],
                            value='all',
                            clearable=False,
                            className="mt-2"
                        )
                    ], width=3),

                    # Фильтр по процессу получения ЭЦП
                    dbc.Col([
                        html.Label("Этап процесса:", className="fw-bold"),
                        dcc.Dropdown(
                            id=f'dropdown-process-filter-{type_page}',
                            options=[
                                {'label': 'Все', 'value': 'all'},
                                {'label': 'Нет действий', 'value': 'no_actions'},
                                {'label': 'Уведомление загружено', 'value': 'notification_uploaded'},
                                {'label': 'Заявление создано', 'value': 'application_created'},
                                {'label': 'Новая ЭЦП готова', 'value': 'new_certificate_ready'},
                                {'label': 'ЭЦП действует', 'value': 'active_certificate'},
                            ],
                            value='all',
                            clearable=False,
                            className="mt-2"
                        )
                    ], width=2),
                    
                    # Фильтр по категории
                    dbc.Col([
                        html.Label("Категория:", className="fw-bold"),
                        dcc.Dropdown(
                            id=f'dropdown-category-filter-{type_page}',
                            options=[
                                {'label': 'Все', 'value': 'all'},
                                {'label': 'Врач', 'value': 'doctor'},
                                {'label': 'Сотрудник', 'value': 'staff'},
                            ],
                            value='all',
                            clearable=False,
                            className="mt-2"
                        )
                    ], width=2),
                    
                    # Фильтр по подразделению
                    dbc.Col([
                        html.Label("Подразделение:", className="fw-bold"),
                        dcc.Dropdown(
                            id=f'dropdown-department-filter-{type_page}',
                            options=[],
                            value=None,
                            placeholder="Все подразделения",
                            clearable=True,
                            className="mt-2"
                        )
                    ], width=2),
                    
                    # Кнопка обновления
                    dbc.Col([
                        html.Label("", className="fw-bold"),  # Пустая метка для выравнивания
                        dbc.Button(
                            "Обновить",
                            id=f'update-button-{type_page}',
                            color="primary",
                            className="mt-2 w-100"
                        )
                    ], width=1)
                ], className="mb-3"),
                
                # Информационные блоки
                dbc.Row([
                    dbc.Col([
                        dbc.Alert(
                            [
                                html.Strong("Цветовая индикация: "),
                                html.Span("Светло-желтый", style={"background-color": "#fffef0", "padding": "2px 8px", "border-radius": "3px"}),
                                " - осталось ≤60 дней; ",
                                html.Span("Желтый", style={"background-color": "#fff3cd", "padding": "2px 8px", "border-radius": "3px"}),
                                " - осталось ≤30 дней; ",
                                html.Span("Оранжевый", style={"background-color": "#ffc107", "padding": "2px 8px", "border-radius": "3px"}),
                                " - осталось ≤7 дней; ",
                                html.Span("Красный", style={"background-color": "#f8d7da", "padding": "2px 8px", "border-radius": "3px"}),
                                " - просрочено; ",
                                html.Span("Синий", style={"background-color": "#cfe2ff", "padding": "2px 8px", "border-radius": "3px"}),
                                " - переоформлено (при показе всех ЭЦП)"
                            ],
                            color="info",
                            className="mb-2"
                        )
                    ])
                ])
            ])
        ], className="mb-3"),
        
        # Блок статистики
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Краткая статистика"),
                    dbc.CardBody([
                        html.Div(id=f'stats-content-{type_page}')
                    ])
                ])
            ], width=12)
        ], className="mb-3"),
        
        # Основная таблица
        dcc.Loading(
            id=f'loading-output-{type_page}',
            type='default',
            children=[
                card_table(
                    f'result-table-{type_page}',
                    "Список ЭЦП",
                    page_size=50,
                    style_cell_conditional=[
                        {'if': {'column_id': 'fio'}, 'width': '12%'},
                        {'if': {'column_id': 'snils'}, 'width': '8%'},
                        {'if': {'column_id': 'certificate_serial'}, 'width': '10%'},
                        {'if': {'column_id': 'category'}, 'width': '8%'},
                        {'if': {'column_id': 'department_name'}, 'width': '12%'},
                        {'if': {'column_id': 'position_name'}, 'width': '12%'},
                        {'if': {'column_id': 'valid_from'}, 'width': '7%'},
                        {'if': {'column_id': 'valid_to'}, 'width': '7%'},
                        {'if': {'column_id': 'days_until_expiration'}, 'width': '7%'},
                        {'if': {'column_id': 'status'}, 'width': '8%'},
                        {'if': {'column_id': 'process_status_display'}, 'width': '10%'},
                        {'if': {'column_id': 'has_scan'}, 'width': '6%'},
                        {'if': {'column_id': 'action'}, 'width': '6%'},
                    ],
                    markdown_options={"link_target": "_blank"}
                )
            ]
        )
    ])


# Callback для загрузки списка подразделений
@callback(
    Output(f'dropdown-department-filter-{type_page}', 'options'),
    Input(f'update-button-{type_page}', 'n_clicks')
)
def load_departments(n_clicks):
    """Загружает список подразделений для фильтра"""
    try:
        # Запрос для получения уникальных подразделений
        # Используем ту же логику, что и в основном запросе
        query = """
        WITH person_departments AS (
            SELECT DISTINCT
                p.id as person_id,
                COALESCE(
                    (SELECT dr.structural_unit 
                     FROM personnel_doctorrecord dr
                     WHERE dr.person_id = p.id
                     AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                     ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                     LIMIT 1),
                    (SELECT dept.name 
                     FROM personnel_doctorrecord dr
                     INNER JOIN organization_department dept ON dept.id = dr.department_id
                     WHERE dr.person_id = p.id
                     AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
                     ORDER BY dr.end_date DESC NULLS FIRST, dr.start_date DESC
                     LIMIT 1),
                    (SELECT dept.name 
                     FROM personnel_staffrecord sr
                     INNER JOIN organization_department dept ON dept.id = sr.department_id
                     WHERE sr.person_id = p.id
                     AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
                     ORDER BY sr.end_date DESC NULLS FIRST, sr.start_date DESC
                     LIMIT 1)
                ) as department_name
            FROM personnel_person p
            WHERE EXISTS (
                SELECT 1 
                FROM personnel_doctorrecord dr
                WHERE dr.person_id = p.id
                AND (dr.end_date IS NULL OR dr.end_date >= CURRENT_DATE)
            )
            OR EXISTS (
                SELECT 1 
                FROM personnel_staffrecord sr
                WHERE sr.person_id = p.id
                AND (sr.end_date IS NULL OR sr.end_date >= CURRENT_DATE)
            )
        )
        SELECT DISTINCT department_name
        FROM person_departments
        WHERE department_name IS NOT NULL AND department_name != '-'
        ORDER BY department_name
        """
        
        columns, data = TableUpdater.query_to_df(engine, query)
        
        # Формируем опции для dropdown
        options = []
        
        for row in data:
            dept_name = row.get('department_name')
            if dept_name:
                options.append({'label': dept_name, 'value': dept_name})
        
        return options
    except Exception as e:
        print(f"Ошибка при загрузке подразделений: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


# Callback для обновления статистики
@callback(
    Output(f'stats-content-{type_page}', 'children'),
    Input(f'update-button-{type_page}', 'n_clicks'),
    [
        State(f'switch-working-only-{type_page}', 'value'),
        State(f'radio-show-mode-{type_page}', 'value'),
        State(f'dropdown-status-filter-{type_page}', 'value'),
        State(f'dropdown-process-filter-{type_page}', 'value'),
        State(f'dropdown-category-filter-{type_page}', 'value'),
        State(f'dropdown-department-filter-{type_page}', 'value')
    ]
)
def update_stats(n_clicks, show_working_only, show_mode, status_filter, process_filter, category_filter, department_filter):
    if not n_clicks:
        return html.Div("Нажмите 'Обновить' для загрузки статистики", className="text-muted")
    
    try:
        # Получаем данные для статистики (без фильтра по статусу)
        show_only_latest = (show_mode == 'latest')
        
        filter_category = None if category_filter == 'all' else category_filter
        filter_department_name = department_filter if department_filter else None
        
        sql_query = sql_query_digital_signatures(
            show_only_latest=show_only_latest,
            show_working_only=show_working_only,
            filter_expiring=None,  # Получаем все для статистики
            filter_category=filter_category,
            filter_department_name=filter_department_name
        )
        
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        if not data:
            return html.Div("Нет данных для отображения", className="text-muted")

        # Фильтры
        if status_filter != 'all':
            if status_filter == 'expiring_60':
                data = [row for row in data if row.get('status') in ['expiring_60', 'expiring_30', 'expiring_7']]
            elif status_filter == 'expiring_30':
                data = [row for row in data if row.get('status') in ['expiring_30', 'expiring_7']]
            elif status_filter == 'expiring_7':
                data = [row for row in data if row.get('status') == 'expiring_7']
            elif status_filter == 'expired':
                data = [row for row in data if row.get('status') == 'expired']
            elif status_filter == 'revoked':
                data = [row for row in data if row.get('status') == 'revoked']

        if process_filter != 'all':
            data = [row for row in data if row.get('process_status') == process_filter]

        if not data:
            return html.Div("Нет данных с выбранными фильтрами", className="text-muted")
        
        # Подсчитываем статистику
        total = len(data)
        active = sum(1 for row in data if row.get('status') == 'active')
        expiring_60 = sum(1 for row in data if row.get('status') in ['expiring_60', 'expiring_30', 'expiring_7'])
        expiring_30 = sum(1 for row in data if row.get('status') in ['expiring_30', 'expiring_7'])
        expiring_7 = sum(1 for row in data if row.get('status') == 'expiring_7')
        expired = sum(1 for row in data if row.get('status') == 'expired')
        revoked = sum(1 for row in data if row.get('status') == 'revoked')
        
        # Уникальные сотрудники
        unique_persons = len(set(row.get('person_id') for row in data if row.get('person_id')))
        
        # Сотрудники с просроченными ЭЦП
        persons_with_expired = len(set(
            row.get('person_id') for row in data 
            if row.get('status') == 'expired' and row.get('person_id')
        ))
        
        # Сотрудники с истекающими ЭЦП (≤60 дней)
        persons_with_expiring = len(set(
            row.get('person_id') for row in data 
            if row.get('status') in ['expiring_60', 'expiring_30', 'expiring_7'] and row.get('person_id')
        ))

        process_counts = {
            'no_actions': 0,
            'notification_uploaded': 0,
            'application_created': 0,
            'new_certificate_ready': 0,
            'active_certificate': 0,
        }
        for row in data:
            ps = row.get('process_status')
            if ps in process_counts:
                process_counts[ps] += 1
        
        # Формируем карточки статистики
        stats_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(total, className="text-primary mb-1"),
                        html.P("Всего ЭЦП", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width={"size": 2, "offset": 0}),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(unique_persons, className="text-info mb-1"),
                        html.P("Сотрудников", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(active, className="text-success mb-1"),
                        html.P("Активных", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(expiring_60, className="text-warning mb-1"),
                        html.P("Истекают (≤60 дней)", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(expiring_30, className="text-warning mb-1"),
                        html.P("Истекают (≤30 дней)", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(expiring_7, className="text-danger mb-1"),
                        html.P("Истекают (≤7 дней)", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(expired, className="text-danger mb-1"),
                        html.P("Просрочено", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
        ], className="g-3")

        process_cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(process_counts['no_actions'], className="text-secondary mb-1"),
                        html.P("Нет действий", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(process_counts['notification_uploaded'], className="text-warning mb-1"),
                        html.P("Уведомление", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(process_counts['application_created'], className="text-warning mb-1"),
                        html.P("Заявление", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(process_counts['new_certificate_ready'], className="text-success mb-1"),
                        html.P("Новая ЭЦП готова", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(process_counts['active_certificate'], className="text-success mb-1"),
                        html.P("ЭЦП действует", className="text-muted mb-0", style={"font-size": "0.9rem"})
                    ])
                ], className="text-center")
            ], width=3),
        ], className="g-3 mt-2")
        
        # Дополнительная информация
        additional_info = dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.Strong("Требуют внимания: "),
                    f"{persons_with_expired} сотрудников с просроченными ЭЦП, ",
                    f"{persons_with_expiring} сотрудников с истекающими ЭЦП (≤60 дней)"
                ], color="warning" if (persons_with_expired > 0 or persons_with_expiring > 0) else "success")
            ], width=12)
        ], className="mt-3")
        
        return html.Div([stats_cards, process_cards, additional_info])
        
    except Exception as e:
        print(f"Ошибка при обновлении статистики: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Ошибка загрузки статистики: {str(e)}", className="text-danger")


# Callback для обновления таблицы
@callback(
    [
        Output(f'result-table-{type_page}', 'columns'),
        Output(f'result-table-{type_page}', 'data'),
        Output(f'result-table-{type_page}', 'style_data_conditional')
    ],
    Input(f'update-button-{type_page}', 'n_clicks'),
    [
        State(f'switch-working-only-{type_page}', 'value'),
        State(f'radio-show-mode-{type_page}', 'value'),
        State(f'dropdown-status-filter-{type_page}', 'value'),
        State(f'dropdown-process-filter-{type_page}', 'value'),
        State(f'dropdown-category-filter-{type_page}', 'value'),
        State(f'dropdown-department-filter-{type_page}', 'value')
    ]
)
def update_table(n_clicks, show_working_only, show_mode, status_filter, process_filter, category_filter, department_filter):
    if not n_clicks:
        return [], [], []
    
    try:
        # Определяем параметры запроса
        show_only_latest = (show_mode == 'latest')
        
        # Преобразуем фильтр статуса
        filter_expiring = None
        if status_filter == 'expiring_60':
            filter_expiring = 'expiring_60'
        elif status_filter == 'expiring_30':
            filter_expiring = 'expiring_30'
        elif status_filter == 'expiring_7':
            filter_expiring = 'expiring_7'
        elif status_filter == 'expired':
            filter_expiring = 'expired'
        elif status_filter == 'active':
            filter_expiring = None  # Будем фильтровать в Python
        
        # Определяем фильтры
        filter_category = None if category_filter == 'all' else category_filter
        filter_department_name = department_filter if department_filter else None
        
        # Выполняем запрос
        sql_query = sql_query_digital_signatures(
            show_only_latest=show_only_latest,
            show_working_only=show_working_only,
            filter_expiring=filter_expiring,
            filter_category=filter_category,
            filter_department_name=filter_department_name
        )
        
        columns, data = TableUpdater.query_to_df(engine, sql_query)
        
        # Дополнительная фильтрация по активным (если нужно)
        if status_filter == 'active':
            data = [row for row in data if row.get('status') == 'active']
        elif status_filter == 'revoked':
            data = [row for row in data if row.get('status') == 'revoked']

        # Фильтрация по процессу
        if process_filter != 'all':
            data = [row for row in data if row.get('process_status') == process_filter]
        
        # Форматируем колонки
        formatted_columns = [
            {'name': 'ФИО', 'id': 'fio'},
            {'name': 'СНИЛС', 'id': 'snils'},
            {'name': 'ИНН', 'id': 'inn'},
            {'name': 'Телефон', 'id': 'phone_number'},
            {'name': 'Категория', 'id': 'category'},
            {'name': 'Подразделение', 'id': 'department_name'},
            {'name': 'Должность', 'id': 'position_name'},
            {'name': 'Действует с', 'id': 'valid_from'},
            {'name': 'Действует по', 'id': 'valid_to'},
            {'name': 'Дней до истечения', 'id': 'days_until_expiration', 'type': 'numeric'},
            {'name': 'Статус', 'id': 'status'},
            {'name': 'Дата выдачи', 'id': 'issued_date'},
            {'name': 'Дата аннулирования', 'id': 'revoked_date'},
            {'name': 'Файл выписки', 'id': 'has_scan'},
            {'name': 'Статус процессов', 'id': 'process_status_display'},
            {'name': 'Действие', 'id': 'action', 'presentation': 'markdown'},
        ]
        
        # Преобразуем is_replaced в строку для filter_query
        for row in data:
            if 'is_replaced' in row:
                row['is_replaced'] = 'true' if row['is_replaced'] else 'false'
            
            # Добавляем ссылки на редактирование и создание новой ЭЦП
            signature_id = row.get('id')
            person_id = row.get('person_id')
            
            action_links = []
            
            # Ссылка на редактирование существующей ЭЦП
            if signature_id:
                admin_url = f"http://10.136.29.166:8000/admin/personnel/digitalsignature/{signature_id}/change/"
                action_links.append(f"[Открыть]({admin_url})")
            
            # Ссылка на создание новой ЭЦП для сотрудника
            if person_id:
                position_id = row.get('position_id')
                if position_id:
                    create_url = f"http://10.136.29.166:8000/admin/personnel/digitalsignature/add/?person={person_id}&position={position_id}"
                else:
                    create_url = f"http://10.136.29.166:8000/admin/personnel/digitalsignature/add/?person={person_id}"
                action_links.append(f"[Создать]({create_url})")
            
            # Объединяем ссылки с переносом строки (двойной перенос для markdown)
            row['action'] = "  \n".join(action_links) if action_links else ""
        
        # Форматируем даты
        for row in data:
            for date_field in ['valid_from', 'valid_to', 'issued_date', 'revoked_date', 'application_date']:
                if row.get(date_field):
                    try:
                        # Парсим дату из строки или объекта
                        if isinstance(row[date_field], str):
                            date_obj = datetime.strptime(row[date_field].split()[0], '%Y-%m-%d')
                            row[date_field] = date_obj.strftime('%d.%m.%Y')
                        elif hasattr(row[date_field], 'strftime'):
                            row[date_field] = row[date_field].strftime('%d.%m.%Y')
                    except:
                        pass
        
        # Форматируем статус для отображения
        status_labels = {
            'active': 'Активна',
            'expiring_60': 'Заканчивается (≤60 дней)',
            'expiring_30': 'Заканчивается (≤30 дней)',
            'expiring_7': 'Заканчивается (≤7 дней)',
            'expired': 'Просрочена',
            'revoked': 'Аннулирована',
            'no_end_date': 'Без даты окончания'
        }
        
        process_status_labels = {
            'no_actions': 'Нет действий',
            'notification_uploaded': 'Уведомление загружено',
            'application_created': 'Заявление создано',
            'new_certificate_ready': 'Новая ЭЦП готова',
            'active_certificate': 'ЭЦП действует',
        }

        for row in data:
            status = row.get('status', '')
            row['status'] = status_labels.get(status, status)
            
            # Форматируем категорию
            category = row.get('category', 'none')
            category_labels = {
                'doctor': 'Врач',
                'staff': 'Сотрудник',
                'both': 'Врач/Сотрудник',
                'none': '-'
            }
            row['category'] = category_labels.get(category, category)
            
            # Добавляем индикатор наличия файла выписки
            scan = row.get('scan')
            if scan:
                row['has_scan'] = '✓ Есть'
            else:
                row['has_scan'] = '✗ Нет'

            # Читаемый статус процесса
            process_status = row.get('process_status')
            process_display = process_status_labels.get(process_status, 'Нет действий')

            if process_status == 'active_certificate':
                if status == 'Заканчивается (≤7 дней)':
                    process_display = 'ЭЦП истекает (≤7 дней)'
                elif status == 'Заканчивается (≤30 дней)':
                    process_display = 'ЭЦП истекает (≤30 дней)'
                elif status == 'Заканчивается (≤60 дней)':
                    process_display = 'ЭЦП истекает (≤60 дней)'
                else:
                    process_display = 'ЭЦП действует'

            row['process_status_display'] = process_display
        
        # Условное форматирование строк
        style_data_conditional = []
        
        # Правила форматирования на основе filter_query
        # Просроченные (красный)
        style_data_conditional.append({
            'if': {
                'filter_query': '{status} = "Просрочена" || {days_until_expiration} < 0'
            },
            'backgroundColor': '#f8d7da',
            'color': '#721c24'
        })
        
        # Выделение наличия файла выписки
        style_data_conditional.append({
            'if': {
                'filter_query': '{has_scan} = "✓ Есть"',
                'column_id': 'has_scan'
            },
            'backgroundColor': '#d4edda',
            'color': '#155724',
            'fontWeight': 'bold'
        })
        
        style_data_conditional.append({
            'if': {
                'filter_query': '{has_scan} = "✗ Нет"',
                'column_id': 'has_scan'
            },
            'backgroundColor': '#f8d7da',
            'color': '#721c24'
        })
        
        # Заканчиваются в течение 7 дней (оранжевый)
        style_data_conditional.append({
            'if': {
                'filter_query': '{status} = "Заканчивается (≤7 дней)" || ({days_until_expiration} >= 0 && {days_until_expiration} <= 7)'
            },
            'backgroundColor': '#ffc107',
            'color': '#856404'
        })
        
        # Заканчиваются в течение 30 дней (желтый)
        style_data_conditional.append({
            'if': {
                'filter_query': '{status} = "Заканчивается (≤30 дней)" || ({days_until_expiration} > 7 && {days_until_expiration} <= 30)'
            },
            'backgroundColor': '#fff3cd',
            'color': '#856404'
        })
        
        # Заканчиваются в течение 60 дней (светло-желтый)
        style_data_conditional.append({
            'if': {
                'filter_query': '{status} = "Заканчивается (≤60 дней)" || ({days_until_expiration} > 30 && {days_until_expiration} <= 60)'
            },
            'backgroundColor': '#fffef0',
            'color': '#856404'
        })
        
        # Переоформленные (синий) - только если показываем все ЭЦП
        if show_mode == 'all':
            style_data_conditional.append({
                'if': {
                    'filter_query': '{is_replaced} = true'
                },
                'backgroundColor': '#cfe2ff',
                'color': '#084298'
            })

        # Цвета по статусу процесса
        style_data_conditional.extend([
            {
                'if': {'filter_query': '{process_status_display} = "Уведомление загружено"', 'column_id': 'process_status_display'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'filter_query': '{process_status_display} = "Заявление создано"', 'column_id': 'process_status_display'},
                'backgroundColor': '#ffe8a1',
                'color': '#7a5200'
            },
            {
                'if': {'filter_query': '{process_status_display} = "Новая ЭЦП готова"', 'column_id': 'process_status_display'},
                'backgroundColor': '#d4edda',
                'color': '#155724'
            }
        ])
        
        return formatted_columns, data, style_data_conditional
        
    except Exception as e:
        print(f"Ошибка при обновлении таблицы: {str(e)}")
        import traceback
        traceback.print_exc()
        return [], [], []


# Экспортируем layout
admin_digital_signatures = layout()

