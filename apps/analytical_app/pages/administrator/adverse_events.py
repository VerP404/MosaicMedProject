from dash import html, dcc
import dash_bootstrap_components as dbc


# Заглушка: Нежелательные события
type_page = "adverse-events-admin"


admin_adverse_events = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Нежелательные события"),
                            html.P(
                                "Аналитика по нежелательным событиям. Страница в разработке.",
                                className="mb-0"
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                        "border-radius": "10px",
                    },
                ),
                width=12,
            ),
            style={"margin": "0 auto", "padding": "0rem"},
        ),
        dcc.Loading(id=f"loading-output-{type_page}", type="default"),
    ]
)


