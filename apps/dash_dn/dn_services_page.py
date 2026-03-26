"""
Страница «Подбор услуг ДН» — данные из локального SQLite (sqlite_catalog).
"""
from __future__ import annotations

import os
from collections import defaultdict

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, dcc, html, dash_table
from dash.exceptions import PreventUpdate
from sqlalchemy import text

from apps.dash_dn.app import dash_dn_app as app
from apps.dash_dn.sqlite_catalog.queries import (
    DIAGNOSES_FOR_SPECIALTY_SQL,
    DIAGNOSES_OPTIONS_SQL,
    SERVICE_CODE_PRICE_BY_ID_SQL,
    SERVICES_CATALOG_LIST_WITH_PRICE_SQL,
    SERVICES_FOR_DIAGNOSES_FLAT_SQL,
    SPECIALTIES_FOR_DIAGNOSIS_SQL,
    SPECIALTIES_OPTIONS_SQL,
)
from apps.dash_dn.sqlite_catalog.db import get_engine

type_page = "dash-dn-services"


def _global_admin_password() -> str:
    return (os.environ.get("DASH_DN_GLOBAL_ADMIN_PASSWORD") or "").strip()


def _fetch_options(sql, params=None, catalog: str = "global"):
    eng = get_engine()
    p = dict(params or {})
    p["catalog"] = catalog
    with eng.connect() as connection:
        rows = connection.execute(sql, p).fetchall()
    return [{"label": row[1], "value": row[0]} for row in rows]


def _aggregate_services(rows):
    """Сводим плоские строки (услуга × диагноз) в строки таблицы."""
    by_key = defaultdict(lambda: {"codes": set(), "groups": set()})
    order = []
    for row in rows:
        m = row._mapping
        code = m["code"]
        name = m["name"]
        price = m["price"]
        key = (code, name, price)
        if key not in by_key:
            order.append(key)
        by_key[key]["codes"].add(m["diagnosis_code"])
        gt = m.get("group_title") or ""
        if gt:
            by_key[key]["groups"].add(gt)
    out = []
    for key in order:
        code, name, price = key
        v = by_key[key]
        out.append(
            {
                "Код услуги": code,
                "Наименование услуги": name,
                "Актуальная стоимость": price,
                "Диагнозы": ", ".join(sorted(v["codes"])),
                "Группы диагнозов": "; ".join(sorted(x for x in v["groups"] if x)),
            }
        )
    return out


def _fmt_rub(value: float | None) -> str:
    if value is None:
        return "нет цены"
    s = f"{float(value):,.2f}".replace(",", " ").replace(".", ",")
    return f"{s} ₽"


def _matrix_total_and_codes(
    main_diagnosis: str | None,
    specialty_name: str | None,
    additional_diagnoses,
    cat: str,
) -> tuple[float, set[str]]:
    """Та же логика суммы, что в сводке и таблице подбора (без учёта блока добавления)."""
    if not main_diagnosis or not specialty_name:
        return 0.0, set()
    diagnosis_codes = [main_diagnosis]
    if additional_diagnoses:
        diagnosis_codes.extend([c for c in additional_diagnoses if c and c != main_diagnosis])
    eng = get_engine()
    with eng.connect() as connection:
        rows = connection.execute(
            SERVICES_FOR_DIAGNOSES_FLAT_SQL,
            {
                "catalog": cat,
                "specialty_name": specialty_name,
                "diagnosis_codes": diagnosis_codes,
            },
        ).fetchall()
    if not rows:
        return 0.0, set()
    data = _aggregate_services(rows)
    total = sum(
        float(row.get("Актуальная стоимость") or 0)
        for row in data
        if row.get("Актуальная стоимость") is not None
    )
    codes = {row["Код услуги"] for row in data}
    return total, codes


_DROPDOWN_STYLE = {"fontSize": "0.95rem", "width": "100%"}


def _filter_row(label_text, control, mb_class="mb-3"):
    return dbc.Row(
        [
            dbc.Col(
                dbc.Label(
                    label_text,
                    className="fw-semibold small text-secondary mb-0",
                ),
                xs=12,
                md=4,
                lg=5,
                className="d-flex align-items-center text-md-end pe-md-3 pb-1 pb-md-0",
            ),
            dbc.Col(control, xs=12, md=8, lg=7, className="ps-md-0"),
        ],
        className=f"{mb_class} align-items-md-center gx-0",
    )


def layout_body():
    cat0 = "global"
    initial_diagnosis_options = _fetch_options(DIAGNOSES_OPTIONS_SQL, catalog=cat0)
    initial_specialty_options = _fetch_options(SPECIALTIES_OPTIONS_SQL, catalog=cat0)
    return html.Div(
        [
            dcc.Store(id=f"pick-refresh-{type_page}", data=0),
            html.H2("Подбор услуг ДН", className="fw-bold text-dark mb-3"),
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Span(
                            [html.I(className="bi bi-funnel me-2"), "Параметры подбора"],
                            className="fw-semibold",
                        ),
                        className="bg-white border-0 border-bottom py-3",
                    ),
                    dbc.CardBody(
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        _filter_row(
                                            "Основной диагноз",
                                            dcc.Dropdown(
                                                id=f"dropdown-main-diagnosis-{type_page}",
                                                options=initial_diagnosis_options,
                                                placeholder="Код диагноза из справочника…",
                                                clearable=True,
                                                className="dash-dn-dropdown",
                                                style=_DROPDOWN_STYLE,
                                            ),
                                        ),
                                        _filter_row(
                                            "Специальность",
                                            dcc.Dropdown(
                                                id=f"dropdown-specialty-{type_page}",
                                                options=initial_specialty_options,
                                                placeholder="Специальность врача…",
                                                clearable=True,
                                                className="dash-dn-dropdown",
                                                style=_DROPDOWN_STYLE,
                                            ),
                                        ),
                                        _filter_row(
                                            "Сопутствующие диагнозы",
                                            dcc.Dropdown(
                                                id=f"dropdown-additional-diagnoses-{type_page}",
                                                options=[],
                                                placeholder="После выбора специальности…",
                                                clearable=True,
                                                multi=True,
                                                className="dash-dn-dropdown",
                                                style=_DROPDOWN_STYLE,
                                            ),
                                            mb_class="mb-0",
                                        ),
                                    ],
                                    xs=12,
                                    lg=5,
                                    className="pe-lg-4",
                                    style={"overflow": "visible", "position": "relative", "zIndex": 2},
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Сводка выбора",
                                            className="fw-semibold small text-secondary d-block mb-2",
                                        ),
                                        html.Div(
                                            id=f"selection-summary-{type_page}",
                                            className="rounded-3 border bg-light p-3",
                                            style={"minHeight": "8rem"},
                                        ),
                                    ],
                                    xs=12,
                                    lg=7,
                                    className="ps-lg-4 mt-4 mt-lg-0",
                                ),
                            ],
                            className="g-0 align-items-lg-stretch",
                        ),
                        className="pt-2 pb-4",
                        style={"overflow": "visible"},
                    ),
                ],
                className="border-0 shadow rounded-4 mb-4",
                style={"overflow": "visible"},
            ),
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Span(
                            [
                                html.I(className="bi bi-table me-2"),
                                "Услуги при проведении диспансерного наблюдения",
                            ],
                            className="fw-semibold",
                        ),
                        className="bg-primary text-white border-0 py-3",
                    ),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id=f"result-table-{type_page}",
                            editable=False,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            export_format="xlsx",
                            export_headers="display",
                            # fixed_rows отключён: при columns=[] / data=[] до выбора диагноза — падение в async-table.js
                            style_table={
                                "overflowX": "auto",
                                "maxHeight": "420px",
                                "borderRadius": "0.375rem",
                            },
                            style_cell={
                                "minWidth": "80px",
                                "maxWidth": "200px",
                                "whiteSpace": "normal",
                                "fontFamily": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
                                "fontSize": "0.9rem",
                            },
                            style_cell_conditional=[
                                {
                                    "if": {"column_id": "Наименование услуги"},
                                    "minWidth": "420px",
                                    "maxWidth": "720px",
                                },
                            ],
                            style_header_conditional=[
                                {
                                    "if": {"column_id": "Наименование услуги"},
                                    "minWidth": "420px",
                                },
                            ],
                            style_header={
                                "fontWeight": "600",
                                "backgroundColor": "#f1f5f9",
                            },
                            page_size=20,
                        ),
                        className="p-0 pt-3",
                    ),
                ],
                className="border-0 shadow rounded-4 overflow-hidden mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Button(
                            [
                                html.I(
                                    className="bi bi-chevron-right me-2",
                                    id=f"pick-add-chevron-{type_page}",
                                ),
                                html.Span(
                                    [
                                        html.I(className="bi bi-plus-circle me-2"),
                                        "Добавить услугу в матрицу для выбранного диагноза и специальности",
                                    ],
                                    className="fw-semibold",
                                ),
                            ],
                            id=f"pick-add-toggle-{type_page}",
                            color="link",
                            className="text-decoration-none text-dark p-0 w-100 text-start d-flex align-items-center",
                        ),
                        className="bg-white border-0 border-bottom py-3",
                    ),
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                html.P(
                                    "Выберите одну или несколько услуг и группу диагнозов (входит основной диагноз). "
                                    "Куда сохраняются связи — по индикатору режима в шапке (рядом с паролем эталона).",
                                    className="text-muted small mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Услуги", className="small fw-semibold"),
                                                dcc.Dropdown(
                                                    id=f"pick-add-service-{type_page}",
                                                    options=[],
                                                    placeholder="Сначала выберите диагноз и специальность…",
                                                    clearable=True,
                                                    multi=True,
                                                    style=_DROPDOWN_STYLE,
                                                ),
                                            ],
                                            md=7,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Группа диагнозов", className="small fw-semibold"),
                                                dcc.Dropdown(
                                                    id=f"pick-add-group-{type_page}",
                                                    options=[],
                                                    placeholder="Группы для текущего диагноза…",
                                                    clearable=True,
                                                    style=_DROPDOWN_STYLE,
                                                ),
                                            ],
                                            md=5,
                                        ),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    id=f"pick-add-cost-preview-{type_page}",
                                    className="small border rounded-3 bg-light px-3 py-2 mb-3",
                                ),
                                dbc.Button(
                                    [html.I(className="bi bi-check2-circle me-1"), "Добавить и сохранить"],
                                    id=f"pick-add-btn-{type_page}",
                                    color="success",
                                    className="mb-2",
                                ),
                                html.Div(id=f"pick-add-msg-{type_page}", className="small"),
                            ],
                            className="pt-2 pb-3",
                        ),
                        id=f"pick-add-collapse-{type_page}",
                        is_open=False,
                    ),
                ],
                className="border-0 shadow rounded-4",
            ),
        ]
    )


@app.callback(
    Output(f"pick-add-collapse-{type_page}", "is_open"),
    Output(f"pick-add-chevron-{type_page}", "className"),
    Input(f"pick-add-toggle-{type_page}", "n_clicks"),
    State(f"pick-add-collapse-{type_page}", "is_open"),
    prevent_initial_call=True,
)
def toggle_pick_add_collapse(n_clicks, is_open):
    if not n_clicks:
        raise PreventUpdate
    new_open = not bool(is_open)
    chevron = "bi bi-chevron-down me-2" if new_open else "bi bi-chevron-right me-2"
    return new_open, chevron


@app.callback(
    Output("dash-dn-active-catalog", "data"),
    Input("dash-dn-pick-catalog", "value"),
)
def sync_pick_catalog_from_services(pick_value):
    return pick_value or "global"


@app.callback(
    Output("dash-dn-global-unlocked", "data"),
    Output("dash-dn-global-unlock-msg", "children"),
    Input("dash-dn-btn-global-unlock", "n_clicks"),
    Input("dash-dn-btn-global-lock", "n_clicks"),
    State("dash-dn-inp-global-pwd", "value"),
    prevent_initial_call=True,
)
def pick_global_unlock_lock(n_unlock, n_lock, pwd):
    ctx = callback_context
    tid = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    if tid == "dash-dn-btn-global-lock":
        return False, ""
    if tid != "dash-dn-btn-global-unlock":
        raise PreventUpdate
    expected = _global_admin_password()
    if not expected:
        return False, "Пароль для правки эталона не настроен."
    if (pwd or "").strip() == expected:
        return True, ""
    return False, "Неверный пароль."


@app.callback(
    Output("dash-dn-edit-mode-badge", "children"),
    Input("dash-dn-global-unlocked", "data"),
)
def render_edit_mode_badge(unlocked: bool | None):
    if bool(unlocked):
        return dbc.Badge(
            [
                html.I(className="bi bi-pencil-square me-1"),
                "Правка эталона: запись в общий справочник и локальный слой",
            ],
            color="success",
            className="px-2 py-2 text-wrap text-start",
            style={"maxWidth": "280px", "whiteSpace": "normal", "lineHeight": "1.25"},
            title="Режим администратора эталона включён",
        )
    return dbc.Badge(
        [
            html.I(className="bi bi-person-lock me-1"),
            "Только локальный слой — эталон не меняется",
        ],
        color="light",
        text_color="dark",
        className="px-2 py-2 text-wrap text-start border",
        style={"maxWidth": "280px", "whiteSpace": "normal", "lineHeight": "1.25"},
        title="Введите пароль эталона в шапке и нажмите «Включить»",
    )


@app.callback(
    Output(f"dropdown-main-diagnosis-{type_page}", "options"),
    Output(f"dropdown-main-diagnosis-{type_page}", "value"),
    Output(f"dropdown-specialty-{type_page}", "options"),
    Output(f"dropdown-specialty-{type_page}", "value"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input("dash-dn-active-catalog", "data"),
)
def sync_main_diagnosis_and_specialty(main_diagnosis, specialty_name, catalog):
    ctx = callback_context
    cat = catalog or "global"
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    diagnosis_options = _fetch_options(DIAGNOSES_OPTIONS_SQL, catalog=cat)
    specialty_options = _fetch_options(SPECIALTIES_OPTIONS_SQL, catalog=cat)

    if triggered == "dash-dn-active-catalog":
        return diagnosis_options, None, specialty_options, None

    if main_diagnosis and specialty_name:
        diagnosis_options = _fetch_options(
            DIAGNOSES_FOR_SPECIALTY_SQL,
            {"specialty_name": specialty_name},
            catalog=cat,
        )
        specialty_options = _fetch_options(
            SPECIALTIES_FOR_DIAGNOSIS_SQL,
            {"diagnosis_code": main_diagnosis},
            catalog=cat,
        )
        diagnosis_values = {opt["value"] for opt in diagnosis_options}
        specialty_values = {opt["value"] for opt in specialty_options}
        if main_diagnosis not in diagnosis_values:
            main_diagnosis = None
        if specialty_name not in specialty_values:
            specialty_name = None
        return diagnosis_options, main_diagnosis, specialty_options, specialty_name

    if triggered == f"dropdown-specialty-{type_page}" and specialty_name:
        diagnosis_options = _fetch_options(
            DIAGNOSES_FOR_SPECIALTY_SQL,
            {"specialty_name": specialty_name},
            catalog=cat,
        )
        diagnosis_values = {opt["value"] for opt in diagnosis_options}
        if main_diagnosis not in diagnosis_values:
            main_diagnosis = None
        return diagnosis_options, main_diagnosis, specialty_options, specialty_name

    if triggered == f"dropdown-main-diagnosis-{type_page}" and main_diagnosis:
        specialty_options = _fetch_options(
            SPECIALTIES_FOR_DIAGNOSIS_SQL,
            {"diagnosis_code": main_diagnosis},
            catalog=cat,
        )
        specialty_values = {opt["value"] for opt in specialty_options}
        if specialty_name not in specialty_values:
            specialty_name = None
        return diagnosis_options, main_diagnosis, specialty_options, specialty_name

    return diagnosis_options, main_diagnosis, specialty_options, specialty_name


@app.callback(
    Output(f"pick-add-service-{type_page}", "options"),
    Output(f"pick-add-group-{type_page}", "options"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input("dash-dn-active-catalog", "data"),
)
def pick_populate_add_dropdowns(main_diagnosis, specialty_name, catalog):
    """Список услуг и групп для текущего справочника и диагноза."""
    cat = catalog or "global"
    if not main_diagnosis:
        return [], []
    eng = get_engine()
    svc_opts: list[dict] = []
    grp_opts: list[dict] = []
    with eng.connect() as conn:
        srows = conn.execute(
            SERVICES_CATALOG_LIST_WITH_PRICE_SQL,
            {"catalog": cat},
        ).mappings().all()
        svc_opts = []
        for r in srows:
            nm = (r["name"] or "")[:55]
            price_bit = _fmt_rub(r["price"]) if r["price"] is not None else "нет цены"
            svc_opts.append(
                {"label": f"{r['code']} — {nm} — {price_bit}", "value": r["id"]}
            )
        grows = conn.execute(
            text(
                """
                SELECT DISTINCT g.id, g.code, g.title
                FROM dn_diagnosis_group g
                JOIN dn_diagnosis_group_membership m ON m.group_id = g.id AND m.catalog = :c
                JOIN dn_diagnosis d ON d.id = m.diagnosis_id AND d.catalog = :c
                WHERE g.catalog = :c AND d.code = :diag AND m.is_active = 1
                ORDER BY g.sort_order, g.code
                """
            ),
            {"c": cat, "diag": main_diagnosis},
        ).mappings().all()
        grp_opts = [{"label": f"{r['code']} — {str(r['title'] or '')[:40]}", "value": r["id"]} for r in grows]
    return svc_opts, grp_opts


@app.callback(
    Output(f"pick-add-cost-preview-{type_page}", "children"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input(f"dropdown-additional-diagnoses-{type_page}", "value"),
    Input("dash-dn-active-catalog", "data"),
    Input(f"pick-refresh-{type_page}", "data"),
    Input(f"pick-add-service-{type_page}", "value"),
)
def pick_add_cost_preview(
    main_diagnosis,
    specialty_name,
    additional_diagnoses,
    catalog,
    _pick_refresh,
    service_ids,
):
    """Суммы только в блоке добавления; верхняя сводка не зависит от выбора услуги здесь."""
    cat = catalog or "global"
    if not main_diagnosis or not specialty_name:
        return html.Div(
            "После выбора диагноза и специальности здесь будет сумма по текущему подбору и просмотр итого при добавлении услуг.",
            className="text-muted mb-0 small",
        )

    base_total, codes = _matrix_total_and_codes(
        main_diagnosis, specialty_name, additional_diagnoses, cat
    )

    parts = [
        html.Div(
            [
                html.Span("Сумма по текущему подбору (как в таблице выше): ", className="text-secondary"),
                html.Strong(_fmt_rub(base_total)),
            ],
            className="mb-2",
        ),
    ]

    if service_ids is None:
        id_list: list = []
    elif isinstance(service_ids, list):
        id_list = list(service_ids)
    else:
        id_list = [service_ids]

    if not id_list:
        parts.append(
            html.Div(
                "Выберите одну или несколько услуг — появятся стоимости и просмотр итого.",
                className="text-muted mb-0 small",
            )
        )
        return html.Div(parts)

    eng = get_engine()
    rows_info: list[tuple[int, str | None, float | None, str | None]] = []
    sum_sel = 0.0
    any_no_price = False
    with eng.connect() as conn:
        for sid_raw in id_list:
            try:
                sid = int(sid_raw)
            except (TypeError, ValueError):
                rows_info.append((0, None, None, "некорректный id"))
                continue
            row = conn.execute(
                SERVICE_CODE_PRICE_BY_ID_SQL,
                {"service_id": sid, "catalog": cat},
            ).mappings().first()
            if not row:
                rows_info.append((sid, None, None, "не найдена"))
                continue
            code = row["code"]
            price = row["price"]
            pr = float(price) if price is not None else None
            if pr is not None:
                sum_sel += pr
            else:
                any_no_price = True
            rows_info.append((sid, str(code) if code is not None else None, pr, None))

    if not rows_info:
        return html.Div(parts + [html.Div("Нет данных по услугам.", className="text-danger small mb-0")])

    line_blocks = []
    for sid, code, pr, err in rows_info:
        if err:
            line_blocks.append(
                html.Div(
                    f"Услуга id={sid}: {err}." if sid else err,
                    className="text-warning small",
                )
            )
            continue
        if not code:
            continue
        in_m = code in codes
        line_blocks.append(
            html.Div(
                [
                    html.Span(f"{code}: ", className="text-secondary"),
                    html.Strong(_fmt_rub(pr)),
                    html.Span(" — уже в подборе" if in_m else "", className="text-muted ms-1 small"),
                ],
                className="mb-1",
            )
        )

    parts.append(
        html.Div(
            [
                html.Span("Сумма по выбранным услугам: ", className="text-secondary"),
                html.Strong(_fmt_rub(sum_sel)),
            ],
            className="mb-2",
        )
    )
    parts.append(html.Div(line_blocks, className="mb-2 small"))

    resolved_codes = [(c, pr) for _sid, c, pr, err in rows_info if not err and c]
    if not resolved_codes:
        return html.Div(parts)

    new_add = sum(
        float(pr) if pr is not None else 0.0 for c, pr in resolved_codes if c not in codes
    )
    if new_add == 0.0 and all(c in codes for c, _ in resolved_codes):
        parts.append(
            html.Div(
                "Все выбранные услуги уже учтены в подборе. После сохранения связей сумма по позициям не изменится.",
                className="text-muted small mb-0",
            )
        )
        return html.Div(parts)

    preview_total = base_total + new_add
    parts.append(
        html.Div(
            [
                html.Span("Просмотр итого после добавления новых позиций (только здесь): ", className="text-secondary"),
                html.Strong(_fmt_rub(preview_total), className="text-primary"),
            ],
            className="mb-0",
        )
    )
    if any_no_price:
        parts.append(
            html.Div(
                "Для части услуг нет актуальной цены в периоде; к сумме добавлено 0 ₽.",
                className="text-warning small mt-2 mb-0",
            )
        )
    return html.Div(parts)


@app.callback(
    Output(f"pick-add-msg-{type_page}", "children"),
    Output(f"pick-refresh-{type_page}", "data"),
    Input(f"pick-add-btn-{type_page}", "n_clicks"),
    State(f"dropdown-main-diagnosis-{type_page}", "value"),
    State(f"dropdown-specialty-{type_page}", "value"),
    State(f"pick-add-service-{type_page}", "value"),
    State(f"pick-add-group-{type_page}", "value"),
    State("dash-dn-active-catalog", "data"),
    State("dash-dn-global-unlocked", "data"),
    State(f"pick-refresh-{type_page}", "data"),
    prevent_initial_call=True,
)
def pick_add_requirement(
    n_clicks,
    main_diagnosis,
    specialty_name,
    service_ids,
    group_id,
    active_catalog,
    global_unlocked_state,
    refresh_val,
):
    if not n_clicks:
        raise PreventUpdate
    if not main_diagnosis or not specialty_name:
        return dbc.Alert("Выберите основной диагноз и специальность.", color="warning", className="py-2 mb-0"), refresh_val

    if service_ids is None:
        id_list: list = []
    elif isinstance(service_ids, list):
        id_list = list(service_ids)
    else:
        id_list = [service_ids]

    seen: set[int] = set()
    id_list_unique: list[int] = []
    for raw in id_list:
        try:
            sid = int(raw)
        except (TypeError, ValueError):
            continue
        if sid not in seen:
            seen.add(sid)
            id_list_unique.append(sid)

    if not id_list_unique:
        return dbc.Alert("Выберите хотя бы одну услугу.", color="warning", className="py-2 mb-0"), refresh_val
    if not group_id:
        return dbc.Alert("Выберите группу диагнозов.", color="warning", className="py-2 mb-0"), refresh_val

    unlocked = bool(global_unlocked_state)
    targets: list[str] = ["global", "user"] if unlocked else ["user"]

    source_cat = active_catalog or "global"

    eng = get_engine()

    def _code(conn, sql, params) -> str | None:
        r = conn.execute(text(sql), params).scalar_one_or_none()
        return str(r) if r is not None else None

    def _lookup_ids(conn, cat: str, svc_code: str, grp_code: str, spec_name: str) -> tuple[int | None, int | None, int | None, str | None]:
        sid = conn.execute(
            text("SELECT id FROM dn_service WHERE catalog = :c AND code = :code"),
            {"c": cat, "code": svc_code},
        ).scalar_one_or_none()
        if sid is None:
            return None, None, None, f"услугой {svc_code}"
        gid = conn.execute(
            text("SELECT id FROM dn_diagnosis_group WHERE catalog = :c AND code = :code"),
            {"c": cat, "code": grp_code},
        ).scalar_one_or_none()
        if gid is None:
            return None, None, None, f"группой {grp_code}"
        spid = conn.execute(
            text("SELECT id FROM dn_specialty WHERE catalog = :c AND name = :name"),
            {"c": cat, "name": spec_name},
        ).scalar_one_or_none()
        if spid is None:
            return None, None, None, f"специальностью «{spec_name}»"
        return int(sid), int(gid), int(spid), None

    try:
        with eng.connect() as conn:
            grp_code = _code(
                conn,
                "SELECT code FROM dn_diagnosis_group WHERE id = :id AND catalog = :c",
                {"id": int(group_id), "c": source_cat},
            )
            if not grp_code:
                return (
                    dbc.Alert("Группа не найдена в справочнике.", color="danger", className="py-2 mb-0"),
                    refresh_val,
                )

            resolved: list[tuple[str, int, int, int]] = []
            for service_id in id_list_unique:
                svc_code = _code(
                    conn,
                    "SELECT code FROM dn_service WHERE id = :id AND catalog = :c",
                    {"id": int(service_id), "c": source_cat},
                )
                if not svc_code:
                    return (
                        dbc.Alert(f"Услуга id={service_id} не найдена в справочнике.", color="danger", className="py-2 mb-0"),
                        refresh_val,
                    )
                for cat in targets:
                    sid, gid, spid, err = _lookup_ids(conn, cat, svc_code, grp_code, specialty_name)
                    if err:
                        return (
                            dbc.Alert(
                                f"В каталоге «{cat}» нет {err}. Скопируйте global→user или добавьте сущности в справочнике.",
                                color="danger",
                                className="py-2 mb-0",
                            ),
                            refresh_val,
                        )
                    resolved.append((cat, sid, gid, spid))

        with eng.begin() as conn:
            for cat, sid, gid, spid in resolved:
                conn.execute(
                    text(
                        """
                        INSERT INTO dn_service_requirement (catalog, service_id, group_id, specialty_id, is_required)
                        VALUES (:c, :sid, :gid, :spid, 1)
                        ON CONFLICT(catalog, service_id, group_id, specialty_id) DO NOTHING
                        """
                    ),
                    {"c": cat, "sid": sid, "gid": gid, "spid": spid},
                )

        layer_hint = "эталон и локальный слой" if unlocked else "только локальный слой"
        msg = dbc.Alert(
            f"Сохранено связей: {len(resolved)} ({layer_hint}). Таблица ниже обновлена.",
            color="success",
            className="py-2 mb-0",
        )
        return msg, (int(refresh_val or 0) + 1)
    except Exception as e:
        return dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0"), refresh_val


@app.callback(
    Output(f"dropdown-additional-diagnoses-{type_page}", "options"),
    Output(f"dropdown-additional-diagnoses-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input("dash-dn-active-catalog", "data"),
    State(f"dropdown-main-diagnosis-{type_page}", "value"),
)
def update_additional_diagnoses(specialty_name, catalog, main_diagnosis):
    if not specialty_name:
        return [], []
    cat = catalog or "global"
    options = _fetch_options(
        DIAGNOSES_FOR_SPECIALTY_SQL,
        {"specialty_name": specialty_name},
        catalog=cat,
    )
    filtered_options = [opt for opt in options if opt["value"] != main_diagnosis]
    return filtered_options, []


@app.callback(
    Output(f"selection-summary-{type_page}", "children"),
    Output(f"result-table-{type_page}", "columns"),
    Output(f"result-table-{type_page}", "data"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    Input(f"dropdown-additional-diagnoses-{type_page}", "value"),
    Input("dash-dn-active-catalog", "data"),
    Input(f"pick-refresh-{type_page}", "data"),
)
def show_dn_services(main_diagnosis, specialty_name, additional_diagnoses, catalog, _pick_refresh):
    cat = catalog or "global"
    if not main_diagnosis:
        return dbc.Alert("Выберите основной диагноз.", color="secondary", className="mb-0"), [], []
    if not specialty_name:
        return dbc.Alert(
            "Выберите специальность для выбранного диагноза.",
            color="info",
            className="mb-0",
        ), [], []

    diagnosis_codes = [main_diagnosis]
    if additional_diagnoses:
        diagnosis_codes.extend([code for code in additional_diagnoses if code and code != main_diagnosis])

    eng = get_engine()
    with eng.connect() as connection:
        rows = connection.execute(
            SERVICES_FOR_DIAGNOSES_FLAT_SQL,
            {
                "catalog": cat,
                "specialty_name": specialty_name,
                "diagnosis_codes": diagnosis_codes,
            },
        ).fetchall()

    summary_parts = [
        dbc.Row(
            [
                dbc.Col([html.Strong("Основной диагноз: ", className="text-secondary"), main_diagnosis], md=4),
                dbc.Col([html.Strong("Специальность: ", className="text-secondary"), specialty_name], md=4),
            ],
            className="g-2 mb-2",
        )
    ]
    if len(diagnosis_codes) > 1:
        summary_parts.append(
            html.Div(
                [html.Strong("Сопутствующие: ", className="text-secondary"), ", ".join(diagnosis_codes[1:])],
                className="small",
            )
        )

    if not rows:
        summary_parts.append(
            dbc.Alert(
                "Для выбранной комбинации диагнозов и специальности услуги не найдены.",
                color="warning",
                className="mt-2 mb-0",
            )
        )
        return html.Div(summary_parts), [], []

    data = _aggregate_services(rows)
    columns = [{"name": k, "id": k} for k in data[0].keys()]
    total_cost = sum(
        float(row.get("Актуальная стоимость") or 0)
        for row in data
        if row.get("Актуальная стоимость") is not None
    )

    summary_parts.extend(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Badge(f"Услуг: {len(data)}", color="success", className="me-2"),
                        width="auto",
                    ),
                    dbc.Col(
                        html.Span(
                            [
                                html.Strong("Итого: ", className="text-secondary"),
                                f"{total_cost:,.2f}".replace(",", " ").replace(".", ","),
                                " ₽",
                            ],
                            className="fw-semibold",
                        ),
                        width="auto",
                    ),
                ],
                className="align-items-center mt-2 g-2",
            ),
        ]
    )

    return html.Div(summary_parts), columns, data
