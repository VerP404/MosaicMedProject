from dash import html, dcc
from datetime import datetime
import dash_bootstrap_components as dbc


def header_func(_date_update):
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Img(src='/assets/logo-vgp3.png', style={'height': '100px', 'width': 'auto'}),
            ], width=3, className="d-flex align-items-center justify-content-center"),
            dbc.Col([
                html.H2("БУЗ ВО ВГКП №3", 
                        style={'textAlign': 'center', 'color': 'white', 'marginTop': '5px', 'marginBottom': '5px', 'fontSize': '32px', 'fontWeight': 'bold'}),
                html.H4("Система мониторинга показателей для главного врача", 
                        style={'textAlign': 'center', 'color': 'white', 'marginTop': '5px', 'marginBottom': '5px', 'fontSize': '20px'}),
            ], width=6, className="d-flex flex-column justify-content-center"),
            dbc.Col([
                html.H5([
                    html.Span("Обновлено: ", style={'color': 'white'}),
                    html.Span(_date_update, id="last-update", style={'color': 'white'})
                ], style={'textAlign': 'right', 'marginTop': '5px', 'marginBottom': '5px', 'fontSize': '18px'}),
                html.H5(id="current-date-output", 
                        style={'textAlign': 'right', 'color': 'white', 'marginTop': '5px', 'marginBottom': '5px', 'fontSize': '18px'}),
                dcc.Interval(
                    id='interval-component',
                    interval=3600000,  # каждый час в миллисекундах
                    n_intervals=0
                ),
                dcc.Interval(
                    id='current-time-interval',
                    interval=60000,  # каждую минуту в миллисекундах
                    n_intervals=0
                )
            ], width=3, className="d-flex flex-column justify-content-end")
        ], className="align-items-center", style={'minHeight': '120px'})
    ], fluid=True, style={'backgroundColor': '#4c4bc0', 'padding': '5px 0'})