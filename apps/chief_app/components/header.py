from dash import html
import dash_bootstrap_components as dbc

from apps.chief_app.query_executor import execute_query
from apps.chief_app.settings import COLORS


def get_organization_name():
    query = "SELECT name FROM organization_medicalorganization LIMIT 1"
    result = execute_query(query)
    if result:
        return result[0][0]
    return "Организация не указана"


header = dbc.Container(
    dbc.Row(
        [
            # Логотип слева
            dbc.Col([
                html.Img(src="/assets/img/plotly-logomark.png", height="30px"),
                html.Div("МозаикаМед", style={"color": COLORS["text"]}),
            ],
                width=2,
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-start",
                }
            ),
            # Заголовок по центру
            dbc.Col(
                html.Div(f"{get_organization_name()} - Панель главного врача",
                         style={"color": COLORS["text"], "fontWeight": "bold"}),
                width=8,
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }
            ),
            # Время справа
            dbc.Col(
                html.Div(id="current-date-output", style={"color": COLORS["text"]}),
                width=2,
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-end"
                }
            ),
        ],
        align="center",  # Выравнивание по вертикали
        className="g-0",  # Убираем горизонтальные отступы
    ),
    style={
        "backgroundColor": COLORS["header_footer"],
        "padding": "10px",
    },
    className="fixed-top shadow-sm",
    fluid=True
)
