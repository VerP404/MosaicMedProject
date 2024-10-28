from datetime import datetime, timedelta
from dash import dcc, html
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.query_executor import engine
from apps.analytical_app.utils import build_sql_filters

# Словарь для группировки статусов
status_groups = {
    'Оплаченные (3)': ['3'],
    'Предъявленные и оплаченные (2, 3)': ['2', '3'],
    'Предъявленные первичные (1, 2, 3)': ['1', '2', '3'],
    'Предъявленные первичные и повторные (1, 2, 3, 4, 6, 8)': ['1', '2', '3', '4', '6', '8'],
    'Все статусы': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '12', '13', '17']
}
months_dict = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
    7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}
months_labels = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль',
    8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}
months_sql_labels = {
    1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля', 5: 'Мая', 6: 'Июня', 7: 'Июля',
    8: 'Августа', 9: 'Сентября', 10: 'Октября', 11: 'Ноября', 12: 'Декабря'
}
current_year = datetime.now().year


# получаем текущий отчетный месяц (по 4 число следующего за отчетным)
def get_current_reporting_month():
    current_date = datetime.now()
    current_day = current_date.day
    current_month_number = current_date.month

    if current_day <= 4:
        if current_month_number == 1:
            current_month_number = 12
        else:
            current_month_number = current_month_number - 1
    current_month_name = f"Текущий отчетный месяц: {months_dict.get(current_month_number)}"
    return current_month_number, current_month_name


def get_available_buildings():
    query = """
        SELECT id, name
        FROM organization_building
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        buildings = [{'label': row[1], 'value': row[0]} for row in result.fetchall()]  # Доступ через индексы
    return buildings


def get_available_departments(building_id=None):
    # Проверяем, передан ли building_id и не является ли он пустым
    if building_id:
        # Если передан не список, преобразуем в список
        if not isinstance(building_id, list):
            building_id = [building_id]  # Преобразуем в список, если передано одно значение

        # Проверяем, что список не пустой
        if building_id:
            building_id_str = ', '.join(map(str, building_id))
            query = f"""
                SELECT id, name
                FROM organization_department
                WHERE building_id IN ({building_id_str})
            """
        else:
            # Если список пустой, выбираем все отделения
            query = """
                SELECT id, name
                FROM organization_department
            """
    else:
        # Если building_id равен None, выбираем все отделения
        query = """
            SELECT id, name
            FROM organization_department
        """

    with engine.connect() as connection:
        result = connection.execute(text(query))
        departments = [{'label': row[1], 'value': row[0]} for row in result.fetchall()]
    return departments


def filter_building(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-building-{type_page}',
            placeholder='Выберите корпус...',
            clearable=True,
            multi=True,
            options=get_available_buildings(),
        ),
        style={"width": "100%"}
    )


def filter_department(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-department-{type_page}',
            placeholder='Выберите отделение...',
            clearable=True,
            multi=True,
            options=[],
        ),
        style={"width": "100%"}
    )


def get_available_profiles(building_ids=None, department_ids=None):
    filters = build_sql_filters(building_ids=building_ids, department_ids=department_ids)

    query = f"""
        SELECT DISTINCT profile.id, profile.description
        FROM personnel_doctorrecord doctor
        JOIN personnel_profile profile ON profile.id = doctor.profile_id
        JOIN organization_department department ON department.id = doctor.department_id
        WHERE 1=1
        {filters}
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        profiles = [{'label': row[1], 'value': row[0]} for row in result.fetchall()]
    return profiles


def get_available_doctors(building_ids=None, department_ids=None, profile_ids=None):
    filters = build_sql_filters(building_ids=building_ids, department_ids=department_ids, profile_ids=profile_ids)

    query = f"""
        SELECT ARRAY_AGG(doctor.id) AS doctor_ids,
               CONCAT(person.last_name, ' ', SUBSTRING(person.first_name, 1, 1), '.', SUBSTRING(person.patronymic, 1, 1), '. - ',
                      CASE 
                          WHEN pp.description = 'общей врачебной практике (семейной медицине)' THEN 'ВОП'
                          WHEN pp.description = 'акушерству и гинекологии (за исключением использования вспомогательных репродуктивных технологий и искусственного прерывания беременности)' THEN 'акушерству и гинекологии'
                        ELSE pp.description
                      END) AS doctor_info
        FROM personnel_doctorrecord doctor
        JOIN personnel_person person ON person.id = doctor.person_id
        JOIN organization_department department ON department.id = doctor.department_id
        JOIN personnel_profile pp ON pp.id = doctor.profile_id
        WHERE 1=1
        {filters}
        GROUP BY person.last_name, person.first_name, person.patronymic, pp.description, department.name
    """

    with engine.connect() as connection:
        result = connection.execute(text(query))
        doctors = [{'label': row[1], 'value': ','.join(map(str, row[0]))} for row in result.fetchall()]
    return doctors


def filter_profile(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-profile-{type_page}',
            options=[],  # Initially empty, will be filled by callback
            placeholder='Выберите профиль...',
            clearable=True,
            multi=True,
        ),
        style={"width": "100%"}
    )


def filter_doctor(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-doctor-{type_page}',
            options=[],  # Initially empty, will be filled by callback
            placeholder='Выберите врача...',
            clearable=True,
            multi=True,
        ),
        style={"width": "100%"}
    )


def filter_years(type_page):
    # Генерируем список годов от 2023 до текущего года
    year_options = [{'label': str(year), 'value': year} for year in range(2023, current_year + 1)]

    return dbc.Col(
        dcc.Dropdown(
            options=year_options,
            id=f'dropdown-year-{type_page}',
            placeholder='Выберите год...',
            value=current_year,  # Текущий год выбран по умолчанию
            clearable=False
        ),
        style={"width": "100%"}

    )


def update_buttons(type_page):
    return dbc.Col(
        dbc.Button("Обновить", id=f'update-button-{type_page}', color="primary",
                   className="mt-3"),
        style={"text-align": "center"}
    ),


def filter_inogorod(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-inogorodniy-{type_page}',
            options=[
                {'label': 'Местные', 'value': '1'},
                {'label': 'Иногородние', 'value': '2'},
                {'label': 'Все', 'value': '3'}
            ],
            value='1',
            clearable=False
        ),
        style={"width": "100%"}
    )


def filter_sanction(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-sanction-{type_page}',
            options=[
                {'label': 'Без санкций', 'value': '1'},
                {'label': 'Санкции', 'value': '2'},
                {'label': 'Все', 'value': '3'}
            ],
            value='1',
            clearable=False
        ),
        style={"width": "100%"}
    )


def filter_report_type(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-report-type-{type_page}',
            options=[
                {'label': 'По отчетному месяцу', 'value': 'month'},
                {'label': 'По дате формирования', 'value': 'initial_input'},
                {'label': 'По дате лечения', 'value': 'treatment'}
            ],
            value='month',
            clearable=False
        ),
        style={"width": "100%"}
    )


def filter_amount_null(type_page):
    return dbc.Col(
        dcc.Dropdown(
            id=f'dropdown-amount-null-{type_page}',
            options=[
                {'label': 'Не нулевые', 'value': '1'},
                {'label': 'Нулевые', 'value': '2'},
                {'label': 'Все', 'value': '3'}
            ],
            value='1',
            clearable=False
        ),
        style={"width": "100%"}
    )


def filter_doctors(type_page):
    return html.Div(
        dcc.Dropdown(
            id=f'dropdown-doctor-{type_page}',
            options=[],  # Initially empty, will be filled by callback
            value=None,
            multi=False,
            placeholder="Выберите врача"
        ),
        style={"width": "100%"}
    )


def filter_months(type_page):
    cur_month_num, _ = get_current_reporting_month()
    return (
        dbc.Col(
            dcc.RangeSlider(
                id=f'range-slider-month-{type_page}',
                min=1,
                max=12,
                marks={i: month for i, month in months_labels.items()},
                value=[cur_month_num, cur_month_num],
                step=1
            )
        )
    )


def date_start(label, type_page):
    return (
        dbc.Col(
            html.Div([
                html.Label(label, style={'width': '200px', 'display': 'inline-block'}),
                dcc.DatePickerSingle(
                    id=f'date-start-{type_page}',
                    first_day_of_week=1,
                    date=(datetime.now() - timedelta(days=1)).date(),
                    display_format='DD.MM.YYYY',
                    className='filter-date'
                ),
            ], className='filters'),
            width=3
        ))


def date_end(label, type_page):
    return (
        dbc.Col(
            html.Div([
                html.Label(label, style={'width': '200px', 'display': 'inline-block'}),
                dcc.DatePickerSingle(
                    id=f'date-end-{type_page}',
                    first_day_of_week=1,
                    date=(datetime.now() - timedelta(days=1)).date(),
                    display_format='DD.MM.YYYY',
                    className='filter-date'
                ),
            ], className='filters'),
            width=3,
        ))


def filter_status(type_page):
    return (
        dbc.CardBody(
            dcc.RadioItems(
                id=f'status-group-radio-{type_page}',
                options=[{'label': group, 'value': group} for group in status_groups.keys()],
                value='Предъявленные и оплаченные (2, 3)',
                labelStyle={'display': 'block'}
            )
        )
    )


def filter_goals_and_categories():
    return dbc.Col(
        [
            dbc.RadioItems(
                id='filter-goals-categories',
                options=[
                    {'label': 'По целям', 'value': 'goals'},
                    {'label': 'По категориям', 'value': 'categories'}
                ],
                value='goals',  # По умолчанию фильтр по целям
                inline=True
            )
        ]
    )


def date_picker(type_page):
    # Вычисляем вчерашнюю дату
    yesterday = datetime.now() - timedelta(days=1)
    week_ago = datetime.now() - timedelta(days=7)

    return html.Div(
        [
            dcc.DatePickerRange(
                id=f'date-picker-range-{type_page}',
                start_date_placeholder_text="Начало",
                end_date_placeholder_text="Конец",
                start_date=week_ago,
                end_date=yesterday,
                display_format="DD.MM.YYYY",
                calendar_orientation='horizontal',
                style={'margin': '10px'},
                first_day_of_week=1
            )
        ]
    )


def get_departments_by_doctor(doctor_id):
    # Если doctor_id передан как список, берем первый элемент
    if isinstance(doctor_id, list) and doctor_id:
        doctor_id = doctor_id[0]

    query = """
        SELECT DISTINCT department.id, department.name
        FROM organization_department department
        JOIN personnel_doctorrecord doctor ON doctor.department_id = department.id
        WHERE doctor.id = :doctor_id
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), {'doctor_id': doctor_id})
        departments = [{'label': row[1], 'value': row[0]} for row in result.fetchall()]

    # Добавляем опцию "Все" в начало списка
    departments.insert(0, {'label': 'Все', 'value': 'all'})
    return departments


def get_doctor_details(doctor_id):
    query = """
        SELECT 
            CONCAT(p.last_name, ' ', SUBSTRING(p.first_name FROM 1 FOR 1), '.', SUBSTRING(p.patronymic FROM 1 FOR 1), '.') AS doctor_name,
            s.description AS specialty,
            d.name AS department,
            b.name AS building
        FROM personnel_person p
        JOIN personnel_doctorrecord dr ON p.id = dr.person_id
        JOIN personnel_specialty s ON dr.specialty_id = s.id
        JOIN organization_department d ON dr.department_id = d.id
        JOIN organization_building b ON d.building_id = b.id
        WHERE dr.id = :doctor_id
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), {'doctor_id': doctor_id}).fetchone()
    if result:
        return {
            'doctor_name': result[0],
            'specialty': result[1],
            'department': result[2],
            'building': result[3]
        }
    return None
