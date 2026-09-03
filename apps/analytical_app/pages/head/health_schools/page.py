# -*- coding: utf-8 -*-
"""Модуль «ведующего: школы здоровья, цель 307."""

from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dash_table, dcc, html
from dash.dcc import send_bytes
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import filter_years
from apps.dn_matrix.runtime import ensure_django

type_page = "head-hs"

TAB_KEYS = {
    "tab-summary": ("summary", "Сводка"),
    "tab-talons": ("talons", "Талоны 307"),
    "tab-period": ("too_soon", "Периодичность"),
    "tab-iszl": ("iszl_schools", "План ИСЗЛ"),
    "tab-due": ("due", "К проведению"),
    "tab-none": ("no_school", "Без школы"),
    "tab-catalog": ("catalog", "Справочник"),
}


def _table(df: pd.DataFrame, table_id: str, page_size: int = 25) -> dash_table.DataTable:
    if df is None or df.empty:
        cols = [{"name": "Сообщение", "id": "Сообщение"}]
        data = [{"Сообщение": "нет данных"}]
    else:
        cols = [{"name": str(c), "id": str(c)} for c in df.columns]
        data = df.fillna("").astype(str).to_dict("records")
    return dash_table.DataTable(
        id=table_id,
        columns=cols,
        data=data,
        page_size=page_size,
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": 12, "padding": "4px 8px", "textAlign": "left", "minWidth": 80},
        style_header={"fontWeight": "bold"},
    )


def _metric(title: str, value) -> dbc.Col:
    return dbc.Col(
        dbc.Card(dbc.CardBody([html.H4(str(value), className="mb-0"), html.P(title, className="mb-0 small")])),
        md=True,
    )


def _df_from_store(store: dict, key: str) -> pd.DataFrame:
    rows = (store or {}).get(key) or []
    return pd.DataFrame(rows)


head_health_schools = html.Div(
    [
        dcc.Store(id=f"store-{type_page}", storage_type="memory"),
        dcc.Download(id=f"download-xlsx-{type_page}"),
        dbc.Row(
            [
                dbc.Col(html.Button("Получить данные", id=f"btn-get-{type_page}", className="btn btn-primary"), width="auto"),
                dbc.Col(filter_years(type_page), width=2),
                dbc.Col(
                    html.Button("Excel (вкладка)", id=f"btn-excel-{type_page}", className="btn btn-success"),
                    width="auto",
                ),
                dbc.Col(
                    html.Button("Excel (всё)", id=f"btn-excel-all-{type_page}", className="btn btn-outline-success"),
                    width="auto",
                ),
                dbc.Col(
                    dcc.Loading(
                        type="circle",
                        children=html.Div(
                            id=f"load-status-{type_page}",
                            className="text-muted",
                            children="Нажмите «Получить данные». Справочник — в админке Django, периодичность по умолчанию 3 года.",
                        ),
                    ),
                    width=True,
                ),
            ],
            align="center",
            className="mb-3",
        ),
        html.P(
            "Цель 307: школа по справочнику МКБ, явки и код услуги, повтор не раньше периода школы, "
            "диагноз в плане ИСЗЛ на выбранный год. «К проведению» — план ИСЗЛ есть, курса 307 в периоде нет.",
            className="text-muted small",
        ),
        html.Div(id=f"metrics-{type_page}", className="mb-3"),
        dbc.Tabs(
            id=f"tabs-{type_page}",
            active_tab="tab-summary",
            children=[
                dbc.Tab(label="Сводка", tab_id="tab-summary"),
                dbc.Tab(label="Талоны 307", tab_id="tab-talons"),
                dbc.Tab(label="Периодичность", tab_id="tab-period"),
                dbc.Tab(label="План ИСЗЛ", tab_id="tab-iszl"),
                dbc.Tab(label="К проведению", tab_id="tab-due"),
                dbc.Tab(label="Без школы", tab_id="tab-none"),
                dbc.Tab(label="Справочник", tab_id="tab-catalog"),
            ],
        ),
        html.Div(id=f"tab-body-{type_page}", className="mt-3"),
    ]
)


@app.callback(
    Output(f"store-{type_page}", "data"),
    Output(f"load-status-{type_page}", "children"),
    Input(f"btn-get-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    prevent_initial_call=True,
)
def load_data(n_clicks, year):
    if not n_clicks:
        raise PreventUpdate
    ensure_django()
    from apps.health_schools.services.analysis import run_analysis

    y = int(year or datetime.now().year)
    result = run_analysis(y)

    def recs(df: pd.DataFrame) -> list:
        if df is None or df.empty:
            return []
        return df.fillna("").astype(str).to_dict("records")

    store = {
        "year": y,
        "counts": result["counts"],
        "summary": recs(result["summary"]),
        "talons": recs(result["talons"]),
        "too_soon": recs(result["too_soon"]),
        "no_school": recs(result["no_school"]),
        "iszl_schools": recs(result["iszl_schools"]),
        "due": recs(result["due"]),
        "catalog": recs(result["catalog"]),
    }
    c = result["counts"]
    status = (
        f"Год {y}: талонов 307 — {c['talons']}, рано повтор — {c['too_soon']}, "
        f"план ИСЗЛ×школа — {c['iszl']}, к проведению — {c['due']}, без школы — {c['no_school']}. "
        f"Справочник: {c['catalog']} школ."
    )
    return store, status


@app.callback(
    Output(f"metrics-{type_page}", "children"),
    Output(f"tab-body-{type_page}", "children"),
    Input(f"store-{type_page}", "data"),
    Input(f"tabs-{type_page}", "active_tab"),
)
def render_tab(store, active_tab):
    if not store:
        return html.Div(), html.P("Нет данных.", className="text-muted")
    c = store.get("counts") or {}
    metrics = dbc.Row(
        [
            _metric("Талоны 307", c.get("talons", 0)),
            _metric("Рано повтор", c.get("too_soon", 0)),
            _metric("План ИСЗЛ", c.get("iszl", 0)),
            _metric("К проведению", c.get("due", 0)),
            _metric("Без школы", c.get("no_school", 0)),
        ],
        className="g-2",
    )
    key, _title = TAB_KEYS.get(active_tab or "tab-summary", ("summary", "Сводка"))
    body = _table(_df_from_store(store, key), f"table-{type_page}-{key}")
    return metrics, body


@app.callback(
    Output(f"download-xlsx-{type_page}", "data"),
    Input(f"btn-excel-{type_page}", "n_clicks"),
    Input(f"btn-excel-all-{type_page}", "n_clicks"),
    State(f"store-{type_page}", "data"),
    State(f"tabs-{type_page}", "active_tab"),
    prevent_initial_call=True,
)
def export_excel(n_tab, n_all, store, active_tab):
    from dash import ctx

    if not ctx.triggered_id or not store:
        raise PreventUpdate

    def to_excel(buffer, sheets: dict):
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for name, df in sheets.items():
                sheet = str(name)[:31]
                if df is None or df.empty:
                    pd.DataFrame({"Сообщение": ["нет данных"]}).to_excel(writer, sheet_name=sheet, index=False)
                else:
                    df.to_excel(writer, sheet_name=sheet, index=False)
        buffer.seek(0)

    year = store.get("year") or datetime.now().year
    all_sheets = {title: _df_from_store(store, key) for key, title in (
        ("summary", "Сводка"),
        ("talons", "Талоны 307"),
        ("too_soon", "Периодичность"),
        ("iszl_schools", "План ИСЗЛ"),
        ("due", "К проведению"),
        ("no_school", "Без школы"),
        ("catalog", "Справочник"),
    )}
    if ctx.triggered_id == f"btn-excel-all-{type_page}":
        return send_bytes(lambda b: to_excel(b, all_sheets), f"health_schools_{year}.xlsx")
    key, title = TAB_KEYS.get(active_tab or "tab-summary", ("summary", "Сводка"))
    return send_bytes(lambda b: to_excel(b, {title: _df_from_store(store, key)}), f"health_schools_{key}_{year}.xlsx")
