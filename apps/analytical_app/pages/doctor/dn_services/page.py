"""Подбор услуг ДН по матрице (apps.dn_matrix)."""
from __future__ import annotations

from dash import Input, Output, State, callback_context, dash_table, dcc, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.elements import card_table
from apps.dn_matrix.runtime import ensure_django

ensure_django()

from apps.dn_matrix.services.workspace import (
    default_edition,
    diagnosis_options,
    directory_diagnoses,
    directory_diagnosis_specialties,
    directory_group_memberships,
    directory_groups,
    directory_prices,
    directory_services,
    directory_specialties,
    edition_options,
    get_edition,
    pick_services,
    specialty_options,
)

type_page = "doctor-dn-services"

DIR_TABLES = [
    {"label": "Специальности", "value": "specialties"},
    {"label": "Диагнозы", "value": "diagnoses"},
    {"label": "Диагноз — специальность", "value": "diag_spec"},
    {"label": "Группы диагнозов", "value": "groups"},
    {"label": "Членства в группах", "value": "memberships"},
    {"label": "Услуги", "value": "services"},
    {"label": "Цены", "value": "prices"},
]


def _empty_table():
    return [], []


def _to_table(rows: list[dict]):
    if not rows:
        return [], []
    columns = [{"name": col, "id": col} for col in rows[0].keys()]
    return columns, rows


PICK_COL_STYLE = [
    {"if": {"column_id": "Код"}, "minWidth": "108px", "maxWidth": "128px", "width": "112px"},
    {"if": {"column_id": "Название"}, "minWidth": "280px", "width": "38%"},
    {"if": {"column_id": "Подбор"}, "minWidth": "118px", "maxWidth": "150px", "width": "128px"},
    {"if": {"column_id": "Пол"}, "minWidth": "44px", "maxWidth": "56px", "width": "50px", "textAlign": "center"},
    {
        "if": {"column_id": "Обязательность"},
        "minWidth": "88px",
        "maxWidth": "120px",
        "width": "108px",
    },
    {"if": {"column_id": "Цена за ед."}, "minWidth": "78px", "maxWidth": "96px", "width": "88px", "textAlign": "right"},
    {"if": {"column_id": "Кол-во"}, "minWidth": "52px", "maxWidth": "64px", "width": "58px", "textAlign": "right"},
    {"if": {"column_id": "Сумма"}, "minWidth": "78px", "maxWidth": "100px", "width": "88px", "textAlign": "right"},
]


def _field(label, control, extra=None):
    children = [html.Label(label, className="small text-muted mb-1 d-block"), control]
    if extra is not None:
        children.append(extra)
    return html.Div(children, className="mb-2")


def _visit_options(max_visits: int) -> list[dict]:
    cap = min(max(int(max_visits or 3), 1), 3)
    labels = {1: "1 явка", 2: "2 явки", 3: "3 явки"}
    return [{"label": labels[n], "value": n} for n in range(1, cap + 1)]


_initial_editions = edition_options()
_initial_edition = default_edition()
_initial_edition_id = _initial_edition.id if _initial_edition else None
_initial_specs = specialty_options(_initial_edition) if _initial_edition else []
_initial_diags = diagnosis_options(_initial_edition) if _initial_edition else []
_initial_visits = _visit_options(_initial_edition.max_doctor_visits if _initial_edition else 3)

pick_tab = dbc.Row(
    [
        dbc.Col(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div("Фильтры подбора", className="fw-semibold mb-2"),
                            _field(
                                "Редакция матрицы",
                                dcc.Dropdown(
                                    id=f"dropdown-edition-{type_page}",
                                    options=_initial_editions,
                                    value=_initial_edition_id,
                                    clearable=False,
                                    searchable=True,
                                ),
                            ),
                            _field(
                                "Специальность",
                                dcc.Dropdown(
                                    id=f"dropdown-specialty-{type_page}",
                                    options=_initial_specs,
                                    placeholder="Специальность...",
                                    clearable=True,
                                    searchable=True,
                                ),
                            ),
                            _field(
                                "Основной диагноз (МКБ)",
                                dcc.Dropdown(
                                    id=f"dropdown-main-diagnosis-{type_page}",
                                    options=_initial_diags,
                                    placeholder="Код МКБ...",
                                    clearable=True,
                                    searchable=True,
                                ),
                            ),
                            _field(
                                "Сопутствующие диагнозы",
                                dcc.Dropdown(
                                    id=f"dropdown-additional-diagnoses-{type_page}",
                                    options=[],
                                    placeholder="Необязательно",
                                    clearable=True,
                                    searchable=True,
                                    multi=True,
                                ),
                            ),
                            _field(
                                "Число явок к врачу",
                                dcc.Dropdown(
                                    id=f"dropdown-visits-{type_page}",
                                    options=_initial_visits,
                                    value=1,
                                    clearable=False,
                                ),
                                html.Small(id=f"visits-hint-{type_page}", className="text-muted"),
                            ),
                            dbc.Button(
                                "Подобрать услуги",
                                id=f"btn-pick-{type_page}",
                                color="primary",
                                className="w-100 mt-1",
                            ),
                        ],
                        className="py-3 px-3",
                    ),
                    className="mb-3",
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div("Итого подбора", className="fw-semibold mb-2"),
                            html.Div(
                                id=f"pick-totals-{type_page}",
                                children=html.Span("Нажмите «Подобрать услуги».", className="text-muted small"),
                            ),
                        ],
                        className="py-3 px-3",
                    )
                ),
            ],
            xs=12,
            lg=3,
            className="mb-3",
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Подобранные услуги", className="fw-semibold mb-2"),
                        html.Div(id=f"selection-summary-{type_page}"),
                        dash_table.DataTable(
                            id=f"result-table-{type_page}",
                            page_size=20,
                            sort_action="native",
                            filter_action="native",
                            export_format="xlsx",
                            export_headers="display",
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "fontSize": "12px",
                                "padding": "4px 8px",
                                "whiteSpace": "normal",
                                "textAlign": "left",
                            },
                            style_header={"fontWeight": "600", "whiteSpace": "normal"},
                            style_cell_conditional=PICK_COL_STYLE,
                        ),
                    ],
                    className="py-3 px-3",
                )
            ),
            xs=12,
            lg=9,
        ),
    ],
    className="g-3",
)

dir_tab = html.Div(
    [
        html.P(
            "Справочники выбранной редакции матрицы (только просмотр). Правки — в Django admin.",
            className="text-muted",
        ),
        dcc.Dropdown(
            id=f"dropdown-dir-table-{type_page}",
            options=DIR_TABLES,
            value="specialties",
            clearable=False,
            className="mb-3",
        ),
        card_table(
            f"dir-table-{type_page}",
            "Справочник",
            page_size=25,
        ),
    ]
)

doctor_dn_services = html.Div(
    [
        html.H5("Подбор услуг ДН", className="mb-1"),
        html.P(
            "Подбор услуг диспансерного наблюдения по диагнозу, специальности и явкам.",
            className="text-muted mb-3",
        ),
        dbc.Tabs(
            [
                dbc.Tab(pick_tab, label="Подбор", tab_id="tab-pick"),
                dbc.Tab(dir_tab, label="Справочники", tab_id="tab-dir"),
            ],
            active_tab="tab-pick",
        ),
    ],
    style={"padding": "0rem"},
)


@app.callback(
    Output(f"dropdown-specialty-{type_page}", "options"),
    Output(f"dropdown-specialty-{type_page}", "value"),
    Output(f"dropdown-main-diagnosis-{type_page}", "options"),
    Output(f"dropdown-main-diagnosis-{type_page}", "value"),
    Output(f"dropdown-visits-{type_page}", "options"),
    Output(f"dropdown-visits-{type_page}", "value"),
    Output(f"visits-hint-{type_page}", "children"),
    Input(f"dropdown-edition-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
    State(f"dropdown-visits-{type_page}", "value"),
)
def sync_filters(edition_id, specialty_id, mkb, current_visits):
    edition = get_edition(edition_id)
    if not edition:
        return [], None, [], None, _visit_options(3), 1, "Нет загруженных редакций матрицы."

    spec_opts = specialty_options(edition)
    spec_ids = {o["value"] for o in spec_opts}
    if specialty_id not in spec_ids:
        specialty_id = None

    diag_opts = diagnosis_options(edition, specialty_id)
    diag_codes = {o["value"] for o in diag_opts}
    if mkb not in diag_codes:
        mkb = None

    visit_opts = _visit_options(edition.max_doctor_visits)
    visit_values = {o["value"] for o in visit_opts}
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    if triggered == f"dropdown-edition-{type_page}" or current_visits not in visit_values:
        visits = 1 if 1 in visit_values else visit_opts[0]["value"]
    else:
        visits = current_visits
    hint = f"Максимум {edition.max_doctor_visits} явок для этой редакции."
    return spec_opts, specialty_id, diag_opts, mkb, visit_opts, visits, hint


@app.callback(
    Output(f"dropdown-additional-diagnoses-{type_page}", "options"),
    Output(f"dropdown-additional-diagnoses-{type_page}", "value"),
    Input(f"dropdown-edition-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
)
def update_additional(edition_id, specialty_id, mkb):
    edition = get_edition(edition_id)
    if not edition or not specialty_id:
        return [], []
    options = [o for o in diagnosis_options(edition, specialty_id) if o["value"] != mkb]
    return options, []


@app.callback(
    Output(f"selection-summary-{type_page}", "children"),
    Output(f"pick-totals-{type_page}", "children"),
    Output(f"result-table-{type_page}", "columns"),
    Output(f"result-table-{type_page}", "data"),
    Input(f"btn-pick-{type_page}", "n_clicks"),
    State(f"dropdown-edition-{type_page}", "value"),
    State(f"dropdown-specialty-{type_page}", "value"),
    State(f"dropdown-main-diagnosis-{type_page}", "value"),
    State(f"dropdown-additional-diagnoses-{type_page}", "value"),
    State(f"dropdown-visits-{type_page}", "value"),
    prevent_initial_call=True,
)
def run_pick(n_clicks, edition_id, specialty_id, mkb, additional, visits):
    if not n_clicks:
        raise PreventUpdate
    empty_totals = html.Span("Нет данных.", className="text-muted small")
    edition = get_edition(edition_id)
    if not edition:
        return dbc.Alert("Выберите редакцию матрицы.", color="warning"), empty_totals, [], []
    if not specialty_id:
        return dbc.Alert("Выберите специальность.", color="warning"), empty_totals, [], []
    if not mkb:
        return dbc.Alert("Выберите основной диагноз.", color="warning"), empty_totals, [], []

    spec = edition.specialties.filter(pk=specialty_id).first()
    result = pick_services(
        edition,
        specialty_id=int(specialty_id),
        mkb=str(mkb),
        secondary_mkb_list=list(additional or []),
        visits=int(visits or 1),
    )
    spec_title = spec.title if spec else str(specialty_id)
    extra = ", ".join(additional or [])

    visit_lines = [
        html.Div([html.Strong("Позиций: "), str(result["count"])]),
        html.Div(
            [
                html.Strong(f"Сумма при выбранных явках ({result['visits']}): "),
                f"{result['total']} ₽",
            ]
        ),
    ]
    visit_labels = {1: "1 явка", 2: "2 явки", 3: "3 явки"}
    for n, amt in (result.get("sums") or {}).items():
        visit_lines.append(
            html.Div([html.Span(f"{visit_labels.get(n, n)}: ", className="text-muted"), f"{amt} ₽"])
        )
    if result["missing_prices"]:
        visit_lines.append(html.Small("Есть услуги без цены.", className="text-warning"))

    banner = dbc.Alert(
        "Обязательность в пакете матрицы не хранится — колонка показывает «не задано».",
        color="info",
        className="py-2 px-3 mb-2",
    )
    meta = [
        html.Span([html.Strong("Редакция: "), edition.title], className="me-3"),
        html.Span([html.Strong("Специальность: "), spec_title], className="me-3"),
        html.Span([html.Strong("МКБ: "), mkb], className="me-3"),
    ]
    if extra:
        meta.append(html.Span([html.Strong("Сопутствующие: "), extra], className="me-3"))
    meta.append(html.Span([html.Strong("Явок: "), str(result["visits"])]))

    if not result["rows"]:
        if result["diagnosis_id"] is None:
            msg = "Диагноз не найден в выбранной редакции."
        else:
            msg = "Для выбранной комбинации услуги не найдены."
        return html.Div([banner, html.Div(meta, className="small text-muted mb-2"), html.Div(msg)]), visit_lines, [], []

    summary = html.Div(
        [banner, html.Div(meta, className="small text-muted mb-2")],
    )
    cols, data = _to_table(result["rows"])
    return summary, visit_lines, cols, data


@app.callback(
    Output(f"dir-table-{type_page}", "columns"),
    Output(f"dir-table-{type_page}", "data"),
    Input(f"dropdown-edition-{type_page}", "value"),
    Input(f"dropdown-dir-table-{type_page}", "value"),
)
def show_directory(edition_id, table_key):
    edition = get_edition(edition_id)
    if not edition:
        return _empty_table()
    loaders = {
        "specialties": directory_specialties,
        "diagnoses": directory_diagnoses,
        "diag_spec": directory_diagnosis_specialties,
        "groups": directory_groups,
        "memberships": directory_group_memberships,
        "services": directory_services,
        "prices": directory_prices,
    }
    loader = loaders.get(table_key or "specialties", directory_specialties)
    return _to_table(loader(edition))
