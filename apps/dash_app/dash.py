# dash_app/dash.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

from django_plotly_dash import DjangoDash

# Создаем Dash-приложение, интегрированное с Django
app = DjangoDash('DashApp')

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Montreal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization',
                'height': '1000px',  # Задаем высоту графика
                'width': '1000px',  # Задаем ширину графика
            }
        }
    )
], style={'width': '100px', 'height': '100px'})
