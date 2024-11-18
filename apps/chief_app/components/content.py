import dash_bootstrap_components as dbc

from apps.chief_app.components.cards.cards_utils import create_card
from apps.chief_app.components.cards.months_rep import report_months
from apps.chief_app.settings import COLORS

content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(create_card("Карточка 1", "Длинный текст " * 10, "card1"), width=6),
                dbc.Col(create_card("Карточка 2", "Контент карточки 2", "card2"), width=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(create_card("Карточка 3", "Контент карточки 3", "card3"), width=4),
                dbc.Col(create_card("Карточка 4", "Контент карточки 4", "card4"), width=4),
                dbc.Col(create_card("ОМС: суммы помесячно", report_months, "card5"), width=4),

            ]
        ),
    ],
    fluid=True,
    style={
        "marginTop": "80px",
        "marginBottom": "50px",
        "height": "calc(100vh - 130px)",
        "overflowY": "auto",
        "backgroundColor": COLORS["background"],  # Фон контента
    }
)
