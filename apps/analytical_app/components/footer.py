from dash import html, Output, Input, State
import dash_bootstrap_components as dbc
from datetime import datetime

from apps.analytical_app.app import app

year = datetime.now().year

footer_style = {
    'position': 'fixed',
    'bottom': 0,
    'margin': 0,
    'height': '40px',
    'width': '100%',
    'background-color': '#0d6efd',
    'color': 'white',
    'display': 'flex',
    'justify-content': 'space-between',
    'align-items': 'center',
    'padding': '0 20px'
}


def create_footer():
    footer = html.Footer([
        # Левая часть – информация о пользователе (статическая заглушка)
        html.Div("Пользователь", style={'font-weight': 'bold'}),
        # Центральная часть – ссылка на сайт
        html.Div(
            html.A(f"©МозаикаМед. 2023—{year}", href="https://mosaicmed.ru",
                   style={'color': 'white', 'text-decoration': 'none'}),
            style={'margin-right': '8%'}
        ),
        # Правая часть – ссылка на поддержку (при клике открывается модальное окно)
        html.Div("Поддержка", id="support-link", style={'font-weight': 'bold', 'cursor': 'pointer'}),
        # Модальное окно для поддержки
        dbc.Modal(
            [
                dbc.ModalHeader("Поддержка"),
                dbc.ModalBody(
                    html.Div([
                        dbc.Row(
                            html.A("Связаться в Telegram",
                                   href="https://t.me/dmitr_rod",  # замените на нужный URL
                                   target="_blank",
                                   style={'font-size': '16px', 'font-weight': 'bold', 'color': '#0d6efd',
                                          'text-decoration': 'none'}), ),
                        dbc.Row(
                            html.Img(src="/assets/img/contacts.jpg", style={'width': '50%'})
                        ),
                    ]),
                ),
                dbc.ModalFooter(
                    dbc.Button("Закрыть", id="close-support-modal", className="ml-auto")
                ),
            ],
            id="support-modal",
            is_open=False,
            centered=True,
            size="lg"
        )
    ], style=footer_style)
    return footer


@app.callback(
    Output("support-modal", "is_open"),
    [Input("support-link", "n_clicks"), Input("close-support-modal", "n_clicks")],
    [State("support-modal", "is_open")]
)
def toggle_support_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open
