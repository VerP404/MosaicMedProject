import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import pandas as pd
from sqlalchemy import text

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import engine

type_page = "journal"

# ---------- Словари для цветов карточек ----------
card_colors = {
    "total": {"bg": "#0d6efd", "text": "white"},  # primary (Всего)
    "unassigned": {"bg": "#ffc107", "text": "black"},  # warning (Не распределено)
    "in_progress": {"bg": "#0dcaf0", "text": "black"},  # info (В работе)
    "deadline_today": {"bg": "#6c757d", "text": "white"},  # secondary (Сегодня срок ответа)
    "overdue": {"bg": "#dc3545", "text": "white"},  # danger (Просрочено)
    "completed": {"bg": "#198754", "text": "white"},  # success (Отработано)
    "with_delay": {"bg": "#6f42c1", "text": "white"},
}

# ---------- LAYOUT ----------
layout_journal = html.Div([
    # --- Фильтры и карточка "Всего обращений" в одной строке ---
    dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row([
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Всего обращений"),
                                dbc.CardBody(
                                    html.H2(id=f"total-appeals-count-{type_page}", style={"fontWeight": "bold"})
                                )
                            ],
                            color=card_colors["total"]["bg"],
                            inverse=True,
                            className="h-100"
                        ),
                        width=2
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                dbc.Row([
                                    dbc.Col(
                                        [
                                            dbc.InputGroup(
                                                [
                                                    dbc.InputGroupText("Дата начала:"),
                                                    dcc.DatePickerSingle(
                                                        id=f"date-picker-start-{type_page}",
                                                        first_day_of_week=1,
                                                        date=f"{datetime.now().year}-01-01",
                                                        display_format="DD.MM.YYYY",
                                                        style={"width": "140px"},  # Фиксированная ширина
                                                        className="mt-1"
                                                    ),
                                                ],
                                                className="mb-2"
                                            ),
                                            dbc.InputGroup(
                                                [
                                                    dbc.InputGroupText("Дата окончания:"),
                                                    dcc.DatePickerSingle(
                                                        id=f"date-picker-end-{type_page}",
                                                        first_day_of_week=1,
                                                        date=datetime.now().date(),
                                                        display_format="DD.MM.YYYY",
                                                        style={"width": "140px"},  # Та же ширина
                                                        className="mt-1"
                                                    ),
                                                ],
                                                className="mb-2"
                                            ),
                                        ],
                                        width=4
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Применить фильтр",
                                            id=f"generate-report-button-{type_page}",
                                            color="primary",
                                            className="mt-4"
                                        ),
                                        width=8
                                    )
                                ], align="center")
                            ),
                            className="h-100"
                        ),
                        width=10
                    )
                ], align="center")
            ),
            dbc.CardBody()  # пустой body, если он не нужен
        ],
        className="mb-3"
    ),

    # --- Ряд индикаторов (7 шт.) ---
    dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Не распределено"),
                        dbc.CardBody(
                            html.H2(id=f"status-unassigned-count-{type_page}", style={"fontWeight": "bold"})
                        )
                    ],
                    color=card_colors["unassigned"]["bg"],
                    inverse=True,
                    className="h-100"
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("В работе"),
                        dbc.CardBody(
                            html.H2(id=f"status-in-progress-count-{type_page}", style={"fontWeight": "bold"})
                        )
                    ],
                    color=card_colors["in_progress"]["bg"],
                    inverse=True,
                    className="h-100"
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Сегодня срок ответа"),
                        dbc.CardBody(
                            html.H2(id=f"status-deadline-today-count-{type_page}", style={"fontWeight": "bold"})
                        )
                    ],
                    color=card_colors["deadline_today"]["bg"],
                    inverse=True,
                    className="h-100"
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Просрочено"),
                        dbc.CardBody(
                            html.H2(id=f"status-overdue-count-{type_page}", style={"fontWeight": "bold"})
                        )
                    ],
                    color=card_colors["overdue"]["bg"],
                    inverse=True,
                    className="h-100"
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Отработано"),
                        dbc.CardBody(
                            html.H2(id=f"status-completed-count-{type_page}", style={"fontWeight": "bold"})
                        )
                    ],
                    color=card_colors["completed"]["bg"],
                    inverse=True,
                    className="h-100"
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Отработано с просрочкой"),
                        dbc.CardBody(
                            html.H2(id=f"status-with_delay-count-{type_page}", style={"fontWeight": "bold"})
                        )
                    ],
                    color=card_colors["with_delay"]["bg"],
                    inverse=True,
                    className="h-100"
                ),
                width=2
            ),
        ],
        className="mb-3"
    ),

    # --- Карточка со вкладками ---
    dbc.Card(
        [
            dbc.CardHeader("Отчёт по обращениям"),
            dbc.CardBody(
                dbc.Tabs(
                    [
                        # Вкладка "Дашборд" - 2 таблицы: Ответственные и Исполнители
                        dbc.Tab(
                            html.Div([
                                html.H5("Ответственные", className="mt-2"),
                                dash_table.DataTable(
                                    id=f"responsible-table-{type_page}",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left'},
                                    export_format="xlsx",
                                    page_size=15,
                                    filter_action="native",
                                    sort_action="native",
                                    sort_mode="multi",
                                    style_header={'fontWeight': 'bold'}
                                ),
                                html.Hr(),
                                html.H5("Исполнители", className="mt-2"),
                                dash_table.DataTable(
                                    id=f"executor-table-{type_page}",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left'},
                                    export_format="xlsx",
                                    page_size=15,
                                    filter_action="native",
                                    sort_action="native",
                                    sort_mode="multi",
                                    style_header={'fontWeight': 'bold'}
                                )
                            ]),
                            label="Дашборд"
                        ),
                        # Вкладки по статусам:
                        dbc.Tab(
                            dash_table.DataTable(
                                id=f"tab-unassigned-{type_page}",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                export_format="xlsx",
                                page_size=15,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                style_header={'fontWeight': 'bold'}
                            ),
                            label="Не распределено"
                        ),
                        dbc.Tab(
                            dash_table.DataTable(
                                id=f"tab-in-progress-{type_page}",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                export_format="xlsx",
                                page_size=15,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                style_header={'fontWeight': 'bold'}
                            ),
                            label="В работе"
                        ),
                        dbc.Tab(
                            dash_table.DataTable(
                                id=f"tab-deadline-today-{type_page}",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                export_format="xlsx",
                                page_size=15,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                style_header={'fontWeight': 'bold'}
                            ),
                            label="Сегодня срок ответа"
                        ),
                        dbc.Tab(
                            dash_table.DataTable(
                                id=f"tab-overdue-{type_page}",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                export_format="xlsx",
                                page_size=15,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                style_header={'fontWeight': 'bold'}
                            ),
                            label="Просрочено"
                        ),
                        dbc.Tab(
                            dash_table.DataTable(
                                id=f"tab-completed-{type_page}",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                export_format="xlsx",
                                page_size=15,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                style_header={'fontWeight': 'bold'}
                            ),
                            label="Отработано"
                        ),
                        dbc.Tab(
                            dash_table.DataTable(
                                id=f"tab-with_delay-{type_page}",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'},
                                export_format="xlsx",
                                page_size=15,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                style_header={'fontWeight': 'bold'}
                            ),
                            label="Отработано с просрочкой"
                        ),
                    ]
                )
            ),
        ],
        className="mb-3"
    ),

    # --- Сообщения об ошибках ---
    html.Div(id=f"report-status-{type_page}", className="mt-2", style={"color": "red"})
], style={"padding": "15px"})


# ---------- CALLBACK ----------
@app.callback(
    [
        # 1) Индикаторы (7 шт.)
        Output(f"total-appeals-count-{type_page}", "children"),
        Output(f"status-unassigned-count-{type_page}", "children"),
        Output(f"status-in-progress-count-{type_page}", "children"),
        Output(f"status-deadline-today-count-{type_page}", "children"),
        Output(f"status-overdue-count-{type_page}", "children"),
        Output(f"status-completed-count-{type_page}", "children"),
        Output(f"status-with_delay-count-{type_page}", "children"),

        # 2) Данные/колонки для сводных таблиц (Ответственные)
        Output(f"responsible-table-{type_page}", "data"),
        Output(f"responsible-table-{type_page}", "columns"),

        # 3) Данные/колонки для сводных таблиц (Исполнители)
        Output(f"executor-table-{type_page}", "data"),
        Output(f"executor-table-{type_page}", "columns"),

        # 4) Таблицы по статусам:
        #    Для каждого статуса: Не распределено, В работе, Сегодня срок ответа, Просрочено, Отработано, Отработано с просрочкой
        Output(f"tab-unassigned-{type_page}", "data"),
        Output(f"tab-unassigned-{type_page}", "columns"),
        Output(f"tab-in-progress-{type_page}", "data"),
        Output(f"tab-in-progress-{type_page}", "columns"),
        Output(f"tab-deadline-today-{type_page}", "data"),
        Output(f"tab-deadline-today-{type_page}", "columns"),
        Output(f"tab-overdue-{type_page}", "data"),
        Output(f"tab-overdue-{type_page}", "columns"),
        Output(f"tab-completed-{type_page}", "data"),
        Output(f"tab-completed-{type_page}", "columns"),
        Output(f"tab-with_delay-{type_page}", "data"),
        Output(f"tab-with_delay-{type_page}", "columns"),

        # 5) Сообщение об ошибке/статус
        Output(f"report-status-{type_page}", "children"),
    ],
    Input(f"generate-report-button-{type_page}", "n_clicks"),
    [
        State(f"date-picker-start-{type_page}", "date"),
        State(f"date-picker-end-{type_page}", "date"),
    ]
)
def update_journal_appeals(n_clicks, start_date, end_date):
    if not n_clicks:
        empty_ind = ["-"] * 7
        empty_tables = [[], []]
        return (
                empty_ind +
                empty_tables * 2 +  # Сводные таблицы
                (empty_tables * 6) +  # 6 вкладок по статусам
                [""]
        )
    if not start_date or not end_date:
        return (
                ["-"] * 7 +
                ([[], []] * 2) +
                ([[], []] * 6) +
                ["Не выбраны даты!"]
        )
    try:
        start_date_str = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date_str = pd.to_datetime(end_date).strftime("%Y-%m-%d")

        # 1) Выгружаем обращения
        query_appeals = text("""
            SELECT
                a.id,
                a.status,
                a.registration_date,
                a.response_deadline,
                a.answer_date,
                a.applicant_id
            FROM journal_appeal a
            WHERE a.registration_date BETWEEN :start_date AND :end_date
        """)
        with engine.connect() as conn:
            df_appeals = pd.read_sql(query_appeals, conn, params={
                "start_date": start_date_str,
                "end_date": end_date_str
            })

        total_appeals = len(df_appeals)
        # Подсчитываем по статусам (исходя из поля status в БД)
        st_unassigned = df_appeals[df_appeals['status'] == 'не распределено'].shape[0]
        st_in_progress = df_appeals[df_appeals['status'] == 'в работе'].shape[0]
        st_deadline_today = df_appeals[df_appeals['status'] == 'сегодня срок ответа'].shape[0]
        st_overdue = df_appeals[df_appeals['status'] == 'просрочено'].shape[0]
        st_completed = df_appeals[df_appeals['status'] == 'отработано'].shape[0]
        st_with_delay = df_appeals[df_appeals['status'] == 'отработано с просрочкой'].shape[0]
        # 2) Сводные таблицы «Ответственные» / «Исполнители» с датой ответа
        #    a) Ответственные
        query_resp = f"""
            SELECT
                p.last_name || ' ' || p.first_name || ' ' || COALESCE(p.middle_name, '') AS responsible_fio,
                a.status,
                STRING_AGG(a.answer_date::text, ', ') AS answer_dates
            FROM journal_appeal a
            JOIN journal_appeal_responsible jar ON jar.appeal_id = a.id
            JOIN journal_employee e ON e.id = jar.employee_id
            JOIN journal_person p ON p.id = e.person_id
            WHERE a.registration_date BETWEEN '{start_date_str}' AND '{end_date_str}'
            GROUP BY p.last_name, p.first_name, p.middle_name, a.status
        """
        df_resp = pd.read_sql(query_resp, con=engine)

        # Группируем + считаем count
        # pivot -> (responsible_fio) x (status) => count, plus we store answer_dates
        group_resp = (
            df_resp
            .groupby(['responsible_fio', 'status'], dropna=False)
            .agg({
                'answer_dates': lambda x: ', '.join(filter(None, x)),
            })
            .reset_index()
        )
        # Отдельно count
        count_resp = (
            df_resp
            .groupby(['responsible_fio', 'status'], dropna=False)
            .size()
            .reset_index(name='count')
        )
        group_resp = group_resp.merge(count_resp, on=['responsible_fio', 'status'], how='left')

        # pivot для count
        pivot_resp_count = group_resp.pivot(
            index='responsible_fio',
            columns='status',
            values='count'
        ).fillna(0).reset_index()

        # pivot для dates
        pivot_resp_dates = group_resp.pivot(
            index='responsible_fio',
            columns='status',
            values='answer_dates'
        ).fillna('').reset_index()

        all_statuses = ['не распределено', 'в работе', 'сегодня срок ответа', 'просрочено', 'отработано',
                        'отработано с просрочкой']
        for st in all_statuses:
            if st not in pivot_resp_count.columns:
                pivot_resp_count[st] = 0
            if st not in pivot_resp_dates.columns:
                pivot_resp_dates[st] = ''

        merged_resp = pivot_resp_count[['responsible_fio']].copy()
        for st in all_statuses:
            merged_resp[f"{st}_count"] = pivot_resp_count[st]
            merged_resp[f"{st}_dates"] = pivot_resp_dates[st]

        resp_data = merged_resp.to_dict('records')
        resp_columns = [{"name": "Ответственный", "id": "responsible_fio"}]
        for st in all_statuses:
            resp_columns.append({"name": f"{st}", "id": f"{st}_count"})

        #    b) Исполнители
        query_exec = f"""
            SELECT
                p.last_name || ' ' || p.first_name || ' ' || COALESCE(p.middle_name, '') AS executor_fio,
                a.status,
                STRING_AGG(a.answer_date::text, ', ') AS answer_dates
            FROM journal_appeal a
            JOIN journal_appeal_executors jae ON jae.appeal_id = a.id
            JOIN journal_employee e ON e.id = jae.employee_id
            JOIN journal_person p ON p.id = e.person_id
            WHERE a.registration_date BETWEEN '{start_date_str}' AND '{end_date_str}'
            GROUP BY p.last_name, p.first_name, p.middle_name, a.status
        """
        df_exec = pd.read_sql(query_exec, con=engine)

        group_exec = (
            df_exec
            .groupby(['executor_fio', 'status'], dropna=False)
            .agg({'answer_dates': lambda x: ', '.join(filter(None, x))})
            .reset_index()
        )
        count_exec = (
            df_exec
            .groupby(['executor_fio', 'status'], dropna=False)
            .size()
            .reset_index(name='count')
        )
        group_exec = group_exec.merge(count_exec, on=['executor_fio', 'status'], how='left')

        pivot_exec_count = group_exec.pivot(
            index='executor_fio',
            columns='status',
            values='count'
        ).fillna(0).reset_index()
        pivot_exec_dates = group_exec.pivot(
            index='executor_fio',
            columns='status',
            values='answer_dates'
        ).fillna('').reset_index()

        for st in all_statuses:
            if st not in pivot_exec_count.columns:
                pivot_exec_count[st] = 0
            if st not in pivot_exec_dates.columns:
                pivot_exec_dates[st] = ''

        merged_exec = pivot_exec_count[['executor_fio']].copy()
        for st in all_statuses:
            merged_exec[f"{st}_count"] = pivot_exec_count[st]
            merged_exec[f"{st}_dates"] = pivot_exec_dates[st]

        exec_data = merged_exec.to_dict('records')
        exec_columns = [{"name": "Исполнитель", "id": "executor_fio"}]
        for st in all_statuses:
            exec_columns.append({"name": f"{st}", "id": f"{st}_count"})

        # 3) Таблицы по каждому статусу (Заявитель, Дата обращения, Дата ответа, Ответственный, Исполнитель)
        #    Нужно сначала получить applicant_fio, responsible_fio, executor_fio построчно.
        #    Но у нас M2M для ответственностей/исполнителей. Для простоты сделаем string_agg.
        #    a) applicant fio
        query_person = text("""
            SELECT
                p.id AS person_id,
                p.last_name || ' ' || p.first_name || ' ' || COALESCE(p.middle_name, '') AS fio
            FROM journal_person p
        """)
        with engine.connect() as conn:
            df_person = pd.read_sql(query_person, conn)

        df_appeals = df_appeals.merge(df_person, left_on="applicant_id", right_on="person_id", how="left")
        df_appeals.rename(columns={"fio": "applicant_fio"}, inplace=True)

        # responsible
        query_responsible_rows = f"""
            SELECT 
              a.id AS appeal_id,
              STRING_AGG(p.last_name || ' ' || p.first_name || ' ' || COALESCE(p.middle_name, ''), ', ') AS resp_list
            FROM journal_appeal a
            JOIN journal_appeal_responsible jar ON jar.appeal_id = a.id
            JOIN journal_employee e ON e.id = jar.employee_id
            JOIN journal_person p ON p.id = e.person_id
            WHERE a.registration_date BETWEEN '{start_date_str}' AND '{end_date_str}'
            GROUP BY a.id
        """
        df_resp_rows = pd.read_sql(query_responsible_rows, con=engine)

        # executor
        query_executor_rows = f"""
            SELECT
              a.id AS appeal_id,
              STRING_AGG(p.last_name || ' ' || p.first_name || ' ' || COALESCE(p.middle_name, ''), ', ') AS exec_list
            FROM journal_appeal a
            JOIN journal_appeal_executors jae ON jae.appeal_id = a.id
            JOIN journal_employee e ON e.id = jae.employee_id
            JOIN journal_person p ON p.id = e.person_id
            WHERE a.registration_date BETWEEN '{start_date_str}' AND '{end_date_str}'
            GROUP BY a.id
        """
        df_exec_rows = pd.read_sql(query_executor_rows, con=engine)

        # Склеим
        df_appeals = df_appeals.merge(df_resp_rows, left_on="id", right_on="appeal_id", how="left")
        df_appeals = df_appeals.merge(df_exec_rows, left_on="id", right_on="appeal_id", how="left")

        # Для удобства создадим столбцы: "Дата обращения", "Дата ответа", "Заявитель", "Ответственный", "Исполнитель"
        df_appeals["Дата обращения"] = pd.to_datetime(df_appeals["registration_date"]).dt.strftime("%d.%m.%Y")
        df_appeals["Дата ответа"] = pd.to_datetime(df_appeals["answer_date"], errors='coerce').dt.strftime("%d.%m.%Y")
        df_appeals["Дата дедлайна"] = pd.to_datetime(df_appeals["response_deadline"], errors='coerce').dt.strftime(
            "%d.%m.%Y")
        df_appeals.rename(columns={
            "applicant_fio": "Заявитель",
            "resp_list": "Ответственный",
            "exec_list": "Исполнитель"
        }, inplace=True)

        # Фильтр по статусам
        def make_table_for_status(df_source, status_name):
            df_filtered = df_source[df_source["status"] == status_name].copy()
            # Оставим нужные колонки
            df_filtered = df_filtered[
                ["Заявитель", "Дата обращения", "Дата дедлайна", "Дата ответа", "Ответственный", "Исполнитель"]]
            data = df_filtered.to_dict('records')
            columns = [{"name": col, "id": col} for col in df_filtered.columns]
            return data, columns

        # Таблица «не распределено»
        tab_unassigned_data, tab_unassigned_cols = make_table_for_status(df_appeals, "не распределено")
        # «в работе»
        tab_inprogress_data, tab_inprogress_cols = make_table_for_status(df_appeals, "в работе")
        # «сегодня срок ответа»
        tab_deadline_data, tab_deadline_cols = make_table_for_status(df_appeals, "сегодня срок ответа")
        # «просрочено»
        tab_overdue_data, tab_overdue_cols = make_table_for_status(df_appeals, "просрочено")
        # «отработано»
        tab_completed_data, tab_completed_cols = make_table_for_status(df_appeals, "отработано")
        tab_with_delay_data, tab_with_delay_cols = make_table_for_status(df_appeals, "отработано с просрочкой")

        return (
            str(total_appeals),  # Всего
            str(st_unassigned),  # Не распределено
            str(st_in_progress),  # В работе
            str(st_deadline_today),  # Сегодня срок ответа
            str(st_overdue),  # Просрочено
            str(st_completed),  # Отработано
            str(st_with_delay),  # Отработано с просрочкой

            resp_data,  # responsible data
            resp_columns,  # responsible columns
            exec_data,  # executor data
            exec_columns,  # executor columns

            tab_unassigned_data,
            tab_unassigned_cols,
            tab_inprogress_data,
            tab_inprogress_cols,
            tab_deadline_data,
            tab_deadline_cols,
            tab_overdue_data,
            tab_overdue_cols,
            tab_completed_data,
            tab_completed_cols,
            tab_with_delay_data,
            tab_with_delay_cols,

            ""  # Сообщение об ошибке
        )

    except Exception as e:
        return (
                ["-"] * 7 +  # индикаторы
                ([[], []] * 2) +  # pivot-таблицы
                ([[], []] * 6) +  # 5 статусных таблиц
                [f"Ошибка: {str(e)}"]
        )
