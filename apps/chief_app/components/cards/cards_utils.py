# # MosaicDashboard/components/cards/cards_utils.py
import dash_bootstrap_components as dbc


# Создание карт в дашборде
def create_card(title, card, card_id):
    return dbc.Card(
        id=card_id,
        children=[
            dbc.CardHeader(title, className="card-header"),
            dbc.CardBody(
                [
                    card
                ],
                className="card-content",
            ),
        ],
        className="mb-4"
    )
