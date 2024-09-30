# footer.py
from dash import State, html, Output, Input, dcc, dash
from datetime import datetime
import dash_bootstrap_components as dbc
from apps.MosaicMed.app import app

year = datetime.now().year

footer_style = {
    'position': 'fixed',
    'bottom': 0,
    'margin': 0,
    'height': '30px',
    'width': '100%',
    'background-color': '#0d6efd',
    'color': 'white',
    'text-align': 'center',
    'display': 'flex',
    'justify-content': 'space-between',
}

footer_main = html.Div([
    html.Footer(children=[
        html.P(id='user-info', style={'margin-left': '8%', 'cursor': 'pointer'}),
        html.P(id='open-developer-modal', children=f"© Разработка приложения Родионов Д.Н., 2023—{year}"),
    ], style=footer_style),
])

user_modal = html.Div([
    dbc.Modal([
        dbc.ModalHeader("Информация о пользователе", close_button=False),
        dbc.ModalBody([
            html.P(id='user-full-name'),
            html.P(id='user-position'),
            html.P(id='user-role'),
            html.P(id='user-category'),
            html.P(id='user-birth-date'),
        ]),
        dbc.ModalFooter([
            dbc.Button("Выход", id="logout-button", color="danger", className="ml-auto"),
            dbc.Button("Закрыть", id="close-user-modal", className="ml-auto")
        ]),
    ], id="user-modal", is_open=False),
])

developer_modal = html.Div([
    dbc.Modal([
        dbc.ModalHeader("О разработчике", close_button=False),
        dbc.ModalBody(html.Img(src="../assets/img/contacts.jpg", style={'width': '100%'})),
        dbc.ModalFooter([
            dbc.Button("Закрыть", id="close-developer-modal", className="ml-auto")
        ]),
    ], id="developer-modal", is_open=False),
])

footer = html.Div([footer_main, user_modal, developer_modal])

@app.callback(
    Output("user-modal", "is_open"),
    [Input("user-info", "n_clicks"), Input("close-user-modal", "n_clicks")],
    [State("user-modal", "is_open")],
)
def toggle_user_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("developer-modal", "is_open"),
    [Input("open-developer-modal", "n_clicks"), Input("close-developer-modal", "n_clicks")],
    [State("developer-modal", "is_open")],
)
def toggle_developer_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open

