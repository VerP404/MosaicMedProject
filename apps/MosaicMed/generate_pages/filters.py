from datetime import datetime, timedelta

from dash import dcc, html
import dash_bootstrap_components as dbc

from services.MosaicMed.callback.callback import get_current_reporting_month
from services.MosaicMed.generate_pages.constants import current_year, months_labels, status_groups


def filter_years(type_page):
    return (
        dbc.Col(
            dcc.Dropdown(options=[
                {'label': '2023', 'value': 2023},
                {'label': '2024', 'value': 2024},
                {'label': '2025', 'value': 2025}
            ], id=f'dropdown-year-{type_page}', placeholder='Выберите год...',
                value=current_year)
        ))


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



