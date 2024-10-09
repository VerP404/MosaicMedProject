# apps/analytical_app/index.py
from dash import dcc, html

from apps.analytical_app.app import app
from apps.analytical_app.routes import register_routes
from components.sidebar import create_sidebar
from components.navbar import create_navbar
from components.footer import create_footer

app.layout = html.Div(
    [
        dcc.Store(id='current-month-number', data=None),
        dcc.Store(id='current-month-name', data=None),
        dcc.Store(id='sidebar-state', data="collapsed"),  # Хранилище для состояния сайдбара
        dcc.Interval(id='date-interval-main', interval=600000, n_intervals=0),  # 10 минут
        dcc.Location(id="url"),
        create_navbar(),
        create_sidebar(),
        html.Div(id='page-content', style={'margin-left': '5rem', 'margin-top': '56px', 'padding': '2rem 1rem'}),
        create_footer(),
    ]
)

register_routes(app)
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port='5000')

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
