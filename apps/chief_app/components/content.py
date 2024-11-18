# MosaicDashboard/components/content.py
from dash import html
import dash_bootstrap_components as dbc

from apps.chief_app import main_color
from apps.chief_app.components.cards.graphs.graphs import bar_chart1, stacked_bar_chart1, pie_chart1, bar_chart2
from apps.chief_app.components.cards.cards_utils import create_card
from apps.chief_app.components.cards.tables.tables import card_table_1, card_table_2, card_table_3, card_table_4

# Определяем стиль контента
CONTENT_STYLE = {
    "padding": "2rem",
    "backgroundColor": main_color,
    "flex": "1"
}

# Создаем контент для карточек и графиков
cards_and_graphs = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(create_card("Доступность первичной записи к ВОП, терапевтам и педиатрам по корпусам на 14 дней",
                                    card_table_1, "card1"), width=3),
                dbc.Col(create_card("Доступность первичной записи по специальностям",
                                    card_table_2, "card2"), width=3),
                dbc.Col(create_card("Динамика выданных свидетельств о смерти по корпусам",
                                    card_table_3, "card3"), width=2),
                dbc.Col(create_card("Диспансеризация репродуктивного здоровья",
                                    card_table_4, "card4"), width=4),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(create_card("ДОГВН, ПМО, УД по корпусам", bar_chart1, "graph-card1"), width=2),
                dbc.Col(create_card("РЭМД/СЭМД по корпусам", stacked_bar_chart1, "card6"), width=2),
                dbc.Col(create_card("Смертность по корпусам", pie_chart1, "card7"), width=2),
                dbc.Col(create_card("Заболеваемость БСК и ХОБЛ", bar_chart2, "card8"), width=3),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(create_card("Население", html.Div(), "card9"), width=2),
                dbc.Col(create_card("Прикрепление через ЕПГУ", html.Div(), "card10"), width=3),
                dbc.Col(create_card("Дневной стационар", html.Div(), "card11"), width=3),
                dbc.Col(create_card("Талоны ОМС", html.Div(), "card12"), width=3),
            ],
        )
    ]
)

# Определяем layout контента
content = html.Div(id="page-content", children=cards_and_graphs, style=CONTENT_STYLE)
