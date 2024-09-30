# users.py
from dash import html, dcc, dash_table, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from services.MosaicMed.app import app
from services.MosaicMed.flaskapp.models import User, UserModel, SessionLocal, bcrypt

def fetch_all_users():
    session = SessionLocal()
    users = session.query(UserModel).all()
    session.close()
    return [
        {
            "username": user.username,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "birth_date": str(user.birth_date),
            "position": user.position,
            "role": user.role,
        }
        for user in users
    ]

users_layout = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Alert(id="output-state", is_open=False, duration=4000, color="danger"),
                    html.H2("Редактирование пользователя", className="card-title mb-4"),
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Фамилия:", html_for="last_name"),
                                dbc.Input(type="text", id="last_name", placeholder="Введите фамилию", required=True)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Имя:", html_for="first_name"),
                                dbc.Input(type="text", id="first_name", placeholder="Введите имя", required=True)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Отчество:", html_for="middle_name"),
                                dbc.Input(type="text", id="middle_name", placeholder="Введите отчество")
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Дата рождения:", html_for="birth_date"),
                                dbc.Input(type="date", id="birth_date", required=True)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Должность:", html_for="position"),
                                dbc.Input(type="text", id="position", placeholder="Введите должность", required=True)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Роль:", html_for="role"),
                                dbc.Select(
                                    id="role",
                                    options=[
                                        {"label": "Оператор", "value": "operator"},
                                        {"label": "Врач", "value": "doctor"},
                                        {"label": "Экономист", "value": "economist"},
                                        {"label": "Статистик", "value": "statistician"},
                                        {"label": "Руководитель", "value": "manager"},
                                        {"label": "Заведующий", "value": "head"},
                                        {"label": "Администратор", "value": "admin"},
                                    ],
                                    required=True
                                )
                            ], width=6)
                        ], className="mb-3"),
                        html.H3("Учетные данные", className="card-title mb-4"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Логин:", html_for="username"),
                                dbc.Input(type="text", id="username", placeholder="Введите логин", required=True)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Пароль:", html_for="password"),
                                dbc.Input(type="password", id="password", placeholder="Введите пароль")
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Сохранить", id="submit-button", color="primary",
                                           className="mr-2", style={"width": "100%"})
                            ]),
                            dbc.Col([
                                dbc.Button("Удалить", id="delete-button", color="danger",
                                           className="mr-2", style={"width": "100%"})
                            ]),
                            dbc.Col([
                                dbc.Button("Очистить", id="clear-button", color="secondary", className="mr-2",
                                           style={"width": "100%"})
                            ])
                        ])
                    ])
                ]),
                style={"width": "100%", "padding": "2rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                       "border-radius": "10px"}
            )
        ], width=4),
        dbc.Col([
            html.H2("Список пользователей", className="mb-4"),
            dash_table.DataTable(
                id='user-table',
                columns=[
                    {"name": "Логин", "id": "username"},
                    {"name": "Фамилия", "id": "last_name"},
                    {"name": "Имя", "id": "first_name"},
                    {"name": "Отчество", "id": "middle_name"},
                    {"name": "Дата рождения", "id": "birth_date"},
                    {"name": "Должность", "id": "position"},
                    {"name": "Роль", "id": "role"}
                ],
                data=fetch_all_users(),  # Загрузка пользователей при загрузке страницы
                row_selectable='single',
                selected_rows=[],
                filter_action="native",  # Фильтрация
                page_size=15,  # Пагинация на 15 строк
                export_format="xlsx",  # Экспорт в Excel
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
            )
        ], width=8)
    ])
])

@app.callback(
    [Output("output-state", "children"),
     Output("output-state", "is_open"),
     Output('user-table', 'data'),
     Output('last_name', 'value'),
     Output('first_name', 'value'),
     Output('middle_name', 'value'),
     Output('birth_date', 'value'),
     Output('position', 'value'),
     Output('role', 'value'),
     Output('username', 'value'),
     Output('password', 'value')],
    [Input("submit-button", "n_clicks"),
     Input("delete-button", "n_clicks"),
     Input("clear-button", "n_clicks"),
     Input('user-table', 'selected_rows')],
    [State("username", "value"),
     State("password", "value"),
     State("last_name", "value"),
     State("first_name", "value"),
     State("middle_name", "value"),
     State("birth_date", "value"),
     State("position", "value"),
     State("role", "value"),
     State('user-table', 'data')]
)
def manage_user(submit_clicks, delete_clicks, clear_clicks, selected_rows, username, password, last_name, first_name, middle_name,
                birth_date, position, role, data):
    ctx = callback_context

    if not ctx.triggered:
        data = fetch_all_users()
        return "", False, data, "", "", "", "", "", "", "", ""

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'submit-button':
        if not (username and last_name and first_name and birth_date and position and role):
            return "Все поля обязательны для заполнения.", True, data, last_name, first_name, middle_name, birth_date, position, role, username, password

        existing_user = User.get_by_username(username)
        if existing_user:
            # Обновление существующего пользователя
            session = SessionLocal()
            user = session.query(UserModel).filter(UserModel.username == username).first()
            user.last_name = last_name
            user.first_name = first_name
            user.middle_name = middle_name
            user.birth_date = birth_date
            user.position = position
            user.role = role
            if password:  # Если пароль введен, обновить его
                user.hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            session.commit()
            session.close()
            data = fetch_all_users()
            return f"Пользователь {username} обновлен.", True, data, "", "", "", "", "", "", "", ""
        else:
            try:
                User.create(username=username, password=password, last_name=last_name, first_name=first_name,
                            middle_name=middle_name, birth_date=birth_date, position=position, role=role,
                            category="general")
                new_user = {"username": username, "last_name": last_name, "first_name": first_name,
                            "middle_name": middle_name, "birth_date": birth_date, "position": position, "role": role}
                data.append(new_user)
                return f"Пользователь {username} добавлен.", True, data, "", "", "", "", "", "", "", ""
            except Exception as e:
                return f"Ошибка при добавлении пользователя: {str(e)}", True, data, last_name, first_name, middle_name, birth_date, position, role, username, password

    if button_id == 'delete-button':
        if selected_rows:
            selected_user = data[selected_rows[0]]
            username = selected_user['username']
            session = SessionLocal()
            user = session.query(UserModel).filter(UserModel.username == username).first()
            if user:
                session.delete(user)
                session.commit()
                data = fetch_all_users()
                session.close()
                return f"Пользователь {username} удален.", True, data, "", "", "", "", "", "", "", ""
            else:
                session.close()
                return "Ошибка удаления пользователя. Пользователь не найден.", True, data, last_name, first_name, middle_name, birth_date, position, role, username, password

    if button_id == 'clear-button':
        return "", False, data, "", "", "", "", "", "", "", ""

    if button_id == 'user-table' and selected_rows:
        selected_user = data[selected_rows[0]]
        return "", False, data, selected_user['last_name'], selected_user['first_name'], selected_user['middle_name'], \
        selected_user['birth_date'], selected_user['position'], selected_user['role'], selected_user['username'], ""

    return "", False, data, "", "", "", "", "", "", "", ""
