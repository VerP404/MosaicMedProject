import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import dash_bootstrap_components as dbc
from apps.chief_app.app import app
from apps.chief_app.query_executor import execute_query


# Загрузка данных из базы
def load_plan_data():
    query = """
        SELECT id, name, goal, year, plan, finance
        FROM plan_chiefdashboard
        ORDER BY goal, year
    """
    return pd.DataFrame(execute_query(query), columns=["id", "name", "goal", "year", "plan", "finance"])


# Сохранение изменений в базу
def update_plan_data(row):
    query = f"""
        UPDATE plan_chiefdashboard
        SET name = '{row['name']}', goal = '{row['goal']}', year = {row['year']}, 
            plan = {row['plan']}, finance = {row['finance']}
        WHERE id = {row['id']}
    """
    execute_query(query)


# Добавление новой записи в базу
def insert_new_plan(row):
    query = f"""
        INSERT INTO plan_chiefdashboard (name, goal, year, plan, finance)
        VALUES ('{row['name']}', '{row['goal']}', {row['year']}, {row['plan']}, {row['finance']})
    """
    execute_query(query)


# Страница плана
def plan_page():
    plan_data = load_plan_data()
    return dbc.Container(
        dbc.Row(
            [
                # Таблица данных слева
                dbc.Col(
                    dash_table.DataTable(
                        id="plan-table",
                        data=plan_data.to_dict("records"),
                        columns=[
                            {"name": "ID", "id": "id", "editable": False},
                            {"name": "Название", "id": "name", "editable": False},
                            {"name": "Цель", "id": "goal", "editable": False},
                            {"name": "Год", "id": "year", "editable": False},
                            {"name": "План", "id": "plan", "editable": False},
                            {"name": "Финансы", "id": "finance", "editable": False},
                        ],
                        row_selectable="single",
                        style_table={"overflowX": "auto", "height": "400px", "overflowY": "scroll"},
                        style_cell={"textAlign": "left"},
                    ),
                    width=6,
                ),
                # Форма для редактирования справа
                # Форма для редактирования справа
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Редактирование плана"),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("Название", html_for="form-name"), width=3),
                                            dbc.Col(dbc.Input(id="form-name", type="text"), width=9),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("Цель", html_for="form-goal"), width=3),
                                            dbc.Col(dbc.Input(id="form-goal", type="text"), width=9),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("Год", html_for="form-year"), width=3),
                                            dbc.Col(dbc.Input(id="form-year", type="number"), width=9),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("План", html_for="form-plan"), width=3),
                                            dbc.Col(dbc.Input(id="form-plan", type="number"), width=9),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("Финансы", html_for="form-finance"), width=3),
                                            dbc.Col(dbc.Input(id="form-finance", type="number"), width=9),
                                        ],
                                        className="mb-3",
                                    ),
                                ]
                            ),
                            dbc.CardFooter(
                                [
                                    dbc.Button("Добавить новые", id="add-new-btn", color="primary", className="me-2"),
                                    dbc.Button("Сохранить изменения", id="save-btn", color="success", className="me-2"),
                                    dbc.Button("Отменить", id="cancel-btn", color="danger"),
                                ],
                                style={"textAlign": "right"},
                            ),
                        ]
                    ),
                    width=6,
                )

            ],
            style={"marginTop": "20px"},
        ),
        fluid=True,
    )


# Callback для заполнения формы при выборе строки
@app.callback(
    [
        Output("form-name", "value"),
        Output("form-goal", "value"),
        Output("form-year", "value"),
        Output("form-plan", "value"),
        Output("form-finance", "value"),
    ],
    Input("plan-table", "selected_rows"),
    State("plan-table", "data"),
)
def fill_form(selected_rows, data):
    if selected_rows:
        selected_row = data[selected_rows[0]]
        return (
            selected_row["name"],
            selected_row["goal"],
            selected_row["year"],
            selected_row["plan"],
            selected_row["finance"],
        )
    return "", "", None, None, None


# Callback для обработки кнопок
@app.callback(
    Output("save-message", "children"),
    [
        Input("add-new-btn", "n_clicks"),
        Input("save-btn", "n_clicks"),
        Input("cancel-btn", "n_clicks"),
    ],
    [
        State("form-name", "value"),
        State("form-goal", "value"),
        State("form-year", "value"),
        State("form-plan", "value"),
        State("form-finance", "value"),
        State("plan-table", "selected_rows"),
        State("plan-table", "data"),
    ],
    prevent_initial_call=True,
)
def handle_buttons(add_clicks, save_clicks, cancel_clicks, name, goal, year, plan, finance, selected_rows, data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "add-new-btn":
        if name and goal and year and plan and finance:
            insert_new_plan({"name": name, "goal": goal, "year": year, "plan": plan, "finance": finance})
            return "Новая запись добавлена!"
        return "Заполните все поля для добавления новой записи!"

    elif button_id == "save-btn" and selected_rows:
        row_id = data[selected_rows[0]]["id"]
        update_plan_data({"id": row_id, "name": name, "goal": goal, "year": year, "plan": plan, "finance": finance})
        return "Изменения сохранены!"

    elif button_id == "cancel-btn":
        return "Изменения отменены!"

    return "Выберите строку или заполните форму!"

