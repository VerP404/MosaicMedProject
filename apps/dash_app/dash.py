# dash_app/dash.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
type_page = 'sdf'
markdown_text = """  
"МозаикаМед" - это веб-приложение, созданное для быстрого и удобного доступа к информации и справочным ресурсам в медицинских учреждениях. Этот инструмент предназначен для упрощения работы медицинского персонала с статистическими данными, обеспечивая их анализ и поддержку принятия управленческих решений.

Система позволяет пользователям получать доступ к широкому спектру статистических данных, проводить их анализ и использовать полученные результаты для повышения эффективности работы и улучшения качества медицинских услуг. "МозаикаМед" разработана с учетом потребностей врачей и других медицинских специалистов, способствуя оптимизации их рабочего процесса и улучшению обслуживания пациентов.
"""
# Создаем Dash-приложение, интегрированное с Django
app2 = DjangoDash('DashApp3')

app2.layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(

                            ),
                            dbc.Row(
                                [
                                ]
                            ),
                            html.Div(id=f'selected-doctor-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'selected-period-{type_page}', className='filters-label',
                                     style={'display': 'none'}),
                            html.Div(id=f'current-month-name-{type_page}', className='filters-label'),
                            html.Div(id=f'selected-month-{type_page}', className='filters-label'),
                            html.Button('Получить данные', id=f'get-data-button-{type_page}'),
                            dcc.Loading(id=f'loading-output-{type_page}', type='default'),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
    ],
    style={"padding": "0rem"}
)

