# apps/analytical_app/pages/head/dn_job/page.py

from dash import html, dcc, dash_table, Input, Output, State, exceptions, callback_context
import pandas as pd
from sqlalchemy import text
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.pages.head.dn_job.query import (
    sql_dn_job_disp,
    sql_dn_job_tal,
    sql_dn_job_orgs,
    sql_dn_job_coverage,
)
from apps.analytical_app.pages.head.dn_job.services import (
    build_store_payload,
    get_status_list,
    patient_passes_filters,
    filter_flat_rows,
    build_report_table,
    build_report_detail,
)
from apps.analytical_app.components.filters import filter_years, filter_status
from apps.analytical_app.query_executor import engine

type_page = "head-dn-job"

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
                    options=[],
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
        ],
        align="center",
        className="mb-2"
    ),
    html.Div(id=f"load-status-{type_page}", className="mb-3 text-muted"),
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
                                dcc.Loading(
                                    id=f"loading-data-{type_page}",
                                    type="default",
                                    color="#0d6efd",
                                    children=[
                                # Фильтры внутри «Данных»
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Label("Дубликат:", className="mb-0"),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id=f"dropdown-duplicate-{type_page}",
                                                options=[
                                                    {"label": "Все", "value": "all"},
                                                    {"label": "Только дубликаты", "value": "dup_only"},
                                                    {"label": "Без дубликатов", "value": "no_dup"},
                                                ],
                                                value="all",
                                                clearable=False,
                                                style={"minWidth": "180px"},
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            html.Label("Талон:", className="mb-0 ms-3"),
                                            width="auto",
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
                                                clearable=False,
                                                style={"minWidth": "160px"},
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            html.Label("Запись:", className="mb-0 ms-3"),
                                            width="auto",
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
                                                clearable=False,
                                                style={"minWidth": "160px"},
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                    align="center",
                                    className="mb-3 g-2",
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
                                                            page_action="native",
                                                            page_size=50,
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
                                            dcc.Loading(
                                                id=f"loading-detail-{type_page}",
                                                type="default",
                                                color="#0d6efd",
                                                children=[
                                            html.Div(
                                                id=f"patient-detail-label-{type_page}",
                                                className="mb-2 text-muted",
                                                children="Выберите пациента из списка слева",
                                            ),
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
                                            ),
                                            width=7
                                        ),
                                    ],
                                    className="g-3"
                                ),
                                    ],
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
    if not year:
        return [], []

    df = pd.read_sql(sql_dn_job_orgs(year), engine)
    opts = [{"label": org, "value": org} for org in df["org_prof_m"]]
    return opts, []


@app.callback(
    Output(f"store-{type_page}", "data"),
    Output(f"load-status-{type_page}", "children"),
    Output(f"last-updated-dn-{type_page}", "children"),
    Output(f"last-updated-talons-{type_page}", "children"),
    Output(f"last-updated-main-{type_page}", "children"),
    Output(f"tbl-patients-{type_page}", "selected_rows", allow_duplicate=True),
    Output(f"tbl-disp-{type_page}", "data", allow_duplicate=True),
    Output(f"tbl-tal-{type_page}", "data", allow_duplicate=True),
    Output(f"patient-detail-label-{type_page}", "children", allow_duplicate=True),
    Input(f"btn-get-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    prevent_initial_call=True,
)
def load_all(n_clicks, year):
    if not n_clicks or not year:
        raise exceptions.PreventUpdate

    disp_df = pd.read_sql(sql_dn_job_disp(year), con=engine)
    tal_df = pd.read_sql(sql_dn_job_tal(year), con=engine)
    store_data = build_store_payload(
        disp_df.to_dict("records"),
        tal_df.to_dict("records"),
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
    n_patients = len(store_data.get("patients", {}))
    load_msg = html.Span(
        f"Данные за {year} г. загружены: {n_patients} пациентов",
        className="text-success",
    )

    return (
        store_data,
        load_msg,
        last_dn,
        last_tal,
        main_str,
        [],
        [],
        [],
        "Выберите пациента из списка слева",
    )


@app.callback(
    Output(f"tbl-patients-{type_page}", "data"),
    Output(f"tbl-patients-{type_page}", "selected_rows", allow_duplicate=True),
    Input(f"store-{type_page}", "data"),
    Input(f"dropdown-org-{type_page}", "value"),
    Input(f"dropdown-duplicate-{type_page}", "value"),
    Input(f"dropdown-has-tal-{type_page}", "value"),
    Input(f"dropdown-has-disp-{type_page}", "value"),
    Input(f"status-selection-mode-{type_page}", "value"),
    Input(f"status-group-radio-{type_page}", "value"),
    Input(f"status-individual-dropdown-{type_page}", "value"),
    Input(f"status-filter-mode-{type_page}", "value"),
    prevent_initial_call=True,
)
def fill_patients(store_data, selected_orgs, dup_filter, has_tal_filter, has_disp_filter,
                  status_mode, sel_group, sel_ind, status_filter_mode):
    if not store_data or not store_data.get("patients"):
        return [], []

    status_list = get_status_list(status_filter_mode, status_mode, sel_group, sel_ind)
    out = []
    for patient in store_data["patients"].values():
        if not patient_passes_filters(
            patient,
            selected_orgs=selected_orgs,
            status_list=status_list,
            dup_filter=dup_filter,
            has_tal_filter=has_tal_filter,
            has_disp_filter=has_disp_filter,
        ):
            continue
        out.append({
            "enp": patient["enp"],
            "patient": patient["patient"],
            "birth_date": patient["birth_date"],
        })

    out.sort(key=lambda x: x["patient"] or "")
    return out, []


app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }
        return "Загрузка данных…";
    }
    """,
    Output(f"load-status-{type_page}", "children", allow_duplicate=True),
    Input(f"btn-get-{type_page}", "n_clicks"),
    prevent_initial_call=True,
)


app.clientside_callback(
    """
    function(selected_rows) {
        if (selected_rows && selected_rows.length) {
            return [[], [], "Загрузка карточки пациента…"];
        }
        return [[], [], "Выберите пациента из списка слева"];
    }
    """,
    Output(f"tbl-disp-{type_page}", "data", allow_duplicate=True),
    Output(f"tbl-tal-{type_page}", "data", allow_duplicate=True),
    Output(f"patient-detail-label-{type_page}", "children", allow_duplicate=True),
    Input(f"tbl-patients-{type_page}", "selected_rows"),
    prevent_initial_call=True,
)


@app.callback(
    Output(f"tbl-disp-{type_page}", "data"),
    Output(f"tbl-tal-{type_page}", "data"),
    Output(f"patient-detail-label-{type_page}", "children"),
    Input(f"tbl-patients-{type_page}", "selected_rows"),
    State(f"tbl-patients-{type_page}", "data"),
    State(f"store-{type_page}", "data"),
)
def update_details(selected_rows, patients, store_data):
    if not selected_rows or not patients or not store_data:
        return [], [], "Выберите пациента из списка слева"

    patient_row = patients[selected_rows[0]]
    selected_enp = patient_row["enp"]
    patient = store_data.get("patients", {}).get(selected_enp)
    if not patient:
        return [], [], "Пациент не найден в загруженных данных"

    name = patient_row.get("patient") or "—"
    label = html.Div([
        html.Strong("Выбран: ", className="text-primary"),
        name,
        html.Span(f" · ЕНП {selected_enp}", className="text-muted ms-1"),
    ])

    return patient.get("disp", []), patient.get("tal", []), label


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
def update_report(store_data, year, orgs,
                  status_filter_mode, status_mode, sel_group, sel_ind,
                  place_service, dup_report):
    if not store_data or not store_data.get("flat"):
        return [], []

    status_list = get_status_list(status_filter_mode, status_mode, sel_group, sel_ind)
    filtered = filter_flat_rows(
        store_data["flat"],
        year=year,
        orgs=orgs,
        status_list=status_list,
        place_service=place_service,
        dup_report=dup_report,
    )
    return build_report_table(filtered)


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
                    store_data):
    trig = callback_context.triggered[0]["prop_id"].split(".")[0]
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

    if not store_data or not store_data.get("flat") or not active_cell:
        return [], [], None

    status_list = get_status_list(status_filter_mode, status_mode, sel_group, sel_ind)
    filtered = filter_flat_rows(
        store_data["flat"],
        year=year,
        orgs=orgs,
        status_list=status_list,
        place_service=place_service,
        dup_report=dup_report,
    )
    columns, data = build_report_detail(filtered, active_cell)
    if not data:
        return [], [], None
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

    df = pd.read_sql(sql_dn_job_coverage(year), con=engine)
    if df.empty:
        return "0 чел.", "0 чел.", "0 чел.", "0 чел."

    row = df.iloc[0]
    return (
        f"{int(row['cov_count'])} чел.",
        f"{int(row['iszl_count'])} чел.",
        f"{int(row['work_count'])} чел.",
        f"{int(row['work_paid_count'])} чел.",
    )
