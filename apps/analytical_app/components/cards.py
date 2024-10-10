from dash import html
import dash_bootstrap_components as dbc


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
            dbc.CardHeader([html.H5(f"{card_header}", className="card-title")]),
            dbc.CardBody(
                [
                    html.P(f"{card_text}", className="card-text"),
                ],
                className="d-flex flex-column h-100"
            ),
            dbc.CardFooter(
                dbc.Button(
                    "Открыть", color=color_button, className="mt-auto", id=f"open-report-{card_num}-{card_type_page}"
                ),
                className="d-flex justify-content-end"
            ),
        ],
        className="h-100"
    )
