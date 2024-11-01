import dash_bootstrap_components as dbc
from dash import html, dash_table

from apps.analytical_app.components.filters import get_current_reporting_month, months_sql_labels


# Функция для создания таблицы с возможностью выбора колонок
def card_table(id_table, card_header, page_size=None, column_selectable=None):
    table_kwargs = {
        'id': id_table,
        'editable': False,
        'filter_action': "native",
        'sort_action': "native",
        'sort_mode': 'multi',
        'export_format': 'xlsx',
        'export_headers': 'display',
        'style_table': {'overflowX': 'auto'},
        'style_cell': {'minWidth': '0px', 'maxWidth': '180px', 'whiteSpace': 'normal'}
    }

    if page_size is not None:
        table_kwargs['page_size'] = page_size

    if column_selectable is not None:
        table_kwargs['column_selectable'] = column_selectable

    return (
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader(card_header),
                            html.Div(
                                dash_table.DataTable(**table_kwargs),
                                style={"maxWidth": "100%", "overflowX": "auto"}
                            ),
                            dbc.Row([
                                dbc.Col(html.Button("Суммировать", id=f'sum-button-{id_table}',
                                                    className="btn btn-primary"), width=4),
                                dbc.Col(html.Div(id=f'sum-result-{id_table}', style={"marginTop": "10px"}), width=4)
                            ]),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        )
    )


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
