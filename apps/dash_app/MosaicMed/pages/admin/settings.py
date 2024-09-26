# settings.py

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from services.MosaicMed.app import app
from services.MosaicMed.flaskapp.models import Setting, SessionLocal, Department
import pandas as pd

def get_setting(name: str) -> str:
    session = SessionLocal()
    setting = session.query(Setting).filter(Setting.name == name).first()
    session.close()
    return setting.value if setting else ""

def set_setting(name: str, value: str) -> None:
    session = SessionLocal()
    setting = session.query(Setting).filter(Setting.name == name).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(name=name, value=value)
        session.add(setting)
    session.commit()
    session.close()

def get_departments():
    session = SessionLocal()
    departments = session.query(Department).all()
    session.close()
    return departments

def add_department(department_data):
    session = SessionLocal()
    department = Department(**department_data)
    session.add(department)
    session.commit()
    session.close()

def update_department(department_id, department_data):
    session = SessionLocal()
    department = session.query(Department).filter(Department.id == department_id).first()
    if department:
        for key, value in department_data.items():
            setattr(department, key, value)
        session.commit()
    session.close()

def delete_department(department_id):
    session = SessionLocal()
    department = session.query(Department).filter(Department.id == department_id).first()
    if department:
        session.delete(department)
        session.commit()
    session.close()

def display_departments():
    departments = get_departments()
    return [
        {
            'id': department.id,
            'kvazar': department.kvazar,
            'weboms': department.weboms,
            'miskauz': department.miskauz,
            'infopanel': department.infopanel
        } for department in departments
    ]

settings_layout = html.Div([html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Alert(id="settings-output-state", is_open=False, duration=4000, color="danger"),
                    html.H2("Настройки", className="card-title mb-4"),
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Сайт МО:", html_for="site_mo"),
                                dbc.Input(type="text", id="site_mo", placeholder="Введите URL",
                                          value=get_setting("site_mo"), required=True)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Название МО:", html_for="name_mo"),
                                dbc.Input(type="text", id="name_mo", placeholder="Введите название",
                                          value=get_setting("name_mo"), required=True)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Краткое название МО:", html_for="short_name_mo"),
                                dbc.Input(type="text", id="short_name_mo", placeholder="Введите краткое название",
                                          value=get_setting("short_name_mo"), required=True)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Дашборд главного врача:", html_for="dashboard_chef"),
                                dbc.Input(type="text", id="dashboard_chef", placeholder="Введите URL",
                                          value=get_setting("dashboard_chef"), required=True)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Дашборд пациента:", html_for="dashboard_patient"),
                                dbc.Input(type="text", id="dashboard_patient", placeholder="Введите URL",
                                          value=get_setting("dashboard_patient"), required=True)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Сохранить", id="save-settings-button", color="primary", className="mr-2",
                                           style={"width": "100%"})
                            ])
                        ])
                    ])
                ]),
                style={"width": "100%", "padding": "2rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                       "border-radius": "10px"}
            )
        ], width=12)
    ], style={"margin": "0 auto", "max-width": "1200px", "padding": "2rem"})
], style={"padding": "2rem"}),

html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H2("Редактирование подразделений", className="card-title mb-4"),
                    dbc.Button("Добавить подразделение", id="add-department-button", color="primary", className="mr-2",
                               style={"width": "100%"}),
                    html.Div(
                        dash_table.DataTable(
                            id='departments-table',
                            columns=[
                                {"name": "Квазар", "id": "kvazar", "editable": True},
                                {"name": "Вебомс", "id": "weboms", "editable": True},
                                {"name": "Мискауз", "id": "miskauz", "editable": True},
                                {"name": "Инфопанель", "id": "infopanel", "editable": True},
                            ],
                            data=display_departments(),
                            editable=True,
                            row_deletable=True,
                            style_table={'overflowX': 'auto'},
                        ),
                        style={"width": "100%", "overflowX": "scroll"}
                    ),
                    dbc.Button("Сохранить изменения", id="save-departments-button", color="primary", className="mr-2",
                               style={"width": "100%"})
                ]),
                style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                       "border-radius": "10px"}
            )
        ], width=12)
    ], style={"margin": "0 auto", "padding": "0rem"})
], style={"padding": "0rem"})
])

@app.callback(
    Output("settings-output-state", "children"),
    Output("settings-output-state", "is_open"),
    Output('departments-table', 'data'),
    Input("save-settings-button", "n_clicks"),
    Input("add-department-button", "n_clicks"),
    Input("save-departments-button", "n_clicks"),
    State('departments-table', 'data'),
    State('site_mo', 'value'),
    State('name_mo', 'value'),
    State('short_name_mo', 'value'),
    State('dashboard_chef', 'value'),
    State('dashboard_patient', 'value')
)
def manage_settings_and_departments(save_settings_clicks, add_department_clicks, save_departments_clicks, rows,
                                    site_mo, name_mo, short_name_mo, dashboard_chef, dashboard_patient):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if triggered_id == 'save-settings-button':
        set_setting("site_mo", site_mo)
        set_setting("name_mo", name_mo)
        set_setting("short_name_mo", short_name_mo)
        set_setting("dashboard_chef", dashboard_chef)
        set_setting("dashboard_patient", dashboard_patient)
        return "Настройки сохранены.", True, display_departments()

    if triggered_id == 'add-department-button':
        new_department = {
            'id': None,
            'kvazar': '',
            'weboms': '',
            'miskauz': '',
            'infopanel': ''
        }
        rows.append(new_department)
        return "", False, rows

    if triggered_id == 'save-departments-button':
        session = SessionLocal()
        for row in rows:
            if row['id'] is None:
                department = Department(
                    kvazar=row['kvazar'],
                    weboms=row['weboms'],
                    miskauz=row['miskauz'],
                    infopanel=row['infopanel']
                )
                session.add(department)
            else:
                department = session.query(Department).filter(Department.id == row['id']).first()
                if department:
                    department.kvazar = row['kvazar']
                    department.weboms = row['weboms']
                    department.miskauz = row['miskauz']
                    department.infopanel = row['infopanel']
        session.commit()
        session.close()
        return "Изменения сохранены.", True, display_departments()

    return "", False, display_departments()
