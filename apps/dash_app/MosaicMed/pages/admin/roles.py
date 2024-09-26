from dash import html, dcc, callback_context, dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
from services.MosaicMed.app import app
from services.MosaicMed.flaskapp.models import RoleModuleAccess, SessionLocal


def get_roles():
    return ['operator', 'doctor', 'economist', 'statistician', 'manager', 'head', 'admin']


def get_modules():
    return ['doctors-report',
            'dispensary',
            'econ',
            'it',
            'admin',
            'other-modules',
            'errors',
            'admin-access',
            'eln',
            'iszl',
            'dispensary-observation',
            'other-reports',
            'volumes',
            'filling-lists',
            'wo-coupons',
            'dashboards',
            ]


def fetch_access_data():
    session = SessionLocal()
    access_data = session.query(RoleModuleAccess).all()
    session.close()
    return [{'role': access.role, 'module': access.module} for access in access_data]


def generate_access_table():
    roles = get_roles()
    modules = get_modules()
    access_data = fetch_access_data()

    def is_checked(role, module):
        return any(item['role'] == role and item['module'] == module for item in access_data)

    return html.Table(
        # Заголовок таблицы
        [html.Tr([html.Th('Модуль')] + [html.Th(role) for role in roles], className="table-header")] +
        # Строки таблицы
        [
            html.Tr([
                html.Td(module, className="table-cell"),
                *[html.Td(dcc.Checklist(
                    options=[{'label': '', 'value': 'checked'}],
                    value=['checked'] if is_checked(role, module) else [],
                    id={'type': 'checkbox', 'role': role, 'module': module},
                    inputStyle={"margin-right": "10px"}
                ), className="table-cell") for role in roles]
            ], className="table-row") for module in modules
        ],
        className="access-table"
    )


def roles_layout():
    return html.Div([
        dbc.Alert(id="save-alert", color="success", is_open=False, dismissable=True, children="Изменения сохранены."),
        html.H2("Управление доступом к модулям", style={"margin-top": "20px"}),
        generate_access_table(),
        dbc.Button("Сохранить изменения", id="save-access-button", color="primary", className="mr-2",
                   style={"margin-top": "20px"}),
        dcc.Interval(id='alert-interval', interval=1 * 1000, n_intervals=0, disabled=True)  # Интервал в миллисекундах
    ], style={"margin": "50px"})


@app.callback(
    Output('save-alert', 'is_open'),
    Output('alert-interval', 'disabled'),
    Output('alert-interval', 'n_intervals'),
    [Input('save-access-button', 'n_clicks'),
     Input('alert-interval', 'n_intervals')],
    [State({'type': 'checkbox', 'role': ALL, 'module': ALL}, 'id'),
     State({'type': 'checkbox', 'role': ALL, 'module': ALL}, 'value')]
)
def manage_alert_and_save(n_clicks, n_intervals, checkbox_ids, checkbox_values):
    ctx = callback_context

    if not ctx.triggered:
        return False, True, 0

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger == 'save-access-button' and n_clicks:
        session = SessionLocal()
        session.query(RoleModuleAccess).delete()

        for checkbox_id, checkbox_value in zip(checkbox_ids, checkbox_values):
            role = checkbox_id['role']
            module = checkbox_id['module']
            if checkbox_value:
                new_access = RoleModuleAccess(role=role, module=module)
                session.add(new_access)

        session.commit()
        session.close()
        return True, False, 0

    elif trigger == 'alert-interval' and n_intervals >= 5:
        return False, True, 0

    return dash.no_update
