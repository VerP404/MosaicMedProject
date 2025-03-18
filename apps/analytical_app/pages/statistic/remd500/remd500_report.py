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
                        # Блок с датами последнего обновления по каждой таблице
                        dbc.Row(
                            [
                                dbc.Col(html.Div(id=f"last-updated-emd-{type_page}"), width=3),
                                dbc.Col(html.Div(id=f"last-updated-recipes-{type_page}"), width=3),
                                dbc.Col(html.Div(id=f"last-updated-reference-{type_page}"), width=3),
                                dbc.Col(html.Div(id=f"last-updated-death-{type_page}"), width=3)
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
    ],
    Input(f"generate-report-button-{type_page}", "n_clicks"),
    State(f"date-picker-start-{type_page}", "date"),
    State(f"date-picker-end-{type_page}", "date")
)
def generate_remd500_report(n_clicks, start_date, end_date):
    if not n_clicks:
        return [], [], [], [], "", "", "", "", ""

    if not start_date or not end_date:
        return [], [], [], [], "", "", "", "", "Не выбраны даты!"

    try:
        start_date_str = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date_str = pd.to_datetime(end_date).strftime("%Y-%m-%d")

        accepted_statuses = [
            "Документ успешно зарегистрирован",
            "Зарегистрирован",
            "Зарегистрирована",
            "Зарегистрировано"
        ]

        # Получаем данные по каждой таблице с учетом форматов даты
        # 1) ЭМД (формат "DD.MM.YYYY HH24:MI")
        query_emd = f"""
            SELECT
                doctor,
                sending_status AS status,
                'ЭМД' AS type,
                document_date
            FROM load_data_emd
            WHERE to_date(document_date, 'DD.MM.YYYY HH24:MI')
                  BETWEEN to_date('{start_date_str}', 'YYYY-MM-DD')
                      AND to_date('{end_date_str}', 'YYYY-MM-DD')
        """
        df_emd = pd.read_sql(query_emd, con=engine)

        # 2) Рецепты (формат "DD.MM.YYYY")
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
            .groupby(['doctor', 'specialty', 'type'])
            .size()
            .reset_index(name='count')
        )

        # Формируем групповой отчет: группировка по специальности
        group_pivot = (
            filtered_df
            .groupby('specialty')
            .size()
            .reset_index(name='total')
        )

        bins = [0, 99, 499, float('inf')]
        labels = ['до 100', '100-499', '>500']
        group_pivot['Категория'] = pd.cut(group_pivot['total'], bins=bins, labels=labels)
        group_summary = group_pivot.groupby('Категория')['total'].sum().reset_index()

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
            f"ЭМД: {last_updated_emd}",
            f"Рецепты: {last_updated_recipes}",
            f"Справки: {last_updated_reference}",
            f"Смертность: {last_updated_death}",
            "Отчет сформирован успешно."
        )

    except Exception as e:
        return [], [], [], [], "", "", "", "", f"Ошибка при формировании отчета: {str(e)}"
