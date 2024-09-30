from services.MosaicMed.callback.callback import get_current_reporting_month
from services.MosaicMed.generate_pages.constants import months_sql_labels


def get_selected_period(selected_months_range, selected_year, current_month_name):
    if selected_months_range and selected_year:
        current_month_num, _ = get_current_reporting_month()
        selected_period = []
        for i in range(selected_months_range[0], selected_months_range[1] + 1):
            month_label = f"{months_sql_labels[i]} {selected_year}"
            if i == current_month_num:
                selected_period.append(month_label)
                selected_period.append('-')
            else:
                selected_period.append(month_label)
        return selected_period
    else:
        return []