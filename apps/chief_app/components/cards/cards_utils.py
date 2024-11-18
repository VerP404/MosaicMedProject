import dash_bootstrap_components as dbc
from dash import html
from apps.chief_app.settings import COLORS


def create_card(title, content, card_id):
    """
    Универсальная функция создания карточки.
    Контент карточки передаётся через аргумент `content` и может быть любым компонентом Dash.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    [
                        html.Span(title, style={"color": COLORS["text"]}),
                        html.Button(
                            html.I(className="bi bi-arrow-clockwise"),
                            id=f"update-btn-{card_id}",
                            className="btn btn-link btn-sm",
                            style={"float": "right", "color": COLORS["accent_blue"], "padding": "0px"},
                        ),
                    ],
                    style={"display": "flex", "justifyContent": "space-between"},
                ),
                style={"backgroundColor": COLORS["card_background"]},
            ),
            dbc.CardBody(
                html.Div(
                    content,  # Контент карточки
                    style={"overflowY": "auto", "height": "200px", "color": COLORS["text"]},
                )
            ),
        ],
        style={
            "backgroundColor": COLORS["card_background"],
            "borderRadius": "10px",
            "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
        },
        className="mb-4 shadow-sm",
    )
