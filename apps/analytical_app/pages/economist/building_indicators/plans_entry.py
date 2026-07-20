"""Вкладка «Ввод планов»: каталог индикаторов + форма корпусов (объёмы+финансы, ТФОМС/внутренний)."""
from __future__ import annotations

import json

import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback_context, dash_table, dcc, html, no_update
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import filter_years
from apps.analytical_app.pages.economist.building_indicators.query import (
    PLAN_KIND_OPTIONS,
    add_building_to_plan,
    list_plan_catalog,
    load_indicator_plan_form,
    save_indicator_plan_form,
)

type_page_plans = "econ-building-indicators-plans"
PLAN_EDIT_EXISTING = "bie-edit-existing"
PLAN_FORM_TABLE = "bie-form-table"


def _form_month_columns():
    cols = [
        {"name": "Строка", "id": "row_label", "editable": False},
        {"name": "Метрика", "id": "metric_label", "editable": False},
        {"name": "building_id", "id": "building_id", "editable": False},
        {"name": "metric", "id": "metric", "editable": False},
    ]
    for m in range(1, 13):
        cols.append({"name": str(m), "id": str(m), "editable": True, "type": "numeric"})
    cols.append({"name": "Итого", "id": "total", "editable": False, "type": "numeric"})
    return cols


def _form_rows_from_payload(payload: dict) -> list[dict]:
    rows: list[dict] = []

    def _add(row_label: str, building_id, metric: str, values: dict):
        is_amt = metric == "amount"
        data = {
            "row_label": row_label,
            "metric_label": "Финансы" if is_amt else "Объёмы",
            "building_id": building_id,
            "metric": metric,
        }
        total = 0.0 if is_amt else 0
        for m in range(1, 13):
            key = str(m)
            raw = values.get(key, 0)
            if is_amt:
                val = float(raw or 0)
                data[key] = val
                total += val
            else:
                val = int(float(raw or 0))
                data[key] = val
                total += val
        data["total"] = round(total, 2) if is_amt else int(total)
        rows.append(data)

    _add("План МО", "org", "quantity", payload.get("org_quantity") or {})
    _add("План МО", "org", "amount", payload.get("org_amount") or {})
    for b in payload.get("buildings") or []:
        name = b.get("building_name") or str(b.get("building_id"))
        bid = int(b["building_id"])
        _add(name, bid, "quantity", b.get("quantity") or {})
        _add(name, bid, "amount", b.get("amount") or {})
    return rows


def _payload_from_form_rows(rows: list[dict]) -> tuple[dict, dict, list[dict]]:
    org_quantity = {str(m): 0 for m in range(1, 13)}
    org_amount = {str(m): 0.0 for m in range(1, 13)}
    by_building: dict[int, dict] = {}

    for row in rows or []:
        bid = row.get("building_id")
        metric = row.get("metric")
        if metric not in ("quantity", "amount"):
            continue
        month_map = {}
        for m in range(1, 13):
            key = str(m)
            raw = row.get(key, 0)
            if metric == "amount":
                try:
                    month_map[key] = float(raw or 0)
                except (TypeError, ValueError):
                    month_map[key] = 0.0
            else:
                try:
                    month_map[key] = int(float(raw or 0))
                except (TypeError, ValueError):
                    month_map[key] = 0

        if bid == "org" or str(bid) == "org":
            if metric == "quantity":
                org_quantity = month_map
            else:
                org_amount = month_map
            continue
        try:
            building_id = int(bid)
        except (TypeError, ValueError):
            continue
        entry = by_building.setdefault(
            building_id,
            {
                "building_id": building_id,
                "building_name": row.get("row_label") or str(building_id),
                "quantity": {str(m): 0 for m in range(1, 13)},
                "amount": {str(m): 0.0 for m in range(1, 13)},
            },
        )
        entry[metric] = month_map
        if row.get("row_label"):
            entry["building_name"] = row["row_label"]

    return org_quantity, org_amount, list(by_building.values())


type_page_plans = "econ-building-indicators-plans"
PLAN_EDIT_EXISTING = "bie-edit-existing"
PLAN_FORM_TABLE = "bie-form-table"
CATALOG_PAGE_SIZE = 15


def _render_catalog(catalog: list[dict], *, page: int = 1, page_size: int = CATALOG_PAGE_SIZE) -> html.Div:
    if not catalog:
        return html.P(
            "Нет показателей с флагом «Отображать в отчете индикаторов» "
            "для выбранного года и версии плана. Отметьте их в админке AnnualPlan.",
            className="text-muted mb-0",
        )

    total = len(catalog)
    page_size = max(1, int(page_size or CATALOG_PAGE_SIZE))
    max_page = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(int(page or 1), max_page))
    start = (page - 1) * page_size
    page_items = catalog[start : start + page_size]

    rows = []
    for item in page_items:
        gid = item["group_id"]
        btn = dbc.Button(
            "Редактировать",
            id={"type": PLAN_EDIT_EXISTING, "index": gid},
            color="primary",
            size="sm",
            className="me-2",
        )
        mark = "есть корпуса" if item.get("has_buildings") else "нет корпусов"
        rows.append(
            html.Tr(
                [
                    html.Td(btn),
                    html.Td(item["group_path"]),
                    html.Td(f"{item['qty_total']} / {item['amt_total']}", className="text-nowrap"),
                    html.Td(mark, className="text-muted small"),
                ]
            )
        )

    return html.Div(
        [
            dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(""),
                                html.Th("Показатель"),
                                html.Th("Итого объём / финансы"),
                                html.Th("Корпуса"),
                            ]
                        )
                    ),
                    html.Tbody(rows),
                ],
                bordered=True,
                hover=True,
                size="sm",
                className="mb-0",
            ),
            html.P(
                f"Стр. {page} из {max_page} · показано {len(page_items)} из {total} "
                f"(только с «Отображать в отчете индикаторов»).",
                className="text-muted small mt-2 mb-0",
            ),
        ]
    )


def _render_form_table(payload: dict) -> dash_table.DataTable:
    return dash_table.DataTable(
        id={"type": PLAN_FORM_TABLE, "index": 0},
        columns=_form_month_columns(),
        data=_form_rows_from_payload(payload),
        editable=True,
        page_size=40,
        style_table={"overflowX": "auto"},
        style_cell={"minWidth": "50px", "textAlign": "center", "padding": "4px"},
        style_cell_conditional=[
            {"if": {"column_id": "row_label"}, "textAlign": "left", "minWidth": "160px"},
            {"if": {"column_id": "metric_label"}, "minWidth": "90px"},
        ],
        style_header={"fontWeight": "bold"},
        style_data_conditional=[
            {
                "if": {"filter_query": '{row_label} = "План МО"'},
                "backgroundColor": "#e7f1ff",
                "fontWeight": "bold",
            },
        ],
        hidden_columns=["building_id", "metric"],
        css=[{"selector": ".show-hide", "rule": "display: none"}],
    )


def _render_form(payload: dict) -> html.Div:
    return html.Div(
        [
            html.H5(payload.get("group_path") or "Индикатор", className="mb-2"),
            html.P(
                "Строки «План МО» и корпуса: для каждого — объёмы и финансы по месяцам. "
                "Σ корпусов не должна превышать план МО (или включите подъём плана МО).",
                className="text-muted small mb-2",
            ),
            _render_form_table(payload),
        ]
    )


def plans_entry_tab() -> html.Div:
    return html.Div(
        [
            dcc.Store(id=f"store-plan-form-{type_page_plans}"),
            dcc.Store(id=f"store-plan-meta-{type_page_plans}"),
            dcc.Store(id=f"store-plan-catalog-{type_page_plans}", data=None),
            dbc.Alert(id=f"alert-{type_page_plans}", is_open=False, duration=8000, className="mb-2"),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Каталог планов", className="mb-2"),
                        html.P(
                            "Только показатели с флагом «Отображать в отчете индикаторов» в AnnualPlan. "
                            "Выберите год и версию плана, нажмите «Получить», затем «Редактировать».",
                            className="text-muted mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Год", className="fw-bold"),
                                        filter_years(type_page_plans),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Версия плана", className="fw-bold"),
                                        dcc.Dropdown(
                                            id=f"dropdown-plan-kind-{type_page_plans}",
                                            options=PLAN_KIND_OPTIONS,
                                            value="internal",
                                            clearable=False,
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Получить",
                                        id=f"btn-get-catalog-{type_page_plans}",
                                        color="primary",
                                        className="mt-4",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-2 mb-3 align-items-start",
                        ),
                        dcc.Loading(
                            id=f"loading-catalog-{type_page_plans}",
                            type="default",
                            children=html.Div(
                                [
                                    html.Div(
                                        id=f"status-{type_page_plans}",
                                        className="text-muted mb-2",
                                    ),
                                    html.Div(
                                        id=f"div-existing-catalog-{type_page_plans}",
                                        children=html.P(
                                            "Выберите год и версию плана, затем нажмите «Получить».",
                                            className="text-muted mb-0",
                                        ),
                                    ),
                                    dbc.Pagination(
                                        id=f"pagination-catalog-{type_page_plans}",
                                        active_page=1,
                                        max_value=1,
                                        fully_expanded=False,
                                        first_last=True,
                                        previous_next=True,
                                        size="sm",
                                        className="mt-2",
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
                className="mb-3 shadow-sm",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Форма индикатора", className="mb-2"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id=f"dropdown-add-building-{type_page_plans}",
                                        options=[],
                                        placeholder="Добавить корпус…",
                                        clearable=True,
                                    ),
                                    width=4,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Добавить корпус",
                                        id=f"btn-add-building-{type_page_plans}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Switch(
                                        id=f"switch-raise-org-{type_page_plans}",
                                        label="Поднять план МО из суммы корпусов",
                                        value=False,
                                        className="mt-1",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Сохранить",
                                        id=f"btn-save-plans-{type_page_plans}",
                                        color="success",
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Закрыть",
                                        id=f"btn-close-form-{type_page_plans}",
                                        color="outline-secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-2 align-items-center mb-2",
                        ),
                        dcc.Loading(
                            id=f"loading-plans-{type_page_plans}",
                            type="default",
                            children=html.Div(
                                id=f"div-plan-editor-{type_page_plans}",
                                children=html.P(
                                    "Выберите показатель в каталоге выше.",
                                    className="text-muted mb-0",
                                ),
                            ),
                        ),
                    ]
                ),
                className="mb-3 shadow-sm",
            ),
        ]
    )


@app.callback(
    Output(f"store-plan-catalog-{type_page_plans}", "data"),
    Output(f"status-{type_page_plans}", "children"),
    Output(f"pagination-catalog-{type_page_plans}", "active_page"),
    Output(f"pagination-catalog-{type_page_plans}", "max_value"),
    Input(f"btn-get-catalog-{type_page_plans}", "n_clicks"),
    Input(f"btn-save-plans-{type_page_plans}", "n_clicks"),
    Input(f"btn-add-building-{type_page_plans}", "n_clicks"),
    State(f"dropdown-year-{type_page_plans}", "value"),
    State(f"dropdown-plan-kind-{type_page_plans}", "value"),
    State(f"store-plan-catalog-{type_page_plans}", "data"),
    prevent_initial_call=True,
)
def refresh_plan_catalog(_get, _save, _add, year, plan_kind, catalog_loaded):
    if not callback_context.triggered:
        raise PreventUpdate
    trigger = callback_context.triggered[0]["prop_id"]
    is_get = f"btn-get-catalog-{type_page_plans}" in trigger
    # После сохранения/добавления корпуса — только если каталог уже загружали
    if not is_get and catalog_loaded is None:
        raise PreventUpdate
    if not year:
        if is_get:
            return None, "Укажите год", 1, 1
        raise PreventUpdate
    kind = plan_kind or "internal"
    catalog = list_plan_catalog(int(year), kind)
    kind_label = "ТФОМС" if kind == "tfoms" else "внутренний"
    status = (
        f"{len(catalog)} показателей (в отчёте индикаторов) · {kind_label} · {year}"
    )
    max_page = max(1, (len(catalog) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    return catalog, status, 1, max_page


@app.callback(
    Output(f"store-plan-catalog-{type_page_plans}", "data", allow_duplicate=True),
    Output(f"status-{type_page_plans}", "children", allow_duplicate=True),
    Output(f"pagination-catalog-{type_page_plans}", "active_page", allow_duplicate=True),
    Output(f"pagination-catalog-{type_page_plans}", "max_value", allow_duplicate=True),
    Input(f"dropdown-year-{type_page_plans}", "value"),
    Input(f"dropdown-plan-kind-{type_page_plans}", "value"),
    prevent_initial_call=True,
)
def reset_plan_catalog_on_filters(_year, _plan_kind):
    """Смена года/версии сбрасывает список — нужна повторная «Получить»."""
    return None, "", 1, 1


@app.callback(
    Output(f"div-existing-catalog-{type_page_plans}", "children"),
    Input(f"store-plan-catalog-{type_page_plans}", "data"),
    Input(f"pagination-catalog-{type_page_plans}", "active_page"),
)
def render_plan_catalog_page(catalog, page):
    if catalog is None:
        return html.P(
            "Выберите год и версию плана, затем нажмите «Получить».",
            className="text-muted mb-0",
        )
    return _render_catalog(catalog, page=page or 1)


@app.callback(
    Output(f"div-plan-editor-{type_page_plans}", "children"),
    Output(f"store-plan-form-{type_page_plans}", "data"),
    Output(f"store-plan-meta-{type_page_plans}", "data"),
    Output(f"dropdown-add-building-{type_page_plans}", "options"),
    Output(f"dropdown-add-building-{type_page_plans}", "value"),
    Output(f"alert-{type_page_plans}", "children"),
    Output(f"alert-{type_page_plans}", "color"),
    Output(f"alert-{type_page_plans}", "is_open"),
    Input({"type": PLAN_EDIT_EXISTING, "index": ALL}, "n_clicks"),
    Input(f"btn-close-form-{type_page_plans}", "n_clicks"),
    Input(f"btn-add-building-{type_page_plans}", "n_clicks"),
    Input(f"btn-save-plans-{type_page_plans}", "n_clicks"),
    State(f"dropdown-year-{type_page_plans}", "value"),
    State(f"dropdown-plan-kind-{type_page_plans}", "value"),
    State(f"dropdown-add-building-{type_page_plans}", "value"),
    State({"type": PLAN_FORM_TABLE, "index": ALL}, "data"),
    State(f"store-plan-meta-{type_page_plans}", "data"),
    State(f"switch-raise-org-{type_page_plans}", "value"),
    prevent_initial_call=True,
)
def plan_form_actions(
    edit_clicks,
    close_clicks,
    add_clicks,
    save_clicks,
    year,
    plan_kind,
    add_building_id,
    tables_data,
    meta,
    raise_org,
):
    if not callback_context.triggered:
        raise PreventUpdate
    trigger = callback_context.triggered[0]["prop_id"]
    if trigger == ".":
        raise PreventUpdate

    kind = plan_kind or "internal"
    empty = (
        html.P("Выберите показатель в каталоге выше.", className="text-muted mb-0"),
        None,
        None,
        [],
        None,
    )

    if f"btn-close-form-{type_page_plans}" in trigger:
        return (*empty, "Форма закрыта", "secondary", True)

    if PLAN_EDIT_EXISTING in trigger:
        if not any(edit_clicks or []):
            raise PreventUpdate
        try:
            tid = json.loads(trigger.split(".")[0])
            group_id = int(tid["index"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            raise PreventUpdate
        if not year:
            return no_update, no_update, no_update, no_update, no_update, "Укажите год", "warning", True
        try:
            payload = load_indicator_plan_form(int(year), group_id, kind)
        except Exception as exc:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                f"Ошибка загрузки: {exc}",
                "danger",
                True,
            )
        meta_out = {
            "year": int(year),
            "group_id": group_id,
            "plan_kind": kind,
            "group_path": payload.get("group_path"),
        }
        return (
            _render_form(payload),
            payload,
            meta_out,
            payload.get("available_buildings") or [],
            None,
            "Форма загружена",
            "success",
            True,
        )

    if f"btn-add-building-{type_page_plans}" in trigger:
        if not meta or not year:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                "Сначала откройте форму индикатора",
                "warning",
                True,
            )
        if not add_building_id:
            return no_update, no_update, no_update, no_update, no_update, "Выберите корпус", "warning", True
        try:
            payload = add_building_to_plan(
                int(year),
                int(meta["group_id"]),
                int(add_building_id),
                meta.get("plan_kind") or kind,
            )
        except Exception as exc:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                f"Ошибка добавления корпуса: {exc}",
                "danger",
                True,
            )
        return (
            _render_form(payload),
            payload,
            meta,
            payload.get("available_buildings") or [],
            None,
            "Корпус добавлен",
            "success",
            True,
        )

    if f"btn-save-plans-{type_page_plans}" in trigger:
        if not meta or not year:
            return no_update, no_update, no_update, no_update, no_update, "Нет открытой формы", "warning", True
        rows = (tables_data or [None])[0] if tables_data else None
        if not rows:
            return no_update, no_update, no_update, no_update, no_update, "Нет данных таблицы", "warning", True
        org_q, org_a, buildings = _payload_from_form_rows(rows)
        try:
            result = save_indicator_plan_form(
                year=int(year),
                group_id=int(meta["group_id"]),
                plan_kind=meta.get("plan_kind") or kind,
                org_quantity=org_q,
                org_amount=org_a,
                buildings=buildings,
                raise_org_from_buildings=bool(raise_org),
            )
        except Exception as exc:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                f"Ошибка сохранения: {exc}",
                "danger",
                True,
            )
        if not result.get("ok"):
            errs = "; ".join(result.get("errors") or ["ошибка валидации"])
            return no_update, no_update, no_update, no_update, no_update, errs, "danger", True
        try:
            payload = load_indicator_plan_form(
                int(year), int(meta["group_id"]), meta.get("plan_kind") or kind
            )
        except Exception:
            payload = None
        msg = (
            f"Сохранено: месяцев МО {result.get('updated_org', 0)}, "
            f"ячеек корпусов {result.get('updated_buildings', 0)}"
        )
        if result.get("raised_org_months"):
            msg += f"; план МО поднят в {result['raised_org_months']} мес."
        if payload:
            return (
                _render_form(payload),
                payload,
                meta,
                payload.get("available_buildings") or [],
                None,
                msg,
                "success",
                True,
            )
        return no_update, no_update, meta, no_update, no_update, msg, "success", True

    raise PreventUpdate
