from dash import html, Output, Input, State
import dash_bootstrap_components as dbc
from datetime import datetime

from apps.analytical_app.app import app

year = datetime.now().year

# Обновленные стили футера
footer_style = {
    'position': 'fixed',  # Оставляем fixed для постоянного отображения внизу
    'bottom': 0,
    'left': 0,
    'right': 0,
    'height': '40px',
    'width': '100%',
    'background-color': '#0d6efd',
    'color': 'white',
    'display': 'flex',
    'align-items': 'center',
    'z-index': 1030,  # Высокий z-index чтобы футер был поверх другого контента
}

# Стили для отступов основного контента
main_content_padding = {
    'padding-bottom': '50px',  # Отступ для основного контента, чтобы футер не перекрывал
}


def create_footer():
    footer = html.Footer([
        # Используем Grid для более точного контроля над расположением элементов
        dbc.Container(
            dbc.Row([
                # Левая часть – информация о пользователе
                dbc.Col(
                    html.Div(
                        "Пользователь", 
                        style={'font-weight': 'bold', 'white-space': 'nowrap'}
                    ),
                    width={"size": 3},
                    className="d-flex justify-content-start"
                ),
                
                # Центральная часть – ссылка на сайт (точно по центру)
                dbc.Col(
                    html.Div(
                        html.A(
                            f"©МозаикаМед. 2023—{year}",
                            href="https://mosaicmed.ru",
                            style={'color': 'white', 'text-decoration': 'none', 'white-space': 'nowrap'}
                        ),
                        className="d-flex justify-content-center"
                    ),
                    width={"size": 6},
                    className="text-center"
                ),
                
                # Правая часть – ссылка на поддержку
                dbc.Col(
                    html.Div(
                        "Поддержка",
                        id="support-link",
                        style={
                            'font-weight': 'bold',
                            'cursor': 'pointer',
                            'white-space': 'nowrap',
                            'text-align': 'right'
                        }
                    ),
                    width={"size": 3},
                    className="d-flex justify-content-end"
                ),
            ], className="h-100 align-items-center"),
            fluid=True,
            className="px-4 h-100"
        ),
        
        # Модальное окно для поддержки (улучшенный дизайн)
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Техническая поддержка"), close_button=True),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Свяжитесь с нами:", className="mb-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    html.P([
                                        html.I(className="bi bi-envelope me-2"),
                                        "Email: ",
                                        html.A("dmitriirod@yandex.ru", 
                                              href="mailto:dmitriirod@yandex.ru")
                                    ]),
                                    html.P([
                                        html.I(className="bi bi-telegram me-2"),
                                        "Telegram: ",
                                        html.A("@dmitr_rod", 
                                              href="https://t.me/dmitr_rod", 
                                              target="_blank")
                                    ]),
                                    html.P([
                                        html.I(className="bi bi-telephone me-2"),
                                        "Телефон: +7 (951) 868-14-28"
                                    ])
                                ])
                            ], className="mb-3"),
                            html.Div([
                                dbc.Button([
                                    html.I(className="bi bi-telegram me-2"),
                                    "Написать в Telegram"
                                ], 
                                color="primary", 
                                href="https://t.me/dmitr_rod", 
                                target="_blank",
                                className="me-2")
                            ])
                        ], md=7),
                        dbc.Col(
                            html.Img(
                                src="/assets/img/contacts.jpg",
                                style={'max-width': '100%', 'border-radius': '5px'}
                            ),
                            md=5,
                            className="d-flex align-items-center"
                        )
                    ])
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Закрыть", 
                        id="close-support-modal",
                        className="ms-auto"
                    )
                ),
            ],
            id="support-modal",
            is_open=False,
            centered=True,
            size="lg"
        )
    ], style=footer_style)
    
    return footer


# Стилевые правила для вставки в основной контейнер приложения
def get_content_style():
    """Возвращает стили для основного контейнера, чтобы избежать перекрытия футером"""
    return main_content_padding


@app.callback(
    Output("support-modal", "is_open"),
    [Input("support-link", "n_clicks"), Input("close-support-modal", "n_clicks")],
    [State("support-modal", "is_open")]
)
def toggle_support_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open
