# apps/analytical_app/pages/head/dn_job/page.py

from dash import html, dcc, dash_table, Input, Output, State, exceptions, callback_context
import pandas as pd
from sqlalchemy import text
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.pages.head.dn_job.query import sql_head_dn_job_nested
from apps.analytical_app.components.filters import filter_years, filter_status, status_groups
from apps.analytical_app.query_executor import engine

type_page = "head-dn-job"

# --- Список организаций для фильтра ---
with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT DISTINCT org_prof_m FROM load_data_dn_work_iszl "
        "WHERE org_prof_m IS NOT NULL AND org_prof_m <> '' ORDER BY org_prof_m"
    )).fetchall()
org_options = [{"label": r[0], "value": r[0]} for r in rows]

# --- layout ---
head_dn_job = html.Div([

    # Хранилище данных
    dcc.Store(id=f"store-{type_page}", storage_type="memory"),

    # Общие фильтры: кнопка «Получить данные», год, организации, спиннер
    dbc.Row(
        [
            dbc.Col(
                html.Button(
                    "Получить данные",
                    id=f"btn-get-{type_page}",
                    className="btn btn-primary"
                ),
                width="auto"
            ),
            dbc.Col(
                dbc.Button(
                    "Справка",
                    id=f"btn-help-{type_page}",
                    color="warning",
                    className="ms-2"
                ),
                width="auto"
            ),
            dbc.Col(filter_years(type_page), width=1),
            dbc.Col(
                dcc.Dropdown(
                    id=f"dropdown-org-{type_page}",
                    options=org_options,
                    multi=True,
                    placeholder="Организации"
                ),
                width=3
            ),
            dbc.Col(
                dbc.RadioItems(
                    id=f"status-filter-mode-{type_page}",
                    options=[
                        {"label": "Все статусы", "value": "all"},
                        {"label": "По статусу талона", "value": "by_status"},
                    ],
                    value="all",
                    inline=True
                ),
                width="auto",
                className="ms-3"
            ),
            dbc.Col(
                html.Div(
                    filter_status(type_page),
                    id=f"status-filters-container-{type_page}",
                    style={"display": "none"}
                ),
                width=6
            ),
            dbc.Col(
                dcc.Loading(id=f"loading-{type_page}", type="default"),
                width="auto"
            ),
        ],
        align="center",
        className="mb-3"
    ),
    dbc.Offcanvas(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Инструкция по работе с модулем", className="mb-3 fw-bold"),
                    dbc.ListGroup(
                        [
                            dbc.ListGroupItem([
                                html.Span("1. ", style={"fontWeight": "bold"}),
                                "Выберите год и/или организации и/или статусы талонов ОМС, нажмите ",
                                html.Code("Получить данные"),
                                "."
                            ]),
                            dbc.ListGroupItem([
                                html.Span("2. ", style={"fontWeight": "bold"}),
                                "Вкладка",
                                html.Span(" «Данные» ", style={"fontWeight": "bold"}),
                                "— содержит информацию для работы с пациентами из ИСЗЛ и WEB-ОМС. "
                                "С помощью фильтров можно отобрать пациентов."
                            ]),
                            dbc.ListGroupItem([
                                html.Span("2.1 ", style={"fontWeight": "bold"}),
                                "Таблица",
                                html.Span(" «Пациенты» ", style={"fontWeight": "bold"}),
                                "— отфильтрованные пациенты. При выборе пациента открывается информация о нём."
                            ]),
                            dbc.ListGroupItem([
                                html.Span("2.2 ", style={"fontWeight": "bold"}),
                                "Таблица",
                                html.Span(" «Диспансерные записи» ", style={"fontWeight": "bold"}),
                                "— записи пациента в ИСЗЛ с отметкой о дубликате и наличии талона. ",
                                html.Span("Синий статус", style={"color": "#0d6efd", "fontWeight": "bold"}),
                                " означает неверное место обслуживания."
                            ]),
                            dbc.ListGroupItem([
                                html.Span("2.3 ", style={"fontWeight": "bold"}),
                                "Таблица",
                                html.Span(" «Талоны» ", style={"fontWeight": "bold"}),
                                "— талоны по цели 3 у пациента. ",
                                html.Span("Синий статус", style={"color": "#0d6efd", "fontWeight": "bold"}),
                                " означает неверное место обслуживания."
                            ]),
                            dbc.ListGroupItem([
                                html.Span("3. ", style={"fontWeight": "bold"}),
                                "Вкладка",
                                html.Span(" «Отчёт» ", style={"fontWeight": "bold"}),
                                "— свод по месяцам и выбранным фильтрам. Для детализации кликайте по ячейке сводной таблицы."
                            ]),
                        ],
                        flush=True
                    )

                ]
            ),
            className="h-100"
        ),
        id=f"offcanvas-help-{type_page}",
        title="Справка",
        is_open=False,
        placement="end",
        backdrop=True,
        scrollable=True
    ),
    # Вкладки «Данные» и «Отчёт»
    dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Диспансерное наблюдение работающих граждан",
                                className="mb-0"
                            ),
                            width="auto"
                        ),
                        dbc.Col(
                            html.Div(
                                id=f"last-updated-main-{type_page}",
                                style={
                                    "textAlign": "right",
                                    "fontWeight": "normal",
                                    "fontSize": "0.9rem"
                                }
                            ),
                            width=True
                        ),
                    ],
                    align="center",
                    justify="between"
                )
            ),
            dbc.CardBody(
                dbc.Tabs(
                    id=f"tabs-{type_page}",
                    active_tab="tab-data",
                    children=[

                        # Вкладка «Данные»
                        dbc.Tab(
                            label="Данные",
                            tab_id="tab-data",
                            children=[

                                # Фильтры внутри «Данных»
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id=f"dropdown-duplicate-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Только дубликаты", "value": "dup_only"},
                                                    {"label": "Без дубликатов", "value": "no_dup"},
                                                ],
                                                value="all",
                                                clearable=False
                                            ),
                                            width=2
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id=f"dropdown-has-tal-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Есть талон", "value": "has"},
                                                    {"label": "Нет талона", "value": "no"},
                                                ],
                                                value="all",
                                                clearable=False
                                            ),
                                            width=2
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id=f"dropdown-has-disp-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Есть запись", "value": "has"},
                                                    {"label": "Нет записи", "value": "no"},
                                                ],
                                                value="all",
                                                clearable=False
                                            ),
                                            width=2
                                        ),
                                    ],
                                    align="center",
                                    className="mb-3"
                                ),

                                # Собственно таблицы «Данные»
                                dbc.Row(
                                    [
                                        # Список пациентов
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Пациенты"),
                                                    dbc.CardBody(
                                                        dash_table.DataTable(
                                                            id=f"tbl-patients-{type_page}",
                                                            columns=[
                                                                {"name": "ЕНП", "id": "enp"},
                                                                {"name": "Пациент", "id": "patient"},
                                                                {"name": "Дата рож.", "id": "birth_date"},
                                                            ],
                                                            row_selectable="single",
                                                            selected_rows=[],
                                                            active_cell=None,
                                                            page_action="none",
                                                            style_table={"height": "500px", "overflowY": "auto"},
                                                            style_cell={"textAlign": "left", "padding": "4px"},
                                                            sort_action="native",
                                                            sort_mode="multi",
                                                            filter_action="native",
                                                        )
                                                    )
                                                ]
                                            ),
                                            width=5
                                        ),

                                        # Диспансерные записи и талоны
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            dbc.Row([
                                                                dbc.Col(
                                                                    html.H5("Диспансерные записи", className="mb-0"),
                                                                    width="auto"),
                                                                dbc.Col(
                                                                    html.Div(id=f"last-updated-dn-{type_page}",
                                                                             style={"textAlign": "right",
                                                                                    "fontWeight": "normal"}),
                                                                    width=True
                                                                )
                                                            ], align="center", justify="between")
                                                        ),
                                                        dbc.CardBody(
                                                            dash_table.DataTable(
                                                                id=f"tbl-disp-{type_page}",
                                                                columns=[
                                                                    {"name": "Дата", "id": "disp_date"},
                                                                    {"name": "Диагноз", "id": "ds_norm"},
                                                                    {"name": "ID", "id": "external_id"},
                                                                    {"name": "МО прикр.", "id": "mo_prikreplenia"},
                                                                    {"name": "Орг. проф.", "id": "org_prof_m"},
                                                                    {"name": "Дубликат", "id": "duplicate"},
                                                                    {"name": "Есть талон", "id": "has_tal"},
                                                                ],
                                                                page_action="none",
                                                                style_table={"height": "240px", "overflowY": "auto"},
                                                                style_cell={"textAlign": "left", "padding": "4px"},
                                                            )
                                                        )
                                                    ],
                                                    className="mb-4"
                                                ),

                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            dbc.Row([
                                                                dbc.Col(html.H5("Талоны (цель=3)", className="mb-0"),
                                                                        width="auto"),
                                                                dbc.Col(
                                                                    html.Div(id=f"last-updated-talons-{type_page}",
                                                                             style={"textAlign": "right",
                                                                                    "fontWeight": "normal"}),
                                                                    width=True
                                                                )
                                                            ], align="center", justify="between")
                                                        ),
                                                        dbc.CardBody(
                                                            dash_table.DataTable(
                                                                id=f"tbl-tal-{type_page}",
                                                                columns=[
                                                                    {"name": "Талон", "id": "talon"},
                                                                    {"name": "Период", "id": "report_period"},
                                                                    {"name": "Место", "id": "place_service"},
                                                                    {"name": "Статус", "id": "status"},
                                                                    {"name": "Лечение", "id": "treatment_end"},
                                                                    {"name": "Врач", "id": "doctor"},
                                                                    {"name": "ds1", "id": "ds1"},
                                                                    {"name": "ds2", "id": "ds2"},
                                                                    {"name": "Есть запись", "id": "has_disp"},
                                                                ],
                                                                page_action="none",
                                                                style_table={"height": "240px", "overflowY": "auto"},
                                                                style_cell={"textAlign": "left", "padding": "4px"},
                                                            )
                                                        )
                                                    ]
                                                ),
                                            ],
                                            width=7
                                        ),
                                    ],
                                    className="g-3"
                                ),
                            ]
                        ),

                        # Вкладка «Отчёт»
                        dbc.Tab(
                            label="Отчёт",
                            tab_id="tab-report",
                            children=[

                                # Фильтр «Место обслуживания»
                                dbc.Row(
                                    [
                                        dbc.Col(html.Label("Место обслуживания:"), width="auto"),
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id=f"dropdown-place-service-report-{type_page}",
                                                options=[
                                                    {"label": "Не учитывать. Все записи.", "value": "all"},
                                                    {"label": "17 — По месту служебной деятельности", "value": "17"},
                                                    {"label": "Не указано", "value": "-"},
                                                ],
                                                value="17",
                                                clearable=False,
                                                style={"width": "350px"}
                                            ),
                                            width="auto"
                                        ),
                                        dbc.Col(html.Label("Дубликат:"), width="auto", className="ms-4"),
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id=f"dropdown-dup-report-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Да", "value": "yes"},
                                                    {"label": "Нет", "value": "no"},
                                                ],
                                                value="no",
                                                clearable=False,
                                                style={"width": "140px"}
                                            ),
                                            width="auto"
                                        ),
                                    ],
                                    align="center",
                                    className="mb-2"
                                ),

                                # Карточка «Отчёт»
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Отчёт. По месяцу прохождения."),
                                        dbc.CardBody(
                                            [
                                                dash_table.DataTable(
                                                    id=f"tbl-report-{type_page}",
                                                    columns=[],
                                                    data=[],
                                                    page_size=20,
                                                    style_table={"overflowX": "auto"},
                                                    style_cell={"textAlign": "center", "padding": "4px"},
                                                    export_format="xlsx",
                                                    export_headers="display"
                                                )
                                            ]
                                        )
                                    ],
                                    className="mb-3"
                                ),

                                # Карточка «Детализация»
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Детализация"),
                                        dbc.CardBody(
                                            [
                                                dash_table.DataTable(
                                                    id=f"tbl-report-detail-{type_page}",
                                                    columns=[],
                                                    data=[],
                                                    page_size=10,
                                                    style_table={"overflowX": "auto"},
                                                    style_cell={"textAlign": "left", "padding": "4px"},
                                                    style_header={"backgroundColor": "#f0f0f0"},
                                                    export_format="xlsx",
                                                    export_headers="display",
                                                    filter_action="native",
                                                    sort_action="native",
                                                    sort_mode="single",
                                                    sort_by=[
                                                        {"column_id": "patient", "direction": "asc"}
                                                    ]
                                                )
                                            ]
                                        )
                                    ]
                                ),
                            ]
                        ),
                        dbc.Tab(
                            label="Охват",
                            tab_id="tab-coverage",
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Охват работающего населения"),
                                                    dbc.CardBody(
                                                        html.H2(
                                                            id=f"coverage-output-{type_page}",
                                                            className="text-center fw-bold"
                                                        )
                                                    )
                                                ],
                                                color="info",
                                                inverse=True,
                                                className="h-100"
                                            ),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Уникальные пациенты в ИСЗЛ"),
                                                    dbc.CardBody(
                                                        html.H2(
                                                            id=f"coverage-iszl-output-{type_page}",
                                                            className="text-center fw-bold"
                                                        )
                                                    )
                                                ],
                                                color="secondary",
                                                inverse=True,
                                                className="h-100"
                                            ),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        "Уникальные пациенты  в талонах по месту работы (17)"),
                                                    dbc.CardBody(
                                                        html.H2(
                                                            id=f"coverage-work-output-{type_page}",
                                                            className="text-center fw-bold"
                                                        )
                                                    )
                                                ],
                                                color="warning",
                                                inverse=True,
                                                className="h-100"
                                            ),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Уникальные пациенты  в талонах по месту работы (17) - оплаченные"),
                                                    dbc.CardBody(
                                                        html.H2(
                                                            id=f"coverage-work-paid-output-{type_page}",
                                                            className="text-center fw-bold"
                                                        )
                                                    )
                                                ],
                                                color="success",
                                                inverse=True,
                                                className="h-100"
                                            ),
                                            width=3
                                        ),
                                    ],
                                    className="mb-3",
                                    align="center"
                                )
                            ]
                        ),
                    ]
                )
            ),
        ],
        className="mb-3"
    ),

    # Место для сообщений о статусе/ошибках
    html.Div(id=f"report-status-{type_page}", style={"color": "red"}),

], style={"padding": "15px"})


# --- CALLBACKS ---
@app.callback(
    Output(f"tbl-patients-{type_page}", "selected_rows"),
    Input(f"tbl-patients-{type_page}", "active_cell"),
    State(f"tbl-patients-{type_page}", "selected_rows"),
)
def toggle_row(active_cell, selected_rows):
    if not active_cell:
        # клик вне таблицы или инициализация — ничего не меняем
        return selected_rows

    clicked_row = active_cell["row"]
    # если уже выбрана та же строка — сброс
    if selected_rows == [clicked_row]:
        return []
    # иначе — ставим выбор на эту строку
    return [clicked_row]


@app.callback(
    Output(f"dropdown-org-{type_page}", "options"),
    Output(f"dropdown-org-{type_page}", "value"),
    Input(f"dropdown-year-{type_page}", "value"),
)
def _update_org_options(year):
    # если год не выбран — чистим
    if not year:
        return [], []

    sql = f"""
    SELECT DISTINCT org_prof_m
    FROM load_data_dn_work_iszl
    WHERE org_prof_m IS NOT NULL
      AND org_prof_m <> ''
      AND EXTRACT(YEAR FROM TO_TIMESTAMP(date, 'DD.MM.YYYY HH24:MI:SS')) = {year}
    ORDER BY org_prof_m
    """
    df = pd.read_sql(sql, engine)

    opts = [{"label": org, "value": org} for org in df["org_prof_m"]]
    return opts, []  # кроме опций очищаем текущее значение


# 1) Загрузка всех данных по году (без фильтра по организации)
@app.callback(
    Output(f"store-{type_page}", "data"),
    Output(f"loading-{type_page}", "children"),
    Output(f"last-updated-dn-{type_page}", "children"),
    Output(f"last-updated-talons-{type_page}", "children"),
    Output(f"last-updated-main-{type_page}", "children"),
    Input(f"btn-get-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"status-selection-mode-{type_page}", "value"),
    State(f"status-group-radio-{type_page}", "value"),
    State(f"status-individual-dropdown-{type_page}", "value"),
)
def load_all(n_clicks, year, mode, sel_group, sel_ind):
    if not n_clicks:
        raise exceptions.PreventUpdate

    sql = sql_head_dn_job_nested(year)
    df = pd.read_sql(sql, con=engine)

    if "ds2" in df:
        df["ds2"] = df["ds2"].apply(
            lambda v: ", ".join(v) if isinstance(v, (list, tuple)) else (str(v) if v else "")
        )

    with engine.connect() as conn:
        row_dn = conn.execute(text(
            "SELECT MAX(updated_at) FROM load_data_dn_work_iszl"
        )).fetchone()
        row_tal = conn.execute(text(
            "SELECT MAX(updated_at) FROM load_data_talons"
        )).fetchone()

    def fmt(r):
        return r[0].strftime("%d.%m.%Y %H:%M") if r and r[0] else "Нет данных"

    last_dn = fmt(row_dn)
    last_tal = fmt(row_tal)
    main_str = f"ИСЗЛ: {last_dn} | Талоны: {last_tal}"

    return (
        df.to_dict("records"),
        None,
        last_dn,
        last_tal,
        main_str
    )


# 2) Формирование списка пациентов, **фильтруя** по выбранным организациям
@app.callback(
    Output(f"tbl-patients-{type_page}", "data"),
    Input(f"store-{type_page}", "data"),
    Input(f"dropdown-org-{type_page}", "value"),
    Input(f"dropdown-duplicate-{type_page}", "value"),
    Input(f"dropdown-has-tal-{type_page}", "value"),
    Input(f"dropdown-has-disp-{type_page}", "value"),
    Input(f"status-selection-mode-{type_page}", "value"),
    Input(f"status-group-radio-{type_page}", "value"),
    Input(f"status-individual-dropdown-{type_page}", "value"),
    Input(f"status-filter-mode-{type_page}", "value"),
)
def fill_patients(all_rows, selected_orgs, dup_filter, has_tal_filter, has_disp_filter, status_mode, sel_group,
                  sel_ind, status_filter_mode):
    if not all_rows:
        return []
    # 1) фильтруем по организациям
    rows = all_rows
    if selected_orgs:
        rows = [r for r in rows if r['org_prof_m'] in selected_orgs]

    if status_filter_mode == "by_status" and status_mode in ("group", "individual"):
        # получаем список статусов
        if status_mode == "group":
            status_list = status_groups[sel_group]
        else:
            status_list = sel_ind or []
        # собираем enp пациентов, у которых есть хотя бы один talon с нужным статусом
        enps = {r["enp"] for r in rows if r.get("status") in status_list}
        rows = [r for r in rows if r["enp"] in enps]
    seen = set()
    out = []
    for r in rows:
        enp = r['enp']
        if enp in seen:
            continue
        # собираем все строки пациента
        patient_rows = [x for x in rows if x['enp'] == enp]
        # формируем списки disp и tal
        disp = [dict(d, **{'has_tal': False}) for d in patient_rows if d.get('external_id')]
        seen_t = set()
        tal = []
        for d in patient_rows:
            if d.get('talon') and d['talon'] not in seen_t:
                seen_t.add(d['talon'])
                tal.append(dict(d, **{'has_disp': False}))
        # отмечаем совпадения (месяц/год/диагноз)
        for t in tal:
            for d in disp:
                if d['duplicate']:
                    continue
                same = (t['month_end'] == d['month_d'] and t['year_end'] == d['year_d'])
                match = (d['ds_norm'] == t['ds1']) or (d['ds_norm'] in (t.get('ds2') or []))
                if same and match:
                    t['has_disp'] = True
                    break
        for d in disp:
            if d['duplicate']:
                continue
            for t in tal:
                same = (t['month_end'] == d['month_d'] and t['year_end'] == d['year_d'])
                match = (d['ds_norm'] == t['ds1']) or (d['ds_norm'] in (t.get('ds2') or []))
                if same and match:
                    d['has_tal'] = True
                    break
        # раскраска флагов
        for d in disp:
            d['has_tal'] = '🔵' if d.get('place_service') == '-' else ('🟢' if d.get('has_tal') else '🔴')
            d['duplicate'] = '🔴' if d.get('duplicate') else '🟢'
        for t in tal:
            t['has_disp'] = '🔵' if t.get('place_service') == '-' else ('🟢' if t.get('has_disp') else '🔴')
            t['duplicate'] = '🔴' if t.get('duplicate') else '🟢'
        # проверяем, остались ли записи после фильтров
        # фильтр дубликатов
        if dup_filter == 'dup_only' and not (
                any(d['duplicate'] == '🔴' for d in disp) or any(t['duplicate'] == '🔴' for t in tal)):
            continue
        if dup_filter == 'no_dup' and (
                any(d['duplicate'] == '🔴' for d in disp) or any(t['duplicate'] == '🔴' for t in tal)):
            continue
        # фильтр наличия талона
        if has_tal_filter == 'has' and not any(d['has_tal'] == '🟢' for d in disp):
            continue
        if has_tal_filter == 'no' and not any(d['has_tal'] == '🔴' for d in disp):
            continue
        # фильтр наличия записи
        if has_disp_filter == 'has' and not any(t['has_disp'] == '🟢' for t in tal):
            continue
        if has_disp_filter == 'no' and not any(t['has_disp'] == '🔴' for t in tal):
            continue
        # добавляем пациента
        out.append({
            'enp': enp,
            'patient': r['patient'],
            'birth_date': r['birth_date'],
        })
        seen.add(enp)
    out.sort(key=lambda x: x['patient'])
    return out


# 3) Объединённый колбэк: сброс при нажатии «Получить данные» и отрисовка деталей при выборе пациента
@app.callback(
    Output(f"tbl-disp-{type_page}", "data"),
    Output(f"tbl-tal-{type_page}", "data"),
    Input(f"tbl-patients-{type_page}", "selected_rows"),
    State(f"tbl-patients-{type_page}", "data"),
    State(f"store-{type_page}", "data"),
)
def update_details(selected_rows, patients, all_rows):
    if not selected_rows or not patients or not all_rows:
        return [], []
    idx = selected_rows[0]
    selected_enp = patients[idx]['enp']
    # все диспансерные записи пациента
    disp = [dict(d, **{'has_tal': False}) for d in all_rows if d.get('external_id') and d['enp'] == selected_enp]
    # все талоны пациента
    seen_t = set()
    tal = []
    for d in all_rows:
        if d.get('talon') and d['enp'] == selected_enp and d['talon'] not in seen_t:
            seen_t.add(d['talon'])
            tal.append(dict(d, **{'has_disp': False}))
    # отмечаем совпадения и раскрашиваем флаги аналогично выше
    for t in tal:
        for d in disp:
            if d['duplicate']: continue
            same = (t['month_end'] == d['month_d'] and t['year_end'] == d['year_d'])
            match = (d['ds_norm'] == t['ds1']) or (d['ds_norm'] in (t.get('ds2') or []))
            if same and match:
                t['has_disp'] = True
                break
    for d in disp:
        if d['duplicate']: continue
        for t in tal:
            same = (t['month_end'] == d['month_d'] and t['year_end'] == d['year_d'])
            match = (d['ds_norm'] == t['ds1']) or (d['ds_norm'] in (t.get('ds2') or []))
            if same and match:
                d['has_tal'] = True
                break
    for d in disp:
        d['has_tal'] = '🟢' if d.get('has_tal') else '🔴'
        d['duplicate'] = '🔴' if d.get('duplicate') else '🟢'
        if d.get('place_service') == '-': d['has_tal'] = '🔵'
    for t in tal:
        t['has_disp'] = '🟢' if t.get('has_disp') else '🔴'
        if t.get('place_service') == '-': t['has_disp'] = '🔵'
    return disp, tal


@app.callback(
    Output(f"tbl-report-{type_page}", "columns"),
    Output(f"tbl-report-{type_page}", "data"),
    Input(f"store-{type_page}", "data"),
    Input(f"dropdown-year-{type_page}", "value"),
    Input(f"dropdown-org-{type_page}", "value"),
    Input(f"status-filter-mode-{type_page}", "value"),
    Input(f"status-selection-mode-{type_page}", "value"),
    Input(f"status-group-radio-{type_page}", "value"),
    Input(f"status-individual-dropdown-{type_page}", "value"),
    Input(f"dropdown-place-service-report-{type_page}", "value"),
    Input(f"dropdown-dup-report-{type_page}", "value"),
)
def update_report(all_rows, year, orgs,
                  status_filter_mode, status_mode, sel_group, sel_ind,
                  place_service, dup_report):
    if not all_rows:
        return [], []

    df = pd.DataFrame(all_rows)

    # 1) год, организации
    if year:
        df = df[df["year_d"] == year]
    if orgs:
        df = df[df["org_prof_m"].isin(orgs)]

    # 2) фильтрация по статусу ТАЛОНОВ
    if status_filter_mode == "by_status" and status_mode in ("group", "individual"):
        if status_mode == "group":
            status_list = status_groups[sel_group]
        else:
            status_list = sel_ind or []
        # ВАЖНО: фильтруем сами талоны, а не patients по enp
        df = df[df["status"].isin(status_list)]

    # 3) фильтр по месту обслуживания
    if place_service != "all":
        df = df[df["place_service"] == place_service]
    # 4)  фильтр дубликатов
    if dup_report == "yes":
        df = df[df["duplicate"] == True]
    elif dup_report == "no":
        df = df[df["duplicate"] == False]
    # 5) делаем pivot сразу по отфильтрованным строкам
    grp = (
        df.groupby(["org_prof_m", "month_d"])["enp"]
        .nunique()
        .reset_index(name="count")
    )
    pivot = grp.pivot(index="org_prof_m", columns="month_d", values="count") \
        .fillna(0).astype(int)

    # 5) переименовываем месяцы и добавляем недостающие
    month_map = {
        1: "янв", 2: "февр", 3: "мар", 4: "апр",
        5: "май", 6: "июн", 7: "июл", 8: "авг",
        9: "сент", 10: "окт", 11: "ноя", 12: "дек"
    }
    pivot = pivot.rename(columns=month_map)
    for m in month_map.values():
        if m not in pivot.columns:
            pivot[m] = 0

    # 6) считаем «Всего» и готовим итоговый DF
    df_out = pivot.reset_index().rename(columns={"org_prof_m": "Организация"})
    months = [month_map[i] for i in range(1, 13)]
    df_out["Всего"] = df_out[months].sum(axis=1)
    cols = ["Организация", "Всего"] + months
    df_out = df_out[cols]

    # 7) строка Итого
    totals = df_out[months + ["Всего"]].sum()
    total_row = {"Организация": "Итого", **totals.to_dict()}
    df_out = pd.concat([df_out, pd.DataFrame([total_row])], ignore_index=True)

    # 8) отдаём в таблицу
    columns = [{"name": c, "id": c} for c in df_out.columns]
    data = df_out.to_dict("records")
    return columns, data


@app.callback(
    Output(f"tbl-report-detail-{type_page}", "columns"),
    Output(f"tbl-report-detail-{type_page}", "data"),
    Output(f"tbl-report-{type_page}", "active_cell"),
    # Input смены ячейки
    Input(f"tbl-report-{type_page}", "active_cell"),
    # Все фильтры, которые должны его сбрасывать:
    Input(f"dropdown-year-{type_page}", "value"),
    Input(f"dropdown-org-{type_page}", "value"),
    Input(f"status-filter-mode-{type_page}", "value"),
    Input(f"status-selection-mode-{type_page}", "value"),
    Input(f"status-group-radio-{type_page}", "value"),
    Input(f"status-individual-dropdown-{type_page}", "value"),
    Input(f"dropdown-place-service-report-{type_page}", "value"),
    Input(f"dropdown-dup-report-{type_page}", "value"),
    State(f"store-{type_page}", "data"),
)
def detail_on_click(active_cell,
                    year, orgs,
                    status_filter_mode, status_mode, sel_group, sel_ind,
                    place_service, dup_report,
                    all_rows):
    trig = callback_context.triggered[0]["prop_id"].split(".")[0]
    # 1) Любой фильтр (кроме клика по таблице) — чистим и сбрасываем выделение
    filter_ids = {
        f"dropdown-year-{type_page}",
        f"dropdown-org-{type_page}",
        f"status-filter-mode-{type_page}",
        f"status-selection-mode-{type_page}",
        f"status-group-radio-{type_page}",
        f"status-individual-dropdown-{type_page}",
        f"dropdown-place-service-report-{type_page}",
        f"dropdown-dup-report-{type_page}",
    }
    if trig in filter_ids:
        return [], [], None

    # 2) Если еще нет данных или не кликнули по ячейке — ничего не показываем
    if not all_rows or not active_cell:
        return [], [], None

    # === далее ваша старая логика детализации ===
    df = pd.DataFrame(all_rows)
    # общий фильтр по году/орг
    if year:
        df = df[df["year_d"] == year]
    if orgs:
        df = df[df["org_prof_m"].isin(orgs)]
    # фильтр по статусу
    if status_filter_mode == "by_status" and status_mode in ("group", "individual"):
        if status_mode == "group":
            statuses = status_groups[sel_group]
        else:
            statuses = sel_ind or []
        df = df[df["status"].isin(statuses)]
    # фильтр по месту
    if place_service and place_service != "all":
        df = df[df["place_service"] == place_service]
    if dup_report == "yes":
        df = df[df["duplicate"] == True]
    elif dup_report == "no":
        df = df[df["duplicate"] == False]
    # пересчитаем pivot чтобы знать, где «Итого»
    grp = (
        df.groupby(["org_prof_m", "month_d"])["enp"]
        .nunique()
        .reset_index(name="count")
    )
    pivot = grp.pivot(index="org_prof_m", columns="month_d", values="count") \
        .fillna(0).astype(int)
    month_map = {1: "янв", 2: "февр", 3: "мар", 4: "апр", 5: "май", 6: "июн",
                 7: "июл", 8: "авг", 9: "сент", 10: "окт", 11: "ноя", 12: "дек"}
    pivot = pivot.rename(columns=month_map)
    org_list = list(pivot.index)
    total_idx = len(org_list)

    row_i = active_cell["row"]
    col_id = active_cell["column_id"]

    # строим detail
    if row_i == total_idx:  # клик по «Итого»
        detail = df.copy()
    else:
        org = org_list[row_i]
        detail = df[df["org_prof_m"] == org]

    if col_id not in ("Организация", "Всего"):
        inv = {v: k for k, v in month_map.items()}
        m = inv.get(col_id)
        if m:
            detail = detail[detail["month_d"] == m]

    # формируем колонки + данные
    if detail.empty:
        return [], [], None

    # маппинг заголовков
    COL_MAP = {
        "enp": "ЕНП", "patient": "Пациент", "birth_date": "ДР",
        "talon": "ОМС: Талон", "report_period": "ОМС: Период",
        "place_service": "ОМС: Место", "status": "ОМС: Статус",
        "treatment_end": "ОМС: Дата", "doctor": "ОМС: Врач",
        "doctor_profile": "ОМС: Профиль", "ds1": "ОМС: ds1",
        "ds2": "ОМС: ds2", "external_id": "ИСЗЛ: Номер",
        "mo_prikreplenia": "ИСЗЛ: Прикрепление",
        "org_prof_m": "ИСЗЛ: Организация", "ds_norm": "ИСЗЛ: Диагноз",
        "disp_date": "ИСЗЛ: Дата", "month_d": "ИСЗЛ: Месяц",
        "year_d": "ИСЗЛ: Год", "duplicate": "Проверка дубликата"
    }
    # уберем month_end/year_end если они есть
    detail = detail.drop(columns=["month_end", "year_end"], errors="ignore")

    cols_final = [c for c in detail.columns if c in COL_MAP]
    columns = [{"name": COL_MAP[c], "id": c} for c in cols_final]
    data = detail[cols_final].to_dict("records")

    # возвращаем detail + НЕ сбрасываем active_cell (ставим его же)
    return columns, data, active_cell


@app.callback(
    [
        Output(f"status-group-container-{type_page}", "style"),
        Output(f"status-individual-container-{type_page}", "style"),
    ],
    Input(f"status-selection-mode-{type_page}", "value"),
)
def toggle_status_selection_mode(mode):
    if mode == "group":
        return {"display": "block"}, {"display": "none"}
    # mode == "individual"
    return {"display": "none"}, {"display": "block"}


@app.callback(
    Output(f"status-filters-container-{type_page}", "style"),
    Input(f"status-filter-mode-{type_page}", "value"),
)
def toggle_status_filters(mode):
    # если выбрали «По статусу» — показываем, иначе — скрываем
    return {"display": "block"} if mode == "by_status" else {"display": "none"}


@app.callback(
    Output(f"offcanvas-help-{type_page}", "is_open"),
    Input(f"btn-help-{type_page}", "n_clicks"),
    State(f"offcanvas-help-{type_page}", "is_open"),
)
def toggle_help(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


@app.callback(
    Output(f"coverage-output-{type_page}",            "children"),
    Output(f"coverage-iszl-output-{type_page}",       "children"),
    Output(f"coverage-work-output-{type_page}",       "children"),
    Output(f"coverage-work-paid-output-{type_page}",  "children"),
    Input(f"dropdown-year-{type_page}",               "value"),
)
def update_coverage_all(year):
    if not year:
        return "", "", "", ""

    sql_cov = f"""
    WITH base AS (
      SELECT
        enp,
        {year} - EXTRACT(YEAR FROM to_date(birth_date, 'DD-MM-YYYY')) AS age,
        gender
      FROM load_data_talons
      WHERE goal = '3'
        AND EXTRACT(YEAR FROM to_date(treatment_end, 'DD-MM-YYYY')) = {year}
    )
    SELECT COUNT(DISTINCT enp) AS patient_count
    FROM base
    WHERE (gender = 'М' AND age < 65)
       OR (gender = 'Ж' AND age < 60)
    """
    df_cov = pd.read_sql(sql_cov, con=engine)
    cov_count = int(df_cov["patient_count"].iloc[0]) if not df_cov.empty else 0

    sql_iszl = f"""
    SELECT COUNT(DISTINCT enp) AS patient_count
    FROM load_data_dn_work_iszl
    WHERE EXTRACT(YEAR FROM TO_TIMESTAMP(date, 'DD.MM.YYYY HH24:MI:SS')) = {year}
    """
    df_iszl = pd.read_sql(sql_iszl, con=engine)
    iszl_count = int(df_iszl["patient_count"].iloc[0]) if not df_iszl.empty else 0

    sql_work = f"""
    SELECT COUNT(DISTINCT enp) AS patient_count
    FROM load_data_talons
    WHERE goal = '3'
      AND EXTRACT(YEAR FROM TO_DATE(treatment_end, 'DD-MM-YYYY')) = {year}
      AND place_service = '17'
    """
    df_work = pd.read_sql(sql_work, con=engine)
    work_count = int(df_work["patient_count"].iloc[0]) if not df_work.empty else 0

    sql_work_paid = f"""
    SELECT COUNT(DISTINCT enp) AS patient_count
    FROM load_data_talons
    WHERE goal = '3'
      AND EXTRACT(YEAR FROM TO_DATE(treatment_end, 'DD-MM-YYYY')) = {year}
      AND place_service = '17'
      AND status = '3'
    """
    df_work_paid = pd.read_sql(sql_work_paid, con=engine)
    work_paid_count = int(df_work_paid["patient_count"].iloc[0]) if not df_work_paid.empty else 0

    return (
        f"{cov_count} чел.",
        f"{iszl_count} чел.",
        f"{work_count} чел.",
        f"{work_paid_count} чел."
    )
