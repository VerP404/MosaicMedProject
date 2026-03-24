"""Справочники ДН: таблицы эталона, импорт/экспорт JSON, подвкладки по сущностям."""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash import dash_table
from sqlalchemy import text

from apps.dash_dn.app import dash_dn_app as app
from apps.dash_dn.sqlite_catalog.catalog_ops import (
    copy_global_to_user,
    export_catalog,
    import_catalog,
)
from apps.dash_dn.sqlite_catalog.db import get_engine

PREFIX = "dash-dn-ref"


def _engine():
    return get_engine()


def _is_user(cat: str) -> bool:
    return (cat or "global") == "user"


def _global_admin_password() -> str:
    return (os.environ.get("DASH_DN_GLOBAL_ADMIN_PASSWORD") or "").strip()


def _tag_catalog(rows: list[dict], cat: str) -> list[dict]:
    for r in rows:
        r["catalog"] = cat
    return rows


def _can_edit_tables(catalog: str | None, global_unlocked) -> bool:
    """Редактирование таблиц: user — всегда; global — только после ввода пароля."""
    cat = catalog or "global"
    if _is_user(cat):
        return True
    return cat == "global" and bool(global_unlocked) and bool(_global_admin_password())


def _as_int01(v) -> int:
    if v in (True, "1", 1, "True", "true"):
        return 1
    if v in (False, "0", 0, "False", "false", None, ""):
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _as_int_opt(v) -> int | None:
    if v in (None, "", "None"):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _as_int_sort(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


DELETE_ALLOWED = frozenset(
    {
        "dn_service",
        "dn_service_price_period",
        "dn_service_price",
        "dn_specialty",
        "dn_diagnosis_category",
        "dn_diagnosis",
        "dn_diagnosis_group",
        "dn_service_requirement",
    }
)


def _delete_row_by_id(conn, table: str, catalog: str, row_id: int) -> int:
    if table not in DELETE_ALLOWED:
        raise ValueError("Недопустимая таблица")
    res = conn.execute(
        text(f"DELETE FROM {table} WHERE id = :id AND catalog = :c"),
        {"id": int(row_id), "c": catalog},
    )
    return int(res.rowcount or 0)


def layout_body():
    inner_tabs = dbc.Tabs(
        [
            dbc.Tab(
                label="Услуги",
                tab_id="t-svc",
                children=html.Div(
                    [
                        html.P(
                            "Справочник услуг (код + наименование). Цены задаются на вкладках «Периоды цен» и «Цены по периодам».",
                            className="text-muted small",
                        ),
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Код", className="small"),
                                                dbc.Input(id=f"{PREFIX}-svc-code", placeholder="B01.047.001", className="mb-2"),
                                            ],
                                            md=3,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Наименование", className="small"),
                                                dbc.Input(id=f"{PREFIX}-svc-name", placeholder="Наименование", className="mb-2"),
                                            ],
                                            md=6,
                                        ),
                                        dbc.Col(
                                            dbc.Button("Добавить", id=f"{PREFIX}-btn-add-svc", color="primary", className="mt-4"),
                                            md=3,
                                        ),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button(
                                            "Сохранить изменения таблицы",
                                            id=f"{PREFIX}-btn-save-svc",
                                            color="primary",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                        ),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-svc",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-svc",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-services",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "Код", "id": "code"},
                                {"name": "Наименование", "id": "name"},
                                {"name": "Активна", "id": "is_active"},
                            ],
                            data=[],
                            page_size=12,
                            filter_action="native",
                            sort_action="native",
                            style_table={"overflowX": "auto"},
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Периоды цен",
                tab_id="t-per",
                children=html.Div(
                    [
                        html.P(
                            "Период действия тарифов: дата начала обязательна; дата окончания пустая — «по н.в.». "
                            "Один и тот же период можно привязать ко многим услугам с разной ценой на вкладке «Цены по периодам».",
                            className="text-muted small",
                        ),
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col([dbc.Label("С даты (YYYY-MM-DD)", className="small"), dbc.Input(id=f"{PREFIX}-per-start", placeholder="2026-01-01")], md=3),
                                        dbc.Col([dbc.Label("По дату (пусто = бессрочно)", className="small"), dbc.Input(id=f"{PREFIX}-per-end", placeholder="")], md=3),
                                        dbc.Col([dbc.Label("Название периода", className="small"), dbc.Input(id=f"{PREFIX}-per-title", placeholder="2026 год")], md=4),
                                        dbc.Col(dbc.Button("Добавить период", id=f"{PREFIX}-btn-add-per", color="primary", className="mt-4"), md=2),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-per", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-per",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-per",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-periods",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "С", "id": "date_start"},
                                {"name": "По", "id": "date_end"},
                                {"name": "Название", "id": "title"},
                                {"name": "Активен", "id": "is_active"},
                            ],
                            data=[],
                            page_size=10,
                            filter_action="native",
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Цены по периодам",
                tab_id="t-price",
                children=html.Div(
                    [
                        html.P(
                            "Сначала выберите период — загрузятся все услуги этого справочника. "
                            "Для нового периода у услуг без цены показывается 0; сохранение создаёт строку в БД. "
                            "Клик по строке подставляет услугу и сумму в форму выше (услугу из списка выбрать нельзя — только из таблицы).",
                            className="text-muted small",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Период (фильтр таблицы)", className="small fw-semibold"),
                                        dcc.Dropdown(
                                            id=f"{PREFIX}-filter-price-period",
                                            options=[],
                                            clearable=True,
                                            placeholder="Выберите период…",
                                            className="dash-dn-dropdown",
                                        ),
                                    ],
                                    md=6,
                                    lg=5,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Стоимость (фильтр)", className="small fw-semibold"),
                                        dcc.Dropdown(
                                            id=f"{PREFIX}-filter-price-amount",
                                            options=[
                                                {"label": "Все", "value": "all"},
                                                {"label": "Только нулевые (0)", "value": "zero"},
                                                {"label": "Только ненулевые", "value": "nonzero"},
                                            ],
                                            value="all",
                                            clearable=False,
                                            className="dash-dn-dropdown",
                                        ),
                                    ],
                                    md=6,
                                    lg=4,
                                ),
                            ],
                            className="g-2 mb-3",
                        ),
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Услуга", className="small"),
                                                dcc.Store(id=f"{PREFIX}-price-form-service-id", data=None),
                                                dbc.Input(
                                                    id=f"{PREFIX}-price-form-service-label",
                                                    type="text",
                                                    placeholder="Выберите строку в таблице…",
                                                    readonly=True,
                                                    className="form-control form-control-sm",
                                                ),
                                            ],
                                            md=5,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Сумма ₽", className="small"),
                                                dbc.Input(id=f"{PREFIX}-inp-price", type="number", step="0.01"),
                                            ],
                                            md=3,
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Сохранить цену",
                                                id=f"{PREFIX}-btn-add-price",
                                                color="primary",
                                                className="mt-4",
                                            ),
                                            md=2,
                                        ),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-price", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-price",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-price",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-prices",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "service_id", "id": "service_id", "editable": False},
                                {"name": "period_id", "id": "period_id", "editable": False},
                                {"name": "Услуга", "id": "service_code", "editable": False},
                                {"name": "Наименование", "id": "service_name", "editable": False},
                                {"name": "Период", "id": "period_title", "editable": False},
                                {"name": "С", "id": "date_start", "editable": False},
                                {"name": "По", "id": "date_end", "editable": False},
                                {"name": "Цена", "id": "price"},
                            ],
                            data=[],
                            page_size=20,
                            filter_action="native",
                            hidden_columns=["id", "service_id", "period_id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Специальности",
                tab_id="t-spec",
                children=html.Div(
                    [
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col([dbc.Label("Название", className="small"), dbc.Input(id=f"{PREFIX}-inp-spec-name")], md=8),
                                        dbc.Col(dbc.Button("Добавить", id=f"{PREFIX}-btn-add-spec", color="primary", className="mt-4"), md=4),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-spec", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-spec",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-spec",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-specs",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "Название", "id": "name"},
                                {"name": "Активна", "id": "is_active"},
                            ],
                            data=[],
                            page_size=15,
                            filter_action="native",
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Категории диагнозов",
                tab_id="t-cat",
                children=html.Div(
                    [
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col([dbc.Label("Название (168н)", className="small"), dbc.Input(id=f"{PREFIX}-inp-cat-name")], md=8),
                                        dbc.Col(dbc.Button("Добавить", id=f"{PREFIX}-btn-add-cat", color="primary", className="mt-4"), md=4),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-cat", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-cat",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-cat",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-cats",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "Название", "id": "name"},
                                {"name": "Активна", "id": "is_active"},
                            ],
                            data=[],
                            page_size=12,
                            filter_action="native",
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Диагнозы",
                tab_id="t-diag",
                children=html.Div(
                    [
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col([dbc.Label("Код МКБ", className="small"), dbc.Input(id=f"{PREFIX}-inp-diag-code", placeholder="I10")], md=3),
                                        dbc.Col([dbc.Label("Категория", className="small"), dcc.Dropdown(id=f"{PREFIX}-dd-diag-cat", options=[])], md=5),
                                        dbc.Col(dbc.Button("Добавить", id=f"{PREFIX}-btn-add-diag", color="primary", className="mt-4"), md=2),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-diag", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-diag",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-diag",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-diags",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "Код", "id": "code"},
                                {"name": "Категория", "id": "category_name", "editable": False},
                                {"name": "Активен", "id": "is_active"},
                            ],
                            data=[],
                            page_size=15,
                            filter_action="native",
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Группы диагнозов",
                tab_id="t-grp",
                children=html.Div(
                    [
                        html.P(
                            "Группы задают столбцы матрицы услуг; поле «Правило» — текст для сопоставления с кодами МКБ (как в Excel usl_spec).",
                            className="text-muted small",
                        ),
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col([dbc.Label("Код группы", className="small"), dbc.Input(id=f"{PREFIX}-inp-grp-code")], md=2),
                                        dbc.Col([dbc.Label("Название", className="small"), dbc.Input(id=f"{PREFIX}-inp-grp-title")], md=3),
                                        dbc.Col([dbc.Label("Порядок", className="small"), dbc.Input(id=f"{PREFIX}-inp-grp-order", type="number")], md=1),
                                        dbc.Col([dbc.Label("Правило", className="small"), dbc.Input(id=f"{PREFIX}-inp-grp-rule")], md=4),
                                        dbc.Col(dbc.Button("Добавить", id=f"{PREFIX}-btn-add-grp", color="primary", className="mt-4"), md=2),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-grp", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-grp",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-grp",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-grps",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "Код", "id": "code"},
                                {"name": "Название", "id": "title"},
                                {"name": "Порядок", "id": "sort_order"},
                                {"name": "Правило", "id": "rule"},
                                {"name": "Активна", "id": "is_active"},
                            ],
                            data=[],
                            page_size=12,
                            filter_action="native",
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
            dbc.Tab(
                label="Требования услуг",
                tab_id="t-req",
                children=html.Div(
                    [
                        html.P(
                            "Связка: услуга обязательна для группы диагнозов при наблюдении у указанной специальности (ячейка «+» в матрице).",
                            className="text-muted small",
                        ),
                        html.Div(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [dbc.Label("Услуга", className="small"), dcc.Dropdown(id=f"{PREFIX}-dd-req-svc", options=[])],
                                            md=4,
                                        ),
                                        dbc.Col(
                                            [dbc.Label("Группа диагнозов", className="small"), dcc.Dropdown(id=f"{PREFIX}-dd-req-grp", options=[])],
                                            md=4,
                                        ),
                                        dbc.Col(
                                            [dbc.Label("Специальность", className="small"), dcc.Dropdown(id=f"{PREFIX}-dd-req-spec", options=[])],
                                            md=3,
                                        ),
                                        dbc.Col(
                                            dbc.Button("Добавить", id=f"{PREFIX}-btn-add-req", color="primary", className="mt-4"),
                                            md=1,
                                        ),
                                    ],
                                    className="g-2 mb-2",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Сохранить изменения таблицы", id=f"{PREFIX}-btn-save-req", color="primary", outline=True, size="sm", disabled=True),
                                        dbc.Button(
                                            "Удалить выбранные строки",
                                            id=f"{PREFIX}-btn-del-sel-req",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            disabled=True,
                                            className="ms-2",
                                        ),
                                    ],
                                    className="d-flex flex-wrap gap-2 mb-2",
                                ),
                            ],
                            id=f"{PREFIX}-ref-edit-req",
                        ),
                        dash_table.DataTable(
                            id=f"{PREFIX}-table-reqs",
                            columns=[
                                {"name": "Каталог", "id": "catalog", "editable": False},
                                {"name": "id", "id": "id", "editable": False},
                                {"name": "Услуга", "id": "service_code", "editable": False},
                                {"name": "Группа", "id": "group_code", "editable": False},
                                {"name": "Специальность", "id": "specialty_name", "editable": False},
                                {"name": "Обяз.", "id": "is_required"},
                            ],
                            data=[],
                            page_size=15,
                            filter_action="native",
                            hidden_columns=["id"],
                            editable=False,
                            row_selectable=False,
                            selected_rows=[],
                        ),
                    ],
                    className="pt-3",
                ),
            ),
        ],
        id=f"{PREFIX}-inner-tabs",
        active_tab="t-svc",
        className="mt-2",
    )

    return html.Div(
        [
            html.H4("Справочники ДН", className="fw-bold mb-3"),
            html.Div(id=f"{PREFIX}-ref-view-hint", className="mb-2"),
            html.Div(
                id=f"{PREFIX}-ref-global-ops-wrap",
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [html.I(className="bi bi-copy me-1"), "Копировать global → user"],
                                        id=f"{PREFIX}-btn-copy",
                                        color="secondary",
                                        outline=True,
                                        className="me-2 mb-2",
                                        title="Доступно в режиме правки эталона (шапка)",
                                    ),
                                    dbc.Button(
                                        [html.I(className="bi bi-download me-1"), "Экспорт JSON"],
                                        id=f"{PREFIX}-btn-export",
                                        color="primary",
                                        outline=True,
                                        className="me-2 mb-2",
                                        title="Доступно в режиме правки эталона (шапка)",
                                    ),
                                    dcc.Upload(
                                        id=f"{PREFIX}-upload",
                                        children=dbc.Button(
                                            [html.I(className="bi bi-upload me-1"), "Импорт JSON в локальный слой"],
                                            color="success",
                                            outline=True,
                                            className="mb-2",
                                        ),
                                        multiple=False,
                                    ),
                                ],
                                md=12,
                            ),
                        ],
                        className="mb-2",
                    ),
                ],
            ),
            html.Div(id=f"{PREFIX}-msg-main", className="mb-2"),
            html.Div(id=f"{PREFIX}-msg-global-ops", className="mb-2"),
            html.Div(id=f"{PREFIX}-msg-edit", className="mb-2"),
            dcc.Download(id=f"{PREFIX}-download"),
            html.Hr(),
            inner_tabs,
        ]
    )


# --- загрузка таблиц ---

def _load_services(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT id, code, name, is_active FROM dn_service
        WHERE catalog = :c ORDER BY sort_order, code
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _load_periods(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT id, date_start, date_end, title, is_active
        FROM dn_service_price_period WHERE catalog = :c ORDER BY date_start DESC
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _load_prices(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT sp.id AS id, s.code AS service_code, s.name AS service_name, pp.title AS period_title,
               pp.date_start, pp.date_end, sp.price
        FROM dn_service_price sp
        JOIN dn_service s ON s.id = sp.service_id AND s.catalog = :c
        JOIN dn_service_price_period pp ON pp.id = sp.period_id AND pp.catalog = :c
        WHERE sp.catalog = :c
        ORDER BY pp.date_start DESC, s.code
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        d["price"] = float(d["price"]) if d.get("price") is not None else None
        out.append(d)
    return _tag_catalog(out, catalog)


def _load_prices_matrix(catalog: str, period_id: int) -> list[dict]:
    """Все активные услуги × один период; без строки в dn_service_price — цена 0, id пустой (новая запись)."""
    q = text(
        """
        SELECT
            s.id AS service_id,
            s.code AS service_code,
            s.name AS service_name,
            pp.title AS period_title,
            pp.date_start AS date_start,
            pp.date_end AS date_end,
            pp.id AS period_id,
            sp.id AS id,
            COALESCE(sp.price, 0) AS price
        FROM dn_service s
        INNER JOIN dn_service_price_period pp ON pp.id = :pid AND pp.catalog = :c
        LEFT JOIN dn_service_price sp
            ON sp.service_id = s.id AND sp.period_id = pp.id AND sp.catalog = :c
        WHERE s.catalog = :c AND s.is_active = 1
        ORDER BY s.sort_order, s.code
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog, "pid": period_id}).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        d["catalog"] = catalog
        d["service_id"] = int(d["service_id"])
        d["period_id"] = int(d["period_id"])
        rid = d.get("id")
        if rid is None:
            d["id"] = ""
        else:
            d["id"] = int(rid)
        d["price"] = float(d["price"]) if d.get("price") is not None else 0.0
        for k in ("date_start", "date_end"):
            v = d.get(k)
            d[k] = str(v) if v is not None and v != "" else ""
        out.append(d)
    return out


def _prices_table_data_for_filter(cat: str, period_filter) -> list[dict]:
    if period_filter in (None, ""):
        return []
    try:
        pid = int(period_filter)
    except (TypeError, ValueError):
        return []
    return _load_prices_matrix(cat, pid)


def _row_price_float(row: dict) -> float:
    p = row.get("price")
    try:
        return float(p) if p is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _filter_price_rows_by_amount(rows: list[dict], how: str | None) -> list[dict]:
    if how in (None, "", "all"):
        return list(rows)
    out: list[dict] = []
    for r in rows:
        pv = _row_price_float(r)
        is_zero = abs(pv) < 1e-12
        if how == "zero" and is_zero:
            out.append(r)
        elif how == "nonzero" and not is_zero:
            out.append(r)
    return out


def _prices_matrix_filtered(cat: str, period_filter, amount_filter: str | None) -> list[dict]:
    raw = _prices_table_data_for_filter(cat, period_filter)
    return _filter_price_rows_by_amount(raw, amount_filter)


def _load_specs(catalog: str) -> list[dict]:
    q = text("SELECT id, name, is_active FROM dn_specialty WHERE catalog = :c ORDER BY name")
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _load_cats(catalog: str) -> list[dict]:
    q = text("SELECT id, name, is_active FROM dn_diagnosis_category WHERE catalog = :c ORDER BY name")
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _load_diags(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT d.id, d.code, COALESCE(c.name, '') AS category_name, d.is_active
        FROM dn_diagnosis d
        LEFT JOIN dn_diagnosis_category c ON c.id = d.category_id AND c.catalog = :c
        WHERE d.catalog = :c ORDER BY d.code
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _load_grps(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT id, code, title, sort_order, rule, is_active FROM dn_diagnosis_group
        WHERE catalog = :c ORDER BY sort_order, code
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _load_reqs(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT sr.id AS id, s.code AS service_code, g.code AS group_code, sp.name AS specialty_name, sr.is_required
        FROM dn_service_requirement sr
        JOIN dn_service s ON s.id = sr.service_id AND s.catalog = :c
        JOIN dn_diagnosis_group g ON g.id = sr.group_id AND g.catalog = :c
        JOIN dn_specialty sp ON sp.id = sr.specialty_id AND sp.catalog = :c
        WHERE sr.catalog = :c
        ORDER BY sp.name, g.code, s.code
        LIMIT 800
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return _tag_catalog([dict(r) for r in rows], catalog)


def _dd_services(catalog: str) -> list[dict]:
    q = text("SELECT id, code, name FROM dn_service WHERE catalog = :c AND is_active = 1 ORDER BY code")
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return [{"label": f'{r["code"]} — {r["name"][:40]}', "value": r["id"]} for r in rows]


def _dd_periods(catalog: str) -> list[dict]:
    q = text(
        """
        SELECT id, date_start, date_end, title FROM dn_service_price_period
        WHERE catalog = :c AND is_active = 1 ORDER BY date_start DESC
        """
    )
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    out = []
    for r in rows:
        de = r["date_end"] or "…"
        label = f'{r["date_start"]} — {de} ({r["title"] or ""})'[:80]
        out.append({"label": label, "value": r["id"]})
    return out


def _dd_groups(catalog: str) -> list[dict]:
    q = text("SELECT id, code, title FROM dn_diagnosis_group WHERE catalog = :c ORDER BY code")
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return [{"label": f'{r["code"]} — {str(r["title"])[:30]}', "value": r["id"]} for r in rows]


def _dd_specialties(catalog: str) -> list[dict]:
    q = text("SELECT id, name FROM dn_specialty WHERE catalog = :c ORDER BY name")
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return [{"label": r["name"], "value": r["id"]} for r in rows]


def _dd_categories(catalog: str) -> list[dict]:
    q = text("SELECT id, name FROM dn_diagnosis_category WHERE catalog = :c ORDER BY name")
    with _engine().connect() as conn:
        rows = conn.execute(q, {"c": catalog}).mappings().all()
    return [{"label": r["name"], "value": r["id"]} for r in rows]


# --- callbacks ---


def _edit_tuple(on: bool):
    """editable, row_selectable, save_disabled, del_disabled для одной таблицы."""
    ed = bool(on)
    rs = "multi" if on else False
    dis = not on
    return ed, rs, dis, dis


def _edit_tuple_prices(on: bool):
    """То же для таблицы «Цены по периодам»: одна выбранная строка (синхрон с формой)."""
    ed = bool(on)
    rs = "single" if on else False
    dis = not on
    return ed, rs, dis, dis


@app.callback(
    [
        Output(f"{PREFIX}-table-services", "editable"),
        Output(f"{PREFIX}-table-services", "row_selectable"),
        Output(f"{PREFIX}-btn-save-svc", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-svc", "disabled"),
        Output(f"{PREFIX}-table-periods", "editable"),
        Output(f"{PREFIX}-table-periods", "row_selectable"),
        Output(f"{PREFIX}-btn-save-per", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-per", "disabled"),
        Output(f"{PREFIX}-table-prices", "editable"),
        Output(f"{PREFIX}-table-prices", "row_selectable"),
        Output(f"{PREFIX}-btn-save-price", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-price", "disabled"),
        Output(f"{PREFIX}-table-specs", "editable"),
        Output(f"{PREFIX}-table-specs", "row_selectable"),
        Output(f"{PREFIX}-btn-save-spec", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-spec", "disabled"),
        Output(f"{PREFIX}-table-cats", "editable"),
        Output(f"{PREFIX}-table-cats", "row_selectable"),
        Output(f"{PREFIX}-btn-save-cat", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-cat", "disabled"),
        Output(f"{PREFIX}-table-diags", "editable"),
        Output(f"{PREFIX}-table-diags", "row_selectable"),
        Output(f"{PREFIX}-btn-save-diag", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-diag", "disabled"),
        Output(f"{PREFIX}-table-grps", "editable"),
        Output(f"{PREFIX}-table-grps", "row_selectable"),
        Output(f"{PREFIX}-btn-save-grp", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-grp", "disabled"),
        Output(f"{PREFIX}-table-reqs", "editable"),
        Output(f"{PREFIX}-table-reqs", "row_selectable"),
        Output(f"{PREFIX}-btn-save-req", "disabled"),
        Output(f"{PREFIX}-btn-del-sel-req", "disabled"),
    ],
    Input("dash-dn-global-unlocked", "data"),
)
def ref_toggle_table_edit_mode(unlocked):
    on = _can_edit_tables("global", unlocked)
    t = _edit_tuple(on)
    tp = _edit_tuple_prices(on)
    return t + t + tp + t + t + t + t + t


@app.callback(
    Output(f"{PREFIX}-ref-global-ops-wrap", "style"),
    Output(f"{PREFIX}-ref-edit-svc", "style"),
    Output(f"{PREFIX}-ref-edit-per", "style"),
    Output(f"{PREFIX}-ref-edit-price", "style"),
    Output(f"{PREFIX}-ref-edit-spec", "style"),
    Output(f"{PREFIX}-ref-edit-cat", "style"),
    Output(f"{PREFIX}-ref-edit-diag", "style"),
    Output(f"{PREFIX}-ref-edit-grp", "style"),
    Output(f"{PREFIX}-ref-edit-req", "style"),
    Input("dash-dn-global-unlocked", "data"),
)
def ref_toggle_admin_sections_visibility(unlocked):
    """Без пароля эталона скрываем формы добавления и кнопки — остаётся просмотр таблиц."""
    show = _can_edit_tables("global", unlocked)
    st = {"display": "block"} if show else {"display": "none"}
    return (st,) * 9


@app.callback(
    Output(f"{PREFIX}-ref-view-hint", "children"),
    Input("dash-dn-global-unlocked", "data"),
)
def ref_view_mode_hint(unlocked):
    if _can_edit_tables("global", unlocked):
        return ""
    return dbc.Alert(
        "Справочники эталона в режиме просмотра: таблицы ниже можно фильтровать и смотреть. "
        "Добавление записей, копирование global→user, импорт/экспорт JSON и правка таблиц — после «Включить» с паролем в шапке.",
        color="info",
        className="py-2 mb-0 small",
    )


@app.callback(
    [
        Output(f"{PREFIX}-table-services", "selected_rows"),
        Output(f"{PREFIX}-table-periods", "selected_rows"),
        Output(f"{PREFIX}-table-prices", "selected_rows"),
        Output(f"{PREFIX}-table-specs", "selected_rows"),
        Output(f"{PREFIX}-table-cats", "selected_rows"),
        Output(f"{PREFIX}-table-diags", "selected_rows"),
        Output(f"{PREFIX}-table-grps", "selected_rows"),
        Output(f"{PREFIX}-table-reqs", "selected_rows"),
    ],
    Input("dash-dn-active-catalog", "data"),
)
def ref_clear_selected_on_catalog_change(_catalog):
    return [], [], [], [], [], [], [], []


@app.callback(
    Output(f"{PREFIX}-filter-price-period", "options"),
    Output(f"{PREFIX}-dd-req-svc", "options"),
    Output(f"{PREFIX}-dd-req-grp", "options"),
    Output(f"{PREFIX}-dd-req-spec", "options"),
    Output(f"{PREFIX}-dd-diag-cat", "options"),
    Input("dash-dn-active-catalog", "data"),
)
def ref_load_dropdowns(_active_catalog):
    cat = "global"
    return (
        _dd_periods(cat),
        _dd_services(cat),
        _dd_groups(cat),
        _dd_specialties(cat),
        _dd_categories(cat),
    )


@app.callback(
    Output(f"{PREFIX}-table-prices", "selected_rows", allow_duplicate=True),
    Input(f"{PREFIX}-filter-price-period", "value"),
    Input(f"{PREFIX}-filter-price-amount", "value"),
    prevent_initial_call=True,
)
def ref_clear_price_selection_on_period_or_amount_change(_period_value, _amount_filter):
    return []


@app.callback(
    Output(f"{PREFIX}-price-form-service-id", "data"),
    Output(f"{PREFIX}-price-form-service-label", "value"),
    Output(f"{PREFIX}-inp-price", "value"),
    Input(f"{PREFIX}-table-prices", "selected_rows"),
    Input(f"{PREFIX}-filter-price-period", "value"),
    Input(f"{PREFIX}-filter-price-amount", "value"),
    State(f"{PREFIX}-table-prices", "data"),
    prevent_initial_call=False,
)
def sync_price_form_from_table_or_filter(selected_rows, period_filter, amount_filter, data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    tid = ctx.triggered[0]["prop_id"].split(".")[0]
    if tid in (f"{PREFIX}-filter-price-period", f"{PREFIX}-filter-price-amount"):
        return None, "", None
    if tid == f"{PREFIX}-table-prices":
        if selected_rows and data:
            idx = selected_rows[0]
            if idx < len(data):
                row = data[idx]
                code = (row.get("service_code") or "").strip()
                name = (row.get("service_name") or "").strip()
                label = f"{code} — {name}" if code else name
                return row.get("service_id"), label, row.get("price")
        raise PreventUpdate
    raise PreventUpdate


@app.callback(
    Output(f"{PREFIX}-table-services", "data"),
    Output(f"{PREFIX}-table-periods", "data"),
    Output(f"{PREFIX}-table-prices", "data"),
    Output(f"{PREFIX}-table-specs", "data"),
    Output(f"{PREFIX}-table-cats", "data"),
    Output(f"{PREFIX}-table-diags", "data"),
    Output(f"{PREFIX}-table-grps", "data"),
    Output(f"{PREFIX}-table-reqs", "data"),
    Output(f"{PREFIX}-msg-global-ops", "children"),
    Input(f"{PREFIX}-filter-price-period", "value"),
    Input(f"{PREFIX}-filter-price-amount", "value"),
    Input(f"{PREFIX}-btn-copy", "n_clicks"),
    Input(f"{PREFIX}-upload", "contents"),
    Input(f"{PREFIX}-btn-add-svc", "n_clicks"),
    Input(f"{PREFIX}-btn-add-per", "n_clicks"),
    Input(f"{PREFIX}-btn-add-price", "n_clicks"),
    Input(f"{PREFIX}-btn-add-spec", "n_clicks"),
    Input(f"{PREFIX}-btn-add-cat", "n_clicks"),
    Input(f"{PREFIX}-btn-add-diag", "n_clicks"),
    Input(f"{PREFIX}-btn-add-grp", "n_clicks"),
    Input(f"{PREFIX}-btn-add-req", "n_clicks"),
    State(f"{PREFIX}-svc-code", "value"),
    State(f"{PREFIX}-svc-name", "value"),
    State(f"{PREFIX}-upload", "filename"),
    State(f"{PREFIX}-per-start", "value"),
    State(f"{PREFIX}-per-end", "value"),
    State(f"{PREFIX}-per-title", "value"),
    State(f"{PREFIX}-price-form-service-id", "data"),
    State(f"{PREFIX}-inp-price", "value"),
    State(f"{PREFIX}-inp-spec-name", "value"),
    State(f"{PREFIX}-inp-cat-name", "value"),
    State(f"{PREFIX}-inp-diag-code", "value"),
    State(f"{PREFIX}-dd-diag-cat", "value"),
    State(f"{PREFIX}-inp-grp-code", "value"),
    State(f"{PREFIX}-inp-grp-title", "value"),
    State(f"{PREFIX}-inp-grp-order", "value"),
    State(f"{PREFIX}-inp-grp-rule", "value"),
    State(f"{PREFIX}-dd-req-svc", "value"),
    State(f"{PREFIX}-dd-req-grp", "value"),
    State(f"{PREFIX}-dd-req-spec", "value"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=False,
)
def ref_refresh_all_tables(
    period_filter,
    price_amount_filter,
    n_copy,
    upload_contents,
    n_add_svc,
    n_add_per,
    n_add_price,
    n_add_spec,
    n_add_cat,
    n_add_diag,
    n_add_grp,
    n_add_req,
    svc_code,
    svc_name,
    upload_name,
    per_start,
    per_end,
    per_title,
    price_svc,
    price_val,
    spec_name,
    cat_name,
    diag_code,
    diag_cat_id,
    grp_code,
    grp_title,
    grp_order,
    grp_rule,
    req_svc,
    req_grp,
    req_spec,
    unlocked,
):
    ctx = callback_context
    eng = _engine()
    cat = "global"
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    msg_ops = no_update

    if triggered == f"{PREFIX}-btn-copy" and n_copy:
        if _can_edit_tables("global", unlocked):
            try:
                copy_global_to_user(eng)
            except Exception:
                pass
        else:
            msg_ops = dbc.Alert(
                "Копирование в пользовательский слой доступно после включения режима паролем в шапке.",
                color="warning",
                className="py-2 mb-0",
            )

    elif triggered == f"{PREFIX}-upload" and upload_contents:
        if _can_edit_tables("global", unlocked):
            try:
                _ct, cs = upload_contents.split(",", 1)
                payload = json.loads(base64.b64decode(cs).decode("utf-8"))
                with eng.begin() as conn:
                    import_catalog(conn, payload, target_catalog="user")
            except Exception:
                pass
        else:
            msg_ops = dbc.Alert(
                "Импорт JSON доступен после включения режима паролем в шапке.",
                color="warning",
                className="py-2 mb-0",
            )

    elif _can_edit_tables("global", unlocked):
        try:
            with eng.begin() as conn:
                if triggered == f"{PREFIX}-btn-add-svc" and n_add_svc:
                    code = (svc_code or "").strip()
                    name = (svc_name or "").strip()
                    if code and name:
                        conn.execute(
                            text(
                                "INSERT INTO dn_service (catalog, code, name, sort_order, is_active) "
                                "VALUES (:c, :code, :name, 0, 1)"
                            ),
                            {"c": cat, "code": code, "name": name},
                        )
                elif triggered == f"{PREFIX}-btn-add-per" and n_add_per:
                    ds = (per_start or "").strip()
                    if ds:
                        de = (per_end or "").strip() or None
                        conn.execute(
                            text(
                                "INSERT INTO dn_service_price_period (catalog, date_start, date_end, title, is_active) "
                                "VALUES (:c, :ds, :de, :t, 1)"
                            ),
                            {"c": cat, "ds": ds, "de": de, "t": (per_title or "").strip()[:128]},
                        )
                elif triggered == f"{PREFIX}-btn-add-price" and n_add_price:
                    if (
                        price_svc
                        and period_filter not in (None, "")
                        and price_val is not None
                    ):
                        conn.execute(
                            text(
                                "INSERT INTO dn_service_price (catalog, service_id, period_id, price) "
                                "VALUES (:c, :sid, :pid, :pr) ON CONFLICT(catalog, service_id, period_id) "
                                "DO UPDATE SET price = excluded.price"
                            ),
                            {"c": cat, "sid": int(price_svc), "pid": int(period_filter), "pr": float(price_val)},
                        )
                elif triggered == f"{PREFIX}-btn-add-spec" and n_add_spec:
                    nm = (spec_name or "").strip()
                    if nm:
                        conn.execute(
                            text("INSERT INTO dn_specialty (catalog, name, is_active) VALUES (:c, :n, 1)"),
                            {"c": cat, "n": nm},
                        )
                elif triggered == f"{PREFIX}-btn-add-cat" and n_add_cat:
                    nm = (cat_name or "").strip()
                    if nm:
                        conn.execute(
                            text("INSERT INTO dn_diagnosis_category (catalog, name, is_active) VALUES (:c, :n, 1)"),
                            {"c": cat, "n": nm},
                        )
                elif triggered == f"{PREFIX}-btn-add-diag" and n_add_diag:
                    dc = _norm_diag_code(diag_code)
                    if dc:
                        cid = int(diag_cat_id) if diag_cat_id else None
                        conn.execute(
                            text(
                                "INSERT INTO dn_diagnosis (catalog, code, category_id, is_active) "
                                "VALUES (:c, :code, :cid, 1)"
                            ),
                            {"c": cat, "code": dc, "cid": cid},
                        )
                elif triggered == f"{PREFIX}-btn-add-grp" and n_add_grp:
                    gc = (grp_code or "").strip()[:256]
                    if gc:
                        so = int(grp_order) if grp_order not in (None, "") else 0
                        conn.execute(
                            text(
                                "INSERT INTO dn_diagnosis_group (catalog, code, title, sort_order, rule, is_active) "
                                "VALUES (:c, :code, :title, :so, :rule, 1)"
                            ),
                            {
                                "c": cat,
                                "code": gc,
                                "title": (grp_title or "")[:255],
                                "so": so,
                                "rule": (grp_rule or "")[:2000],
                            },
                        )
                elif triggered == f"{PREFIX}-btn-add-req" and n_add_req:
                    if req_svc and req_grp and req_spec:
                        conn.execute(
                            text(
                                "INSERT INTO dn_service_requirement (catalog, service_id, group_id, specialty_id, is_required) "
                                "VALUES (:c, :sid, :gid, :spid, 1) ON CONFLICT(catalog, service_id, group_id, specialty_id) DO NOTHING"
                            ),
                            {"c": cat, "sid": int(req_svc), "gid": int(req_grp), "spid": int(req_spec)},
                        )
        except Exception:
            pass

    return (
        _load_services(cat),
        _load_periods(cat),
        _prices_matrix_filtered(cat, period_filter, price_amount_filter),
        _load_specs(cat),
        _load_cats(cat),
        _load_diags(cat),
        _load_grps(cat),
        _load_reqs(cat),
        msg_ops,
    )


def _norm_diag_code(s) -> str:
    if not s:
        return ""
    return str(s).strip().upper().split()[0]


# --- сохранение / удаление строк таблиц (эталон; правка global после пароля на вкладке «Подбор услуг») ---


@app.callback(
    Output(f"{PREFIX}-table-services", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-services", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children"),
    Input(f"{PREFIX}-btn-save-svc", "n_clicks"),
    State(f"{PREFIX}-table-services", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_services(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                conn.execute(
                    text(
                        "UPDATE dn_service SET code=:code, name=:name, is_active=:ia "
                        "WHERE id=:id AND catalog=:c"
                    ),
                    {
                        "code": str(row.get("code") or "").strip()[:128],
                        "name": str(row.get("name") or "").strip()[:512],
                        "ia": _as_int01(row.get("is_active")),
                        "id": int(rid),
                        "c": cat,
                    },
                )
        return _load_services(cat), [], dbc.Alert("Таблица «Услуги» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-services", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-services", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-svc", "n_clicks"),
    State(f"{PREFIX}-table-services", "data"),
    State(f"{PREFIX}-table-services", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_services(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_service", cat, int(rid))
        return _load_services(cat), [], dbc.Alert("Выбранные услуги удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-periods", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-periods", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-per", "n_clicks"),
    State(f"{PREFIX}-table-periods", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_periods(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                de = str(row.get("date_end") or "").strip() or None
                conn.execute(
                    text(
                        "UPDATE dn_service_price_period SET date_start=:ds, date_end=:de, title=:t, is_active=:ia "
                        "WHERE id=:id AND catalog=:c"
                    ),
                    {
                        "ds": str(row.get("date_start") or "").strip()[:32],
                        "de": de,
                        "t": str(row.get("title") or "").strip()[:128],
                        "ia": _as_int01(row.get("is_active")),
                        "id": int(rid),
                        "c": cat,
                    },
                )
        return _load_periods(cat), [], dbc.Alert("Таблица «Периоды цен» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-periods", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-periods", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-per", "n_clicks"),
    State(f"{PREFIX}-table-periods", "data"),
    State(f"{PREFIX}-table-periods", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_periods(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_service_price_period", cat, int(rid))
        return _load_periods(cat), [], dbc.Alert("Выбранные периоды удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-prices", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-prices", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-price", "n_clicks"),
    State(f"{PREFIX}-table-prices", "data"),
    State(f"{PREFIX}-filter-price-period", "value"),
    State(f"{PREFIX}-filter-price-amount", "value"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_prices(n, data, period_filter, amount_filter, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                price = _as_float(row.get("price"))
                pid = row.get("period_id")
                sid = row.get("service_id")
                if rid in (None, "", "None"):
                    if pid is None or sid is None:
                        continue
                    conn.execute(
                        text(
                            "INSERT INTO dn_service_price (catalog, service_id, period_id, price) "
                            "VALUES (:c, :sid, :pid, :pr) ON CONFLICT(catalog, service_id, period_id) "
                            "DO UPDATE SET price = excluded.price"
                        ),
                        {"c": cat, "sid": int(sid), "pid": int(pid), "pr": price},
                    )
                else:
                    conn.execute(
                        text("UPDATE dn_service_price SET price=:p WHERE id=:id AND catalog=:c"),
                        {"p": price, "id": int(rid), "c": cat},
                    )
        return (
            _prices_matrix_filtered(cat, period_filter, amount_filter),
            [],
            dbc.Alert("Таблица «Цены по периодам» сохранена.", color="success", className="py-2 mb-0"),
        )
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-prices", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-prices", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-price", "n_clicks"),
    State(f"{PREFIX}-table-prices", "data"),
    State(f"{PREFIX}-table-prices", "selected_rows"),
    State(f"{PREFIX}-filter-price-period", "value"),
    State(f"{PREFIX}-filter-price-amount", "value"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_prices(n, data, selected_rows, period_filter, amount_filter, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid not in (None, "", "None"):
                    _delete_row_by_id(conn, "dn_service_price", cat, int(rid))
        return (
            _prices_matrix_filtered(cat, period_filter, amount_filter),
            [],
            dbc.Alert("Выбранные цены удалены (строки без записи в БД пропущены).", color="success", className="py-2 mb-0"),
        )
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-specs", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-specs", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-spec", "n_clicks"),
    State(f"{PREFIX}-table-specs", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_specs(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                conn.execute(
                    text("UPDATE dn_specialty SET name=:n, is_active=:ia WHERE id=:id AND catalog=:c"),
                    {
                        "n": str(row.get("name") or "").strip()[:256],
                        "ia": _as_int01(row.get("is_active")),
                        "id": int(rid),
                        "c": cat,
                    },
                )
        return _load_specs(cat), [], dbc.Alert("Таблица «Специальности» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-specs", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-specs", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-spec", "n_clicks"),
    State(f"{PREFIX}-table-specs", "data"),
    State(f"{PREFIX}-table-specs", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_specs(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_specialty", cat, int(rid))
        return _load_specs(cat), [], dbc.Alert("Выбранные специальности удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-cats", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-cats", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-cat", "n_clicks"),
    State(f"{PREFIX}-table-cats", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_cats(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                conn.execute(
                    text("UPDATE dn_diagnosis_category SET name=:n, is_active=:ia WHERE id=:id AND catalog=:c"),
                    {
                        "n": str(row.get("name") or "").strip()[:256],
                        "ia": _as_int01(row.get("is_active")),
                        "id": int(rid),
                        "c": cat,
                    },
                )
        return _load_cats(cat), [], dbc.Alert("Таблица «Категории диагнозов» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-cats", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-cats", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-cat", "n_clicks"),
    State(f"{PREFIX}-table-cats", "data"),
    State(f"{PREFIX}-table-cats", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_cats(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_diagnosis_category", cat, int(rid))
        return _load_cats(cat), [], dbc.Alert("Выбранные категории удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-diags", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-diags", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-diag", "n_clicks"),
    State(f"{PREFIX}-table-diags", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_diags(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                dc = _norm_diag_code(row.get("code"))
                if not dc:
                    continue
                conn.execute(
                    text("UPDATE dn_diagnosis SET code=:code, is_active=:ia WHERE id=:id AND catalog=:c"),
                    {"code": dc, "ia": _as_int01(row.get("is_active")), "id": int(rid), "c": cat},
                )
        return _load_diags(cat), [], dbc.Alert("Таблица «Диагнозы» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-diags", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-diags", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-diag", "n_clicks"),
    State(f"{PREFIX}-table-diags", "data"),
    State(f"{PREFIX}-table-diags", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_diags(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_diagnosis", cat, int(rid))
        return _load_diags(cat), [], dbc.Alert("Выбранные диагнозы удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-grps", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-grps", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-grp", "n_clicks"),
    State(f"{PREFIX}-table-grps", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_grps(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                conn.execute(
                    text(
                        "UPDATE dn_diagnosis_group SET code=:code, title=:title, sort_order=:so, rule=:rule, is_active=:ia "
                        "WHERE id=:id AND catalog=:c"
                    ),
                    {
                        "code": str(row.get("code") or "").strip()[:256],
                        "title": str(row.get("title") or "").strip()[:255],
                        "so": _as_int_sort(row.get("sort_order")),
                        "rule": str(row.get("rule") or "").strip()[:2000],
                        "ia": _as_int01(row.get("is_active")),
                        "id": int(rid),
                        "c": cat,
                    },
                )
        return _load_grps(cat), [], dbc.Alert("Таблица «Группы диагнозов» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-grps", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-grps", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-grp", "n_clicks"),
    State(f"{PREFIX}-table-grps", "data"),
    State(f"{PREFIX}-table-grps", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_grps(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_diagnosis_group", cat, int(rid))
        return _load_grps(cat), [], dbc.Alert("Выбранные группы удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-reqs", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-reqs", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-save-req", "n_clicks"),
    State(f"{PREFIX}-table-reqs", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def save_table_reqs(n, data, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for row in data or []:
                rid = row.get("id")
                if rid is None:
                    continue
                conn.execute(
                    text("UPDATE dn_service_requirement SET is_required=:ir WHERE id=:id AND catalog=:c"),
                    {"ir": _as_int01(row.get("is_required")), "id": int(rid), "c": cat},
                )
        return _load_reqs(cat), [], dbc.Alert("Таблица «Требования услуг» сохранена.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-table-reqs", "data", allow_duplicate=True),
    Output(f"{PREFIX}-table-reqs", "selected_rows", allow_duplicate=True),
    Output(f"{PREFIX}-msg-edit", "children", allow_duplicate=True),
    Input(f"{PREFIX}-btn-del-sel-req", "n_clicks"),
    State(f"{PREFIX}-table-reqs", "data"),
    State(f"{PREFIX}-table-reqs", "selected_rows"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def del_table_reqs(n, data, selected_rows, unlocked):
    if not n or not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = "global"
    try:
        with _engine().begin() as conn:
            for idx in selected_rows or []:
                if idx is None or not data or idx >= len(data):
                    continue
                rid = data[idx].get("id")
                if rid is not None:
                    _delete_row_by_id(conn, "dn_service_requirement", cat, int(rid))
        return _load_reqs(cat), [], dbc.Alert("Выбранные требования удалены.", color="success", className="py-2 mb-0")
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Ошибка: {e}", color="danger", className="py-2 mb-0")


@app.callback(
    Output(f"{PREFIX}-msg-main", "children"),
    Input(f"{PREFIX}-btn-copy", "n_clicks"),
    Input(f"{PREFIX}-upload", "contents"),
    State(f"{PREFIX}-upload", "filename"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=False,
)
def ref_msg_main(n_copy, upload_contents, upload_name, unlocked):
    ctx = callback_context
    if not ctx.triggered:
        return ""
    tid = ctx.triggered[0]["prop_id"].split(".")[0]
    if tid == f"{PREFIX}-btn-copy" and n_copy:
        if not _can_edit_tables("global", unlocked):
            return dbc.Alert(
                "Включите режим правки эталона паролем в шапке, чтобы копировать global → user.",
                color="warning",
                className="py-2",
            )
        try:
            copy_global_to_user(_engine())
            return dbc.Alert("Скопировано в пользовательский справочник.", color="success", className="py-2")
        except Exception as e:
            return dbc.Alert(str(e), color="danger", className="py-2")
    if tid == f"{PREFIX}-upload" and upload_contents:
        if not _can_edit_tables("global", unlocked):
            return dbc.Alert(
                "Включите режим правки эталона паролем в шапке, чтобы импортировать JSON.",
                color="warning",
                className="py-2",
            )
        try:
            _ct, cs = upload_contents.split(",", 1)
            payload = json.loads(base64.b64decode(cs).decode("utf-8"))
            with _engine().begin() as conn:
                import_catalog(conn, payload, target_catalog="user")
            return dbc.Alert(f"Импорт выполнен ({upload_name or 'файл'}).", color="success", className="py-2")
        except Exception as e:
            return dbc.Alert(f"Ошибка импорта: {e}", color="danger", className="py-2")
    return ""


@app.callback(
    Output(f"{PREFIX}-download", "data"),
    Input(f"{PREFIX}-btn-export", "n_clicks"),
    State("dash-dn-active-catalog", "data"),
    State("dash-dn-global-unlocked", "data"),
    prevent_initial_call=True,
)
def ref_export_json(n, active_catalog, unlocked):
    if not n:
        raise PreventUpdate
    if not _can_edit_tables("global", unlocked):
        raise PreventUpdate
    cat = active_catalog if active_catalog in ("global", "user") else "global"
    with _engine().connect() as conn:
        payload = export_catalog(conn, cat)
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    name = f"dn_catalog_{cat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return dcc.send_bytes(lambda b: b.write(raw), name)
