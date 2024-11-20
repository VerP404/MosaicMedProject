import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(BASE_DIR)

from config.settings import DEBUG_DASH, PORT_DASH_CHIEF

from dash import html, Input, Output, dcc
from apps.chief_app.app import app
from apps.chief_app.components.content import content
from apps.chief_app.components.footer import footer
from apps.chief_app.components.header import header
from apps.chief_app.settings import COLORS

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        header,
        content,
        footer,
    ],
    style={"height": "100vh",
           "display": "flex",
           "flexDirection": "column",
           "backgroundColor": COLORS["background"]}
)


# Callback для обновления содержимого карточки
@app.callback(
    Output("content-card1", "children"),
    Input("update-btn-card1", "n_clicks"),
    prevent_initial_call=True,
)
def update_card1(n_clicks):
    return f"Данные обновлены! Количество обновлений: {n_clicks}"


@app.callback(
    Output("content-card2", "children"),
    Input("update-btn-card2", "n_clicks"),
    prevent_initial_call=True,
)
def update_card2(n_clicks):
    return f"Обновлено: новое содержимое (нажатий: {n_clicks})"


@app.callback(
    Output("content-card3", "children"),
    Input("update-btn-card3", "n_clicks"),
    prevent_initial_call=True,
)
def update_card3(n_clicks):
    return f"Данные обновлены: {n_clicks}"


if __name__ == "__main__":
    app.run_server(debug=DEBUG_DASH, host='0.0.0.0', port=PORT_DASH_CHIEF)
