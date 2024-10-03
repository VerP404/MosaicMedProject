from datetime import datetime, timedelta
from dash import dcc, html
import dash_bootstrap_components as dbc

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
        if current_month_number == 1:  # для января возвращаем декабрь
            current_month_number = 12
        else:
            current_month_number = current_month_number - 1
    current_month_name = f"Текущий отчетный месяц: {months_dict.get(current_month_number)}"
    return current_month_number, current_month_name


def filter_years(type_page):
    # Генерируем список годов от 2023 до текущего года
    year_options = [{'label': str(year), 'value': year} for year in range(2023, current_year + 1)]

    return dbc.Col(
        dcc.Dropdown(
            options=year_options,
            id=f'dropdown-year-{type_page}',
            placeholder='Выберите год...',
            value=current_year,  # Текущий год выбран по умолчанию
            clearable=False  # Можно выбрать только один год
        )
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
        dcc.RadioItems(
            id=f'status-group-radio-{type_page}',
            options=[{'label': group, 'value': group} for group in status_groups.keys()],
            value='Предъявленные и оплаченные (2, 3)',
            labelStyle={'display': 'block'}
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

