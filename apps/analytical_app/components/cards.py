import dash_bootstrap_components as dbc
from dash import html


def create_card(card_num, card_type_page, card_header, card_text, color_button="success"):
    """
    Шаблон карточки
    :param card_num: номер карточки на странице
    :param card_type_page: тип страницы
    :param card_header: заголовок карточки
    :param card_text: текст карточки
    :param color_button: цвет кнопки
    """
    return dbc.Card(
        [
            # Заголовок
            dbc.CardHeader(
                html.H5(card_header, className="card-title")
            ),

            # Тело — flex-grow, чтобы занять всё пространство между header и footer
            dbc.CardBody(
                html.P(card_text, className="card-text"),
                className="flex-grow-1"
            ),

            # Футер: кнопка прижата вниз благодаря mt-auto на wrapper‑div
            dbc.CardFooter(
                dbc.Button(
                    "Открыть",
                    color=color_button,
                    id=f"open-report-{card_num}-{card_type_page}"
                ),
                className="mt-auto d-flex justify-content-end"
            ),
        ],
        className="h-100 d-flex flex-column"
    )
