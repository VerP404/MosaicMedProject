from datetime import datetime
from dash import html

from apps.chief_app import main_color, name_mo

# Определяем стиль футера
footer_style = {
    'position': 'fixed',
    'bottom': 0,
    'margin': 0,
    'height': '30px',
    'width': '100%',
    'background-color': main_color,
    'color': 'white',
    'text-align': 'center',
    'display': 'flex',
    'justify-content': 'space-between',
}

# Определяем футер
footer = html.Footer(children=[
    html.P(html.A("МозаикаМед", style={'text-decoration': 'none', 'color': 'white'}),
           style={'margin-left': '8%'}),
    html.P(id='open-modal', children=f"© МозаикаМед - Родионов ДН 2023—{datetime.now().year}"),
    html.P(html.A(name_mo, style={'text-decoration': 'none', 'color': 'white'}),
           style={'margin-right': '8%'}),
], style=footer_style)



