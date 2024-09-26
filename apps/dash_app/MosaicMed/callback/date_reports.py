from datetime import datetime


def get_current_reporting_month():
    current_date = datetime.now()
    current_day = current_date.day
    cur_month_number = current_date.month
    if current_day <= 4:
        if cur_month_number == 1:  # для января возвращаем декабрь
            cur_month_number = 12
        else:
            cur_month_number = cur_month_number - 1
    months_dict = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
        7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    cur_month_name = f"Текущий отчетный месяц: {months_dict.get(cur_month_number)}"
    return cur_month_number, cur_month_name


def update_current_month(n_intervals):
    current_month_num, current_month_name = get_current_reporting_month()
    return current_month_num


def get_selected_year(selected_year):
    if selected_year:
        return [f"{selected_year}", "-"]
    else:
        return []