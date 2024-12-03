from datetime import datetime
from dash import html, Input, Output, ctx, ALL
import dash_bootstrap_components as dbc
from apps.chief_app.app import app
from apps.chief_app.query_executor import execute_query
from apps.chief_app.settings import COLORS

# Генерация списка годов
current_year = datetime.now().year
years = list(range(2023, current_year + 1))


def get_main_app_url():
    query = "SELECT main_app_ip, main_app_port FROM home_mainsettings LIMIT 1"
    result = execute_query(query)
    if result:
        ip, port = result[0]
        return f"http://{ip}:{port}"
    return "#"


# Футер
footer = dbc.Container(
    dbc.Row(
        [
            dbc.Col(
                dbc.NavLink(
                    html.Span("Главное меню", className="ms-2", id="main-menu-label"),
                    href=get_main_app_url(),  # Функция возвращает URL
                ),
                width=2
            ),
            # Центрированный текст
            dbc.Col(
                html.Div(
                    html.Span(f"© МозаикаМед. 2023-{current_year}", style={"color": COLORS["text"]}),
                    style={"textAlign": "center"}
                ),
                width=8,
            ),
            # Год справа
            dbc.Col(
                html.Div(
                    [
                        html.Span(
                            id="selected-year",
                            children=str(current_year),
                            style={"color": COLORS["text"], "cursor": "pointer"}
                        ),
                        html.Span(
                            "План",
                            id="plan-link",
                            style={"color": COLORS["text"], "marginLeft": "10px", "cursor": "pointer",
                                   "textDecoration": "underline"},
                        ),
                        html.Div(
                            id="year-options",
                            children=[
                                html.Div(
                                    str(year),
                                    id={"type": "dropdown-year", "year": year},
                                    style={"color": COLORS["text"], "padding": "5px", "cursor": "pointer"},
                                ) for year in years
        ],
        style={
            "display": "none",  # Скрываем меню по умолчанию
            "position": "absolute",
            "bottom": "25px",  # Открытие вверх
            "backgroundColor": COLORS["header_footer"],
            "border": "1px solid white",
            "zIndex": "10",
            "padding": "5px",
        }
    ),
],
style = {"textAlign": "right", "position": "relative"}
),
width = 2,
),
],
style = {"backgroundColor": COLORS["header_footer"], "color": COLORS["text"]},
className = "fixed-bottom",
align = "center",
),
fluid = True,
)

# Callback для обработки выбора года
@app.callback(
    [
        Output("selected-year", "children"),
        Output("year-options", "style"),
        Output("selected-year-store", "data"),  # Сохраняем год в dcc.Store
    ],
    [Input({"type": "dropdown-year", "year": ALL}, "n_clicks"), Input("selected-year", "n_clicks")],
    prevent_initial_call=True,
)
def update_selected_year(*args):
    ctx_triggered = ctx.triggered_id

    if isinstance(ctx_triggered, dict) and ctx_triggered["type"] == "dropdown-year":
        year = str(ctx_triggered["year"])
        return year, {"display": "none"}, year  # Обновляем выбранный год

    if ctx_triggered == "selected-year":
        return str(current_year), {
            "display": "block",
            "position": "absolute",
            "bottom": "25px",
            "backgroundColor": COLORS["header_footer"],
            "border": "1px solid white",
            "zIndex": "10",
            "padding": "5px",
        }, str(current_year)

    return str(current_year), {"display": "none"}, str(current_year)


@app.callback(
    Output("url", "pathname"),
    Input("plan-link", "n_clicks"),
    prevent_initial_call=True
)
def open_plan_page(n_clicks):
    return "/plan"  # URL для страницы "План"