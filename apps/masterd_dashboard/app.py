import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from datetime import datetime
import dash.exceptions
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

from header import header_func


def get_default_organization_name():
    """Имя дефолтной организации из БД (первая по id)."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "mosaicmed"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM organization_medicalorganization ORDER BY id LIMIT 1"
            )
            row = cur.fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception:
        return ""

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/style.css'])

# Определение цветов и стилей блоков
style_td = {'padding': '0 10px 0 0', 'color': 'green', 'fontSize': '1.1rem'}


def graph_pie(df):
    dff = pd.DataFrame(df)
    fig = px.pie(dff, values="К-во", names="Корпус", title="Численность по корпусам", hole=0.3)
    fig.update_traces(textinfo='label+percent+value', pull=[0, 0, 0, 0, 0, 0], textposition='outside', showlegend=False)
    fig.update(layout=dict(title=dict(x=0.5)))
    fig.update_layout(
        plot_bgcolor='#1f2c56',  # Цвет фона области построения графика
        paper_bgcolor='#1f2c56',  # Цвет фона за пределами области построения графика
        title_x=0.5,  # Горизонтальное положение заголовка по центру
        font=dict(color='white'),  # Цвет шрифта
        # legend=False
        # Установка размера шрифта легенды
    )
    return fig


# Графики
# ДВ4, ОПВ, УД по корпусам
disp = {'Корпус': ['Корпус 1', 'Корпус 2', 'Корпус 3', 'Корпус 6', ],
        'ДВ4': [3880, 1635, 3880, 825],
        'ОПВ': [1686, 588, 1433, 299],
        'УД1': [656, 70, 830, 175]}
df_disp = pd.DataFrame(disp)
df_disp = pd.melt(df_disp, id_vars=['Корпус'], var_name='Тип диспансеризации', value_name='Количество')

# РЭМД/СЭМД по корпусам
remd_semd = {'ЭМД': ['РЭМД', 'СЭМД', 'РЭМД', 'СЭМД', 'РЭМД', 'СЭМД', 'РЭМД', 'СЭМД'],
             'Корпус': ['Корпус 1', 'Корпус 1', 'Корпус 2', 'Корпус 2', 'Корпус 3', 'Корпус 3', 'Корпус 6', 'Корпус 6'],
             'count': [492, 43, 108, 22, 284, 109, 15, 44]}
df_remd_semd = pd.DataFrame(remd_semd)
df_remd_semd['percent'] = df_remd_semd.groupby('Корпус')['count'].transform(lambda x: round(x / x.sum() * 100, 2))

# заболеваемость бСК и ХОБЛ
morbidity = {'Группа': ['БСК', 'ХОБЛ', 'БСК', 'ХОБЛ', 'БСК', 'ХОБЛ', 'БСК', 'ХОБЛ'],
             'Корпус': ['Корпус 1', 'Корпус 1', 'Корпус 2', 'Корпус 2', 'Корпус 3', 'Корпус 3', 'Корпус 6', 'Корпус 6'],
             'count': [342, 13, 124, 5, 167, 16, 102, 2]}
df_morbidity = pd.DataFrame(morbidity)

# диаграмма
# Смертность
data_mortality = {'Корпус': ['Корпус 1', 'Корпус 2', 'Корпус 3', 'Корпус 6'],
                  'всего': [116, 58, 127, 43],
                  'за 7 дней': [11, 6, 13, 8],
                  'вчера': [2, 1, 4, 1]}
df_mortality = pd.DataFrame(data_mortality)

card_container = dbc.Container([
    # Первый ряд - 4 блока
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Доступность первичной записи к ВОП, терапевтам и педиатрам по корпусам на 14 дней", 
                              style={'color': 'red', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('Корпус', style=style_td),
                            html.Td('Выложено', style=style_td),
                            html.Td('Свободно', style=style_td),
                            html.Td('% своб.', style=style_td)]),
                        html.Tr([
                            html.Td('Корпус 1:', style={'padding': '0 10px 0 0'}),
                            html.Td('2 975'),
                            html.Td('2 607'),
                            html.Td('88 %')]),
                        html.Tr([
                            html.Td('Корпус 2:'),
                            html.Td('1 581'),
                            html.Td('1 449'),
                            html.Td('92 %')]),
                        html.Tr([
                            html.Td('Корпус 3:'),
                            html.Td('2 330'),
                            html.Td('1 624'),
                            html.Td('70 %')]),
                        html.Tr([
                            html.Td('Корпус 6:'),
                            html.Td('510'),
                            html.Td('301'),
                            html.Td('59 %')]),
                        html.Tr([
                            html.Td('ДП 1:'),
                            html.Td('2 122'),
                            html.Td('1 552'),
                            html.Td('73 %')]),
                        html.Tr([
                            html.Td('ДП 8:'),
                            html.Td('1 021'),
                            html.Td('630'),
                            html.Td('62 %')]),
                        html.Tr([
                            html.Td('Итого:'),
                            html.Td('10 539'),
                            html.Td('8 163'),
                            html.Td('77 %')]),
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Динамика доступности на 14 дней по специальностям", 
                              style={'color': 'red', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('Специальность', style=style_td),
                            html.Td('Выложено', style=style_td),
                            html.Td('Свободно', style=style_td),
                            html.Td('% своб.', style=style_td)]),
                        html.Tr([
                            html.Td('Акушер-гинеколог', style={'padding': '0 10px 0 0'}),
                            html.Td('1 242'),
                            html.Td('718'),
                            html.Td('58 %')]),
                        html.Tr([
                            html.Td('Отоларинголог', style={'padding': '0 10px 0 0'}),
                            html.Td('755'),
                            html.Td('446'),
                            html.Td('59 %')]),
                        html.Tr([
                            html.Td('Офтальмолог', style={'padding': '0 10px 0 0'}),
                            html.Td('747'),
                            html.Td('238'),
                            html.Td('32 %')]),
                        html.Tr([
                            html.Td('Хирург', style={'padding': '0 10px 0 0'}),
                            html.Td('824'),
                            html.Td('648'),
                            html.Td('79 %')]),
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Динамика выданных свидетельств о смерти по корпусам", 
                              style={'color': 'red', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('Корпус', style=style_td),
                            html.Td('всего', style=style_td),
                            html.Td('за 7 дней', style=style_td),
                            html.Td('вчера', style=style_td)]),
                        html.Tr([
                            html.Td('Корпус 1:', style={'padding': '0 10px 0 0'}),
                            html.Td('116'),
                            html.Td('11', style={'color': 'orange'}),
                            html.Td('2', style={'color': 'red'})]),
                        html.Tr([
                            html.Td('Корпус 2:'),
                            html.Td('58'),
                            html.Td('6', style={'color': 'orange'}),
                            html.Td('1', style={'color': 'red'})]),
                        html.Tr([
                            html.Td('Корпус 3:'),
                            html.Td('127'),
                            html.Td('13', style={'color': 'orange'}),
                            html.Td('4', style={'color': 'red'})]),
                        html.Tr([
                            html.Td('Корпус 6:'),
                            html.Td('43'),
                            html.Td('8', style={'color': 'orange'}),
                            html.Td('1', style={'color': 'red'})]),
                        html.Tr([
                            html.Td('ДП 1:'),
                            html.Td('0'),
                            html.Td('0'),
                            html.Td('0')]),
                        html.Tr([
                            html.Td('ДП 8:'),
                            html.Td('0'),
                            html.Td('0'),
                            html.Td('0')]),
                        html.Tr([
                            html.Td('Итого:'),
                            html.Td('344'),
                            html.Td('38', style={'color': 'orange'}),
                            html.Td('8', style={'color': 'red'})])
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Динамика обратившихся по корпусам", 
                              style={'color': 'red', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('Корпус', style=style_td),
                            html.Td('всего', style=style_td),
                            html.Td('за 7 дней', style=style_td),
                            html.Td('вчера', style=style_td)]),
                        html.Tr([
                            html.Td('Корпус 1:', style={'padding': '0 10px 0 0'}),
                            html.Td('2 060'),
                            html.Td('1 743'),
                            html.Td('290')]),
                        html.Tr([
                            html.Td('Корпус 2:'),
                            html.Td('355'),
                            html.Td('325'),
                            html.Td('45')]),
                        html.Tr([
                            html.Td('Корпус 3:'),
                            html.Td('1 506'),
                            html.Td('1 188'),
                            html.Td('206')]),
                        html.Tr([
                            html.Td('Корпус 6:'),
                            html.Td('314'),
                            html.Td('285'),
                            html.Td('52')]),
                        html.Tr([
                            html.Td('ЖК:'),
                            html.Td('49'),
                            html.Td('43'),
                            html.Td('4')]),
                        html.Tr([
                            html.Td('ДП 1:'),
                            html.Td('1 187'),
                            html.Td('772'),
                            html.Td('170')]),
                        html.Tr([
                            html.Td('ДП 8:'),
                            html.Td('369'),
                            html.Td('242'),
                            html.Td('54')]),
                        html.Tr([
                            html.Td('Итого:'),
                            html.Td('5 840'),
                            html.Td('4 598'),
                            html.Td('821')])
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
    ], className="mb-4"),
    
    # Второй ряд - 4 графика
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ДОГВН, ПМО, УД по корпусам", 
                              style={'color': 'coral', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    dcc.Graph(
                        id='corpus-bar-chart-1',
                        figure=px.bar(df_disp, x="Корпус", y="Количество", color='Тип диспансеризации',
                                      barmode='group',
                                      labels={'Количество': 'Количество', 'Корпус': '',
                                              'Тип диспансеризации': 'Тип диспансеризации'},
                                      ).update_layout(plot_bgcolor='#1f2c56',
                                                      paper_bgcolor='#1f2c56',
                                                      title_x=0.5,
                                                      font=dict(color='white'),
                                                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                                      ),
                        style={'height': '100%', 'minHeight': '250px'}
                    )
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("РЭМД/СЭМД по корпусам", 
                              style={'color': 'coral', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    dcc.Graph(
                        id='corpus-bar-chart-2',
                        figure=px.bar(df_remd_semd, x="Корпус", y="count", color="ЭМД",
                                      text=df_remd_semd['count'].astype(str) + ' (' + df_remd_semd['percent'].astype(str) + '%)',
                                      labels={'count': 'Количество', 'Корпус': '', 'ЭМД': 'Тип документа'},
                                      barmode='stack').update_layout(plot_bgcolor='#1f2c56',
                                                                     paper_bgcolor='#1f2c56',
                                                                     title_x=0.5,
                                                                     font=dict(color='white'),
                                                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                                                     ),
                        style={'height': '100%', 'minHeight': '250px'}
                    )
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Смертность по корпусам", 
                              style={'color': 'coral', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    dcc.Graph(
                        id='corpus-pie-1',
                        figure=px.pie(df_mortality, values="всего", names="Корпус", hole=0.3).update_layout(
                            plot_bgcolor='#1f2c56',
                            paper_bgcolor='#1f2c56',
                            title_x=0.5,
                            font=dict(color='white'),
                        ).update_traces(textinfo='label+percent+value', showlegend=False),
                        style={'height': '100%', 'minHeight': '250px'}
                    )
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Заболеваемость БСК и ХОБЛ", 
                              style={'color': 'coral', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    dcc.Graph(
                        id='corpus-bar-chart-3',
                        figure=px.bar(df_morbidity, x="Корпус", y="count", color="Группа",
                                      text="count",
                                      labels={'count': 'Количество', 'Корпус': '', 'Группа': 'Группа'},
                                      barmode='stack').update_layout(plot_bgcolor='#1f2c56',
                                                                     paper_bgcolor='#1f2c56',
                                                                     title_x=0.5,
                                                                     font=dict(color='white'),
                                                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                                                     ),
                        style={'height': '100%', 'minHeight': '250px'}
                    )
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
    ], className="mb-4"),
    
    # Третий ряд - 4 блока
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Население", 
                              style={'color': 'Violet', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('', style=style_td),
                            html.Td('Прикреплено', style=style_td),
                            html.Td('Под Д-набл.', style=style_td)]),
                        html.Tr([
                            html.Td('Всего:', style={'padding': '0 10px 0 0'}),
                            html.Td('156 647'),
                            html.Td('57 133')]),
                        html.Tr([
                            html.Td('Взрослые:', style={'padding': '0 10px 0 0'}),
                            html.Td('124 468'),
                            html.Td('54 943')]),
                        html.Tr([
                            html.Td('Дети'),
                            html.Td('31 979'),
                            html.Td('8 246')]),
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Прикрепление через ЕПГУ", 
                              style={'color': 'Violet', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('', style=style_td),
                            html.Td('к-во заявлений', style=style_td),
                        ]),
                        html.Tr([
                            html.Td('Поступило'),
                            html.Td(679)]),
                        html.Tr([
                            html.Td('Не обработано', style={'padding': '0 20px 0 0'}),
                            html.Td(4)]),
                        html.Tr([
                            html.Td('Прикреплено', style={'padding': '0 20px 0 0'}),
                            html.Td(576)]),
                        html.Tr([
                            html.Td('Отказано'),
                            html.Td(99)]),
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Дневной стационар", 
                              style={'color': 'Violet', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('Корпус', style=style_td),
                            html.Td('Койки', style=style_td),
                            html.Td('Занято', style=style_td),
                            html.Td('Выписано', style=style_td),
                            html.Td('Поступило', style=style_td),
                        ]),
                        html.Tr([
                            html.Td('ГП 3'),
                            html.Td('45'),
                            html.Td('43'),
                            html.Td('2'),
                            html.Td('3'),
                        ]),
                        html.Tr([
                            html.Td('ГП 11'),
                            html.Td('35'),
                            html.Td('32'),
                            html.Td('4'),
                            html.Td('5')]),
                        html.Tr([
                            html.Td('ЖК'),
                            html.Td('28'),
                            html.Td('26'),
                            html.Td('5'),
                            html.Td('1')]),
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Талоны ОМС (текущий месяц)", 
                              style={'color': 'Violet', 'text-align': 'center', 'font-weight': 'bold', 'fontSize': '1.4rem'}),
                dbc.CardBody([
                    html.Table([
                        html.Tr([
                            html.Td('', style=style_td),
                            html.Td('к-во талонов', style=style_td),
                            html.Td('сумма', style=style_td),
                        ]),
                        html.Tr([
                            html.Td('Выставлено', style={'padding': '0 20px 0 0'}),
                            html.Td('44 225'),
                            html.Td('44 797 714.81'),
                        ]),
                        html.Tr([
                            html.Td('Оплачено'),
                            html.Td('2 036'),
                            html.Td('1 812 371,03')]),
                    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'white', 'margin': '0 auto', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#1f2c56', 'border': '1px solid #34495e', 'borderRadius': '15px'})
        ], width=3, className="mb-3"),
    ], className="mb-4"),
], fluid=True)




app.layout = html.Div([
    header_func(datetime.now().strftime('%d.%m.%Y %H:%M'), get_default_organization_name()),
    card_container
])

@callback(
    Output('last-update', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_last_update(n):
    current_time = datetime.now()
    # Показываем время последнего обновления (круглый час)
    # Если сейчас 15:45, то показываем 15:00
    last_hour = current_time.replace(minute=0, second=0, microsecond=0)
    return last_hour.strftime('%d.%m.%Y %H:%M')

@callback(
    Output('current-date-output', 'children'),
    Input('current-time-interval', 'n_intervals')
)
def update_current_time(n):
    current_time = datetime.now()
    # Формат как на первом скрине: "чт 14 августа 2025 19:06:56"
    weekday_short = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'][current_time.weekday()]
    month_names = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 
                   'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    month_name = month_names[current_time.month - 1]
    return f"{weekday_short} {current_time.day} {month_name} {current_time.year} {current_time.strftime('%H:%M:%S')}"

if __name__ == '__main__':
    # Получаем настройки из переменных окружения
    port = int(os.getenv('PORT', 5020))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    
    app.run(debug=debug, host=host, port=port)
