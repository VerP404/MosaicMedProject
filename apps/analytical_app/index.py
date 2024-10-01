# apps/analytical_app/index.py
from dash import dcc, html
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from dash.dependencies import Output, Input, State
import datetime
from components.sidebar import create_sidebar
from components.navbar import create_navbar
from components.footer import create_footer
from babel.dates import format_datetime

app.layout = html.Div(
    [
        dcc.Store(id='current-month-number', data=None),
        dcc.Store(id='current-month-name', data=None),
        dcc.Interval(id='date-interval-main', interval=600000, n_intervals=0),  # 10 минут
        dcc.Location(id="url"),
        create_navbar(),
        create_sidebar(),
        html.Div(id='page-content', style={'margin-left': '18rem', 'margin-top': '56px', 'padding': '2rem 1rem'}),
        create_footer(),
    ]
)


# Callback для обновления времени в навбаре
@app.callback(
    Output('current-time', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_time(n):
    now = datetime.datetime.now()
    formatted_time = format_datetime(now, "EEE d MMMM y H:mm:ss", locale='ru')
    return formatted_time


# Callback для сворачивания/разворачивания сайдбара
@app.callback(
    [Output("sidebar", "style"),
     Output("page-content", "style"),
     Output("main-label", "style"),
     Output("about-label", "style")],
    [Input("btn_sidebar", "n_clicks")],
    [State("sidebar", "style"), State("page-content", "style")]
)
def toggle_sidebar(n_clicks, sidebar_style, page_content_style):
    if n_clicks and n_clicks % 2 == 1:
        # Свернутый вид (только иконки)
        sidebar_style["width"] = "5rem"
        page_content_style["margin-left"] = "5rem"
        return sidebar_style, page_content_style, {"display": "none"}, {"display": "none"}
    else:
        # Развернутый вид (иконки и текст)
        sidebar_style["width"] = "18rem"
        page_content_style["margin-left"] = "18rem"
        return sidebar_style, page_content_style, {"display": "inline"}, {"display": "inline"}


# Callback для отображения страницы в зависимости от URL
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/about':
        return html.H1('О нас')
    else:
        return html.Div([
            html.H1("Добро пожаловать в МозаикаМед", style={"textAlign": "center"}),
            html.P("Это информационно-справочная система для анализа данных.", style={"textAlign": "center"}),
        ])


if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port='5000')

# MosaicMedProject/
# └──apps/
#    └── analytical_app/
#        └── components/
#            ├── footer.py
#            ├── navbar.py
#            └── sidebar.py
#        └── assets/
#            ├── css/
#            │   ├── styles.css
#            │   └── bootstrap_icons.css
#            ├── js/
#            │   └── custom.js
#            ├── images/
#            │   └── logo.png
#            └── other_assets/
#                └── ...
#        ├── app.py
#        └── index.py
