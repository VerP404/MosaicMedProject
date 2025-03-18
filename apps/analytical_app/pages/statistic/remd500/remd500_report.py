# remd500.py

import re
import pandas as pd
from datetime import datetime, timedelta

import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine

type_page = "remd500"

layout_remd500 = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(html.H5("Фильтры (РЭМД 500)", className="mb-0"), width="auto"),
                        ],
                        align="center",
                        justify="between"
                    )
                ),
                dbc.CardBody(
                    [
                        # ------ Блок фильтров (дата начала, дата окончания, кнопка) ------
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Дата начала:", className="mb-0"),
                                        dcc.DatePickerSingle(
                                            id=f"date-picker-start-{type_page}",
                                            first_day_of_week=1,
                                            date=datetime.now().date() - timedelta(days=7),
                                            display_format="DD.MM.YYYY",
                                            className="mt-1"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Дата окончания:", className="mb-0"),
                                        dcc.DatePickerSingle(
                                            id=f"date-picker-end-{type_page}",
                                            first_day_of_week=1,
                                            date=datetime.now().date(),
                                            display_format="DD.MM.YYYY",
                                            className="mt-1"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Сформировать отчет",
                                            id=f"generate-report-button-{type_page}",
                                            color="primary",
                                            className="mt-4"
                                        )
                                    ],
                                    width=3
                                )
                            ],
                            className="mb-3"
                        ),

                        # ------ ВМЕСТО старой строки с html.Div(...) -> 4 карточки в одной строке ------
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("ЭМД", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-emd-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([
                                                html.Div([
                                                    dcc.Dropdown(
                                                        id=f"emd-date-type-dropdown-{type_page}",
                                                        options=[
                                                            {"label": "По дате исходного документа",
                                                             "value": "document_date"},
                                                            {"label": "По дате формирования ЭМД",
                                                             "value": "formation_date"},
                                                            {"label": "По дате последней отправки в РИР",
                                                             "value": "sending_date"}
                                                        ],
                                                        value="formation_date",  # Значение по умолчанию
                                                        clearable=False,
                                                        style={"marginBottom": "10px"}
                                                    ),
                                                    dcc.Dropdown(
                                                        id=f"emd-status-dropdown-{type_page}",
                                                        options=[
                                                            {"label": "Все", "value": "all"},
                                                            {"label": "Ошибка отправки", "value": "Ошибка отправки"},
                                                            {"label": "Ошибка регистрации документа",
                                                             "value": "Ошибка регистрации документа"},
                                                            {"label": "Документ успешно зарегистрирован",
                                                             "value": "Документ успешно зарегистрирован"},
                                                            {"label": "Не отправлено", "value": "-"},
                                                            {"label": "Отправлен в РИР", "value": "Отправлен в РИР"},
                                                            {"label": "Прочие", "value": "other"}
                                                        ],
                                                        value=["Документ успешно зарегистрирован"],
                                                        # По умолчанию выбираем "Все"
                                                        multi=True,  # Включаем мультивыбор
                                                        clearable=False,
                                                        style={"marginBottom": "10px"}
                                                    ),
                                                    html.Div(
                                                        id=f"emd-count-{type_page}",
                                                        style={"fontSize": "16px", "marginTop": "10px",
                                                               "fontWeight": "bold"}
                                                    )
                                                ])
                                            ])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("Рецепты", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-recipes-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([
                                                html.Div(
                                                    [
                                                        dcc.Dropdown(
                                                            id=f"recipe-verification-dropdown-{type_page}",
                                                            options=[
                                                                {"label": "Все", "value": "all"},
                                                                {"label": "2 из 2", "value": "2 из 2"},
                                                                {"label": "Не подлежит отправке в РЭМД",
                                                                 "value": "Не подлежит отправке в РЭМД"},
                                                                {"label": "0 из 2", "value": "0 из 2"},
                                                                {"label": "1 из 2", "value": "1 из 2"},
                                                                {"label": "-", "value": "-"},
                                                                {"label": "Прочие", "value": "other"}
                                                            ],
                                                            value=["2 из 2"],
                                                            multi=True,
                                                            clearable=False,
                                                            style={"marginBottom": "10px"}
                                                        ),
                                                        dcc.Dropdown(
                                                            id=f"recipe-status-dropdown-{type_page}",
                                                            options=[
                                                                {"label": "Все", "value": "all"},
                                                                {"label": "Отправлен", "value": "Отправлен"},
                                                                {"label": "Зарегистрирован",
                                                                 "value": "Зарегистрирован"},
                                                                {"label": "Ошибка регистрации",
                                                                 "value": "Ошибка регистрации"},
                                                                {"label": "Не подлежит отправке",
                                                                 "value": "Не подлежит отправке"},
                                                                {"label": "-", "value": "-"},
                                                                {"label": "Прочие", "value": "other"}
                                                            ],
                                                            value=["Зарегистрирован"],
                                                            multi=True,
                                                            clearable=False,
                                                            style={"marginBottom": "10px"}
                                                        ),
                                                        html.Div(
                                                            id=f"recipe-count-{type_page}",
                                                            style={"fontSize": "16px", "marginTop": "10px",
                                                                   "fontWeight": "bold"}
                                                        )
                                                    ]
                                                )
                                            ])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("Справки", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-reference-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5("Смертность", className="mb-0"), width="auto"),
                                                        dbc.Col(
                                                            html.Div(
                                                                id=f"last-updated-death-{type_page}",
                                                                style={"textAlign": "right", "fontWeight": "normal"}
                                                            ),
                                                            width=True
                                                        )
                                                    ],
                                                    align="center",
                                                    justify="between"
                                                )
                                            ),
                                            dbc.CardBody([])
                                        ],
                                        className="h-100"
                                    ),
                                    width=3
                                ),
                            ],
                            className="mb-3"
                        ),
                    ]
                ),
            ],
            className="mb-3"
        ),

        dbc.Tabs(
            [
                dbc.Tab(
                    dbc.Card(
                        [
                            dbc.CardHeader("Отчет по группе"),
                            dbc.CardBody(
                                dash_table.DataTable(
                                    id=f"group-report-table-{type_page}",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left'},
                                    export_format="xlsx",
                                    page_size=15
                                )
                            ),
                        ],
                        className="mb-3"
                    ),
                    label="По специальности (групповой)"
                ),
                dbc.Tab(
                    dbc.Card(
                        [
                            dbc.CardHeader("Отчет по врачу"),
                            dbc.CardBody(
                                dash_table.DataTable(
                                    id=f"doctor-report-table-{type_page}",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left'},
                                    export_format="xlsx",
                                    page_size=15
                                )
                            ),
                        ],
                        className="mb-3"
                    ),
                    label="По врачам"
                ),
            ]
        ),

        html.Div(id=f"report-status-{type_page}", className="mt-2")
    ],
    style={"padding": "15px"}
)


# ОБЪЕДИНЁННЫЙ CALLBACK: формирует отчет и получает даты обновления для каждой таблицы
@app.callback(
    [
        Output(f"group-report-table-{type_page}", "data"),
        Output(f"group-report-table-{type_page}", "columns"),
        Output(f"doctor-report-table-{type_page}", "data"),
        Output(f"doctor-report-table-{type_page}", "columns"),
        Output(f"last-updated-emd-{type_page}", "children"),
        Output(f"last-updated-recipes-{type_page}", "children"),
        Output(f"last-updated-reference-{type_page}", "children"),
        Output(f"last-updated-death-{type_page}", "children"),
        Output(f"report-status-{type_page}", "children"),
        Output(f"emd-count-{type_page}", "children"),
        Output(f"recipe-count-{type_page}", "children"),
    ],
    Input(f"generate-report-button-{type_page}", "n_clicks"),
    State(f"date-picker-start-{type_page}", "date"),
    State(f"date-picker-end-{type_page}", "date"),
    State(f"emd-date-type-dropdown-{type_page}", "value"),
    State(f"emd-status-dropdown-{type_page}", "value"),
    State(f"recipe-verification-dropdown-{type_page}", "value"),
    State(f"recipe-status-dropdown-{type_page}", "value"),
)
def generate_remd500_report(n_clicks, start_date, end_date, emd_date_type, emd_selected_statuses, recipe_verification,
                            recipe_status):
    if not n_clicks:
        return [], [], [], [], "", "", "", "", "", "итого: 0", "итого: 0"

    if not start_date or not end_date:
        return [], [], [], [], "", "", "", "", "Не выбраны даты!", "итого: 0", "итого: 0"

    try:
        start_date_str = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date_str = pd.to_datetime(end_date).strftime("%Y-%m-%d")

        accepted_statuses = [
            "Документ успешно зарегистрирован",
            "Зарегистрирован",
            "Зарегистрирована",
            "Зарегистрировано"
        ]

        emd_known_statuses = [
            "Ошибка отправки",
            "Ошибка регистрации документа",
            "Документ успешно зарегистрирован",
            "-",
            "Отправлен в РИР"
        ]
        # Получаем все возможные статусы из базы данных
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT DISTINCT sending_status
                FROM load_data_emd
            """)).fetchall()
        emd_all_statuses = [row[0] for row in result]  # Все статусы в базе
        emd_unknown_statuses = [status for status in emd_all_statuses if
                                status not in emd_known_statuses]  # Неизвестные статусы

        # ✅ Если список пуст или None — также выбираем все статусы
        if not emd_selected_statuses or len(emd_selected_statuses) == 0:
            emd_selected_statuses = emd_known_statuses + emd_unknown_statuses

        # ✅ Если выбрано "Прочие" — добавляем только неизвестные статусы
        if "other" in emd_selected_statuses:
            emd_selected_statuses.remove("other")
            emd_selected_statuses += emd_unknown_statuses

        # ✅ Если выбрано "Все" — добавляем все статусы (известные + неизвестные)
        if "all" in emd_selected_statuses:
            emd_selected_statuses.remove("all")
            emd_selected_statuses = emd_known_statuses + emd_unknown_statuses

        # Получаем данные по каждой таблице с учетом форматов даты
        # 1) ЭМД (формат "DD.MM.YYYY HH24:MI")
        query_emd = f"""
            SELECT
                doctor,
                sending_status AS status,
                'ЭМД' AS type,
                {emd_date_type} AS document_date
            FROM load_data_emd
            WHERE NULLIF({emd_date_type}, '-') IS NOT NULL
                  AND {emd_date_type} ~ '^[0-9]{{2}}\\.[0-9]{{2}}\\.[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}$'
                  AND to_date({emd_date_type}, 'DD.MM.YYYY HH24:MI')
                      BETWEEN to_date('{start_date}', 'YYYY-MM-DD')
                          AND to_date('{end_date}', 'YYYY-MM-DD')
                  AND sending_status IN ({",".join(f"'{status}'" for status in emd_selected_statuses)})
        """
        if not emd_selected_statuses:
            df_emd = pd.DataFrame()
        else:
            df_emd = pd.read_sql(query_emd, con=engine)
        # 2) Рецепты
        # Получаем все возможные статусы из базы данных
        recipe_known_verifications = [
            "2 из 2",
            "Не подлежит отправке в РЭМД",
            "0 из 2",
            "1 из 2",
            "-"
        ]
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT distinct emd_verification
                FROM load_data_recipes
            """)).fetchall()
        recipe_all_verifications = [row[0] for row in result]
        recipe_unknown_verifications = [status for status in recipe_all_verifications if
                                        status not in recipe_known_verifications]

        # ✅ Если список пуст или None — также выбираем все статусы
        if not recipe_verification or len(recipe_verification) == 0:
            recipe_verification = recipe_known_verifications + recipe_unknown_verifications
        # ✅ Если выбрано "Прочие" — добавляем только неизвестные статусы
        if "other" in recipe_verification:
            recipe_verification.remove("other")
            recipe_verification += recipe_unknown_verifications
        # ✅ Если выбрано "Все" — добавляем все статусы (известные + неизвестные)
        if "all" in recipe_verification:
            recipe_verification.remove("all")
            recipe_verification = recipe_known_verifications + recipe_unknown_verifications

        recipe_known_status = [
            "Отправлен",
            "Зарегистрирован",
            "Ошибка регистрации",
            "Не подлежит отправке",
            "-"]

        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT distinct sending_status_remd
                FROM load_data_recipes
            """)).fetchall()

        recipe_all_status = [row[0] for row in result]
        recipe_unknown_status = [status for status in recipe_all_status if
                                        status not in recipe_known_status]
        # ✅ Если список пуст или None — также выбираем все статусы
        if not recipe_status or len(recipe_status) == 0:
            recipe_status = recipe_known_status + recipe_unknown_status
        # ✅ Если выбрано "Прочие" — добавляем только неизвестные статусы
        if "other" in recipe_status:
            recipe_status.remove("other")
            recipe_status += recipe_unknown_status
        # ✅ Если выбрано "Все" — добавляем все статусы (известные + неизвестные)
        if "all" in recipe_status:
            recipe_status.remove("all")
            recipe_status = recipe_known_status + recipe_unknown_status

        query_recipes = f"""
            SELECT
                doctor_full_name AS doctor,
                sending_status_remd AS status,
                'Рецепты' AS type,
                date AS document_date
            FROM load_data_recipes
            WHERE to_date(date, 'DD.MM.YYYY')
                      BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD')
                          AND to_date('{end_date_str}', 'YYYY-MM-DD')
                      AND emd_verification IN ({",".join(f"'{v}'" for v in recipe_verification)})
                      AND sending_status_remd IN ({",".join(f"'{s}'" for s in recipe_status)})
        """
        df_recipes = pd.read_sql(query_recipes, con=engine)

        # 3) Справки (формат "DD.MM.YYYY")
        query_reference = f"""
            SELECT
                doctor,
                status,
                'Справки' AS type,
                issue_date AS document_date
            FROM load_data_reference
            WHERE to_date(issue_date, 'DD.MM.YYYY')
                  BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD')
                      AND to_date('{end_date_str}', 'YYYY-MM-DD')
        """
        df_reference = pd.read_sql(query_reference, con=engine)

        # 4) Смертность (формат "YYYY-MM-DD")
        query_death = f"""
            SELECT
                doctor,
                emd_sending_status AS status,
                'Смертность' AS type,
                issue_date AS document_date
            FROM load_data_death
            WHERE to_date(issue_date, 'YYYY-MM-DD')
                  BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD')
                      AND to_date('{end_date_str}', 'YYYY-MM-DD')
        """
        df_death = pd.read_sql(query_death, con=engine)

        # Объединяем данные
        combined_df = pd.concat([df_emd, df_recipes, df_reference, df_death], ignore_index=True)

        # Фильтруем по статусам
        filtered_df = combined_df[combined_df['status'].isin(accepted_statuses)].copy()

        # Извлечение специальности из строки врача (если указано в скобках)
        def extract_specialty(doctor_str):
            if pd.isna(doctor_str):
                return None
            match = re.search(r"\((.*?)\)", doctor_str)
            return match.group(1) if match else None

        filtered_df['specialty'] = filtered_df['doctor'].apply(extract_specialty)

        # Формируем отчет по врачам: группировка по (doctor, specialty, type)
        doctor_pivot = (
            filtered_df
            .groupby(['doctor', 'specialty', 'type'], observed=False)
            .size()
            .reset_index(name='count')
        )

        # Формируем групповой отчет: группировка по специальности
        group_pivot = (
            filtered_df
            .groupby('specialty', observed=False)
            .size()
            .reset_index(name='total')
        )

        bins = [0, 99, 499, float('inf')]
        labels = ['до 100', '100-499', '>500']
        group_pivot['Категория'] = pd.cut(group_pivot['total'], bins=bins, labels=labels)
        group_summary = group_pivot.groupby('Категория', observed=False)['total'].sum().reset_index()

        group_columns = [{"name": col, "id": col} for col in group_summary.columns]
        doctor_columns = [{"name": col, "id": col} for col in doctor_pivot.columns]

        # Получаем дату последнего обновления для каждой таблицы
        with engine.connect() as conn:
            row_emd = conn.execute(text("SELECT MAX(updated_at) FROM load_data_emd")).fetchone()
            row_recipes = conn.execute(text("SELECT MAX(updated_at) FROM load_data_recipes")).fetchone()
            row_reference = conn.execute(text("SELECT MAX(updated_at) FROM load_data_reference")).fetchone()
            row_death = conn.execute(text("SELECT MAX(updated_at) FROM load_data_death")).fetchone()

        last_updated_emd = row_emd[0].strftime('%d.%m.%Y %H:%M') if row_emd and row_emd[0] else "Нет данных"
        last_updated_recipes = row_recipes[0].strftime('%d.%m.%Y %H:%M') if row_recipes and row_recipes[
            0] else "Нет данных"
        last_updated_reference = row_reference[0].strftime('%d.%m.%Y %H:%M') if row_reference and row_reference[
            0] else "Нет данных"
        last_updated_death = row_death[0].strftime('%d.%m.%Y %H:%M') if row_death and row_death[0] else "Нет данных"

        return (
            group_summary.to_dict('records'),
            group_columns,
            doctor_pivot.to_dict('records'),
            doctor_columns,
            f"{last_updated_emd}",
            f"{last_updated_recipes}",
            f"{last_updated_reference}",
            f"{last_updated_death}",
            "",
            f"итого: {len(df_emd)}",
            f"итого: {len(df_recipes)}"
        )

    except Exception as e:
        return [], [], [], [], "", "", "", "", f"Ошибка при формировании отчета: {str(e)}", "итого: 0", "итого: 0"
