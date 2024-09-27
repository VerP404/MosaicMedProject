import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

PLOTLY_LOGO = r"\assets\img\plotly-logomark.png"

header = dbc.Navbar(
    dbc.Container(
        [
            dcc.Interval(
                id='date-interval',
                interval=3600000,
                n_intervals=0
            ),
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("МозаикаМед", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="/home/",
                style={"textDecoration": "none"},
            ),
            dbc.NavLink(),
            dbc.NavLink(),
            dbc.NavLink(),
            dbc.NavLink(),
            dbc.NavLink(),
            dbc.NavLink(),
            dbc.NavLink(),
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Справка", header=True),
                    dbc.DropdownMenuItem("Статусы талонов", href="/statuses"),
                    dbc.DropdownMenuItem("Диагнозы по 168н", href="/diagnoses-168"),
                    dbc.DropdownMenuItem("Инструкция", href="/readme"),
                    dbc.DropdownMenuItem("2023 год", href="http://10.136.29.166:2023/"),
                ],
                nav=True,
                in_navbar=True,
                label=html.Span("Справка", className="text-white"),
            ),
            dbc.NavLink(html.Div(id='current-date-output', style={"color": "white"})),
            dbc.NavLink(html.Div(id='file-info', style={"color": "white"})),
        ], className="ms-auto"
    ),
    color="primary",
    dark=True,
    fixed="top",

)

