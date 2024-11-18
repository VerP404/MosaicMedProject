from dash import html, dcc
import dash_bootstrap_components as dbc

from apps.chief_app import main_color

# Определяем заголовок с логотипом и временем
header = dbc.Row(
    [
        dbc.Col(html.Img(src='assets/img/logo.png', height='100px', style={"margin-top": "10px", "margin-left": "10px"})),
        dbc.Col(
            html.Div([
                html.H2("БУЗ ВО ВГП №3", className="text-center text-white", style={"margin-bottom": "0"}),
                html.H4("Дашборд главного врача", className="text-center text-white", style={"margin-top": "0"})
            ]),
            width=8
        ),
        dbc.Col(html.Div(id='live-time', className="text-center text-white"), width=2)
    ],
    align="center",
    style={"backgroundColor": main_color, "margin": "0", "padding": "0"}
)

# Добавляем компонент для обновления времени
header.children.append(
    dcc.Interval(
        id='interval-component',
        interval=1 * 60000,  # обновление каждую минуту
        n_intervals=0
    )
)
