from sqlalchemy import text
from datetime import datetime, timedelta


current_year = datetime.now().year


def date_r():
    date_start_rep = datetime.now()
    day_list = ['01', '02', '03', '04', '05']

    date = date_start_rep
    day_str = date.strftime("%d")
    if day_str in day_list:
        date = (date_start_rep - timedelta(days=10))
        mon = date.strftime("%m")
    else:
        mon = date.strftime("%m")
    return mon


current_month = date_r()

months_labels = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль',
    8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}

months_sql_labels = {
    1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля', 5: 'Мая', 6: 'Июня', 7: 'Июля',
    8: 'Августа', 9: 'Сентября', 10: 'Октября', 11: 'Ноября', 12: 'Декабря'
}

# Словарь для группировки статусов
status_groups = {
    'Оплаченные (3)': ['3'],
    'Предъявленные и оплаченные (2, 3)': ['2', '3'],
    'Предъявленные первичные (1, 2, 3)': ['1', '2', '3'],
    'Предъявленные первичные и повторные (1, 2, 3, 4, 6, 8)': ['1', '2', '3', '4', '6', '8'],
    'Все статусы': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '12', '13', '17']
}
