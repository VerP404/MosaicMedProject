from datetime import datetime
from dash import html
import dash_bootstrap_components as dbc
from apps.chief_app.settings import COLORS

footer = dbc.Container(
    dbc.Row(
        dbc.Col(
            html.Div(
                [
                    html.Span(f"© МозаикаМед. 2023-{datetime.now().year}", style={"color": COLORS["text"]}),
                ],
                style={"textAlign": "center", "width": "100%"}
            )
        ),
        style={"backgroundColor": COLORS["header_footer"], "color": COLORS["text"], "textAlign": "center"},
        className="fixed-bottom"
    ),
    fluid=True,
)
