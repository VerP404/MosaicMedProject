# footer.py

from dash import html, Output, Input, State, dcc, dash
from datetime import datetime
import dash_bootstrap_components as dbc

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
        html.P(
            id='footer-mo-name',
            children=html.A(
                style={'text-decoration': 'none', 'color': 'white'}
            ),
            style={'margin-right': '8%'}
        ),
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


# @app.callback(
#     Output("user-modal", "is_open"),
#     [Input("user-info", "n_clicks"), Input("close-user-modal", "n_clicks")],
#     [State("user-modal", "is_open")],
# )
# def toggle_user_modal(open_clicks, close_clicks, is_open):
#     if open_clicks or close_clicks:
#         return not is_open
#     return is_open
#
#
# @app.callback(
#     Output("developer-modal", "is_open"),
#     [Input("open-developer-modal", "n_clicks"), Input("close-developer-modal", "n_clicks")],
#     [State("developer-modal", "is_open")],
# )
# def toggle_developer_modal(open_clicks, close_clicks, is_open):
#     if open_clicks or close_clicks:
#         return not is_open
#     return is_open
#
#
# @app.callback(
#     Output('user-info', 'children'),
#     Input('url', 'pathname')
# )
# def update_user_info(pathname, **kwargs):
#     user = kwargs.get('user')
#     if user and user.is_authenticated:
#         # Assuming your user model has the attributes below
#         return f"{user.last_name} {user.first_name[0]}. {user.middle_name[0]}."
#     return "Гость"
#
#
# @app.callback(
#     [
#         Output('user-full-name', 'children'),
#         Output('user-position', 'children'),
#         Output('user-role', 'children'),
#         Output('user-category', 'children'),
#         Output('user-birth-date', 'children')
#     ],
#     Input('user-modal', 'is_open')
# )
# def update_modal_user_info(is_open, **kwargs):
#     user = kwargs.get('user')
#     if is_open and user and user.is_authenticated:
#         return (
#             f"ФИО: {user.last_name} {user.first_name} {user.middle_name}",
#             f"Должность: {user.position}",
#             f"Роль: {user.role}",
#             f"Категория: {user.category}",
#             f"Дата рождения: {user.birth_date}"
#         )
#     return ("", "", "", "", "")
#
#
# @app.callback(
#     Output('url', 'pathname'),
#     Input('logout-button', 'n_clicks')
# )
# def logout_callback(n_clicks, **kwargs):
#     if n_clicks:
#         request = kwargs.get('request')
#         if request:
#             logout(request)
#         return '/login'
#     return dash.no_update
#
#
# @app.callback(
#     Output('footer-mo-name', 'children'),
#     [Input('save-settings-button', 'n_clicks')],
#     [State('name_mo', 'value'), State('site_mo', 'value')]
# )
# def update_footer_mo_name(n_clicks, name_mo, site_mo):
#     if n_clicks:
#         return html.A(name_mo, href=site_mo, style={'text-decoration': 'none', 'color': 'white'})
#     return html.A(
#         get_setting("name_mo"),
#         href=get_setting("site_mo"),
#         style={'text-decoration': 'none', 'color': 'white'}
#     )
