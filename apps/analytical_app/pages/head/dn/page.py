# apps/analytical_app/pages/head/dn/page.py
"""ДН как ИСЗЛ: карточка пациента + списки сверок (silver dn_app)."""
from __future__ import annotations

from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dash_table, dcc, html, no_update
from dash.dcc import send_bytes
from dash.exceptions import PreventUpdate

from apps.analytical_app.app import app
from apps.analytical_app.components.filters import filter_years
from apps.analytical_app.pages.head.dn.services import (
    build_dropped_diagnoses,
    build_etl_status,
    build_iszl_not_in_kvazar,
    build_kvazar_not_in_iszl,
    build_kvazar_stats,
    build_missing_prior,
    build_not_passed,
    build_not_passed_grouped,
    build_out_of_168n,
    build_summary,
    patient_card,
    patient_meta,
    search_patients,
)
from apps.analytical_app.query_executor import engine

type_page = "head-dn"

SEARCH_COLS = ["ЕНП", "ФИО", "Дата рождения", "Участок", "Откреплён"]


def _table(df: pd.DataFrame, table_id: str, page_size: int = 25, selectable: bool = False) -> dash_table.DataTable:
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
        row_selectable="single" if selectable else False,
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": 12, "padding": "4px 8px", "textAlign": "left", "minWidth": 80},
        style_header={"fontWeight": "bold"},
    )


def _metric(title: str, value, subtitle: str = "") -> dbc.Col:
    body = [html.H4(str(value), className="mb-0"), html.P(title, className="mb-0 small")]
    if subtitle:
        body.append(html.P(subtitle, className="text-muted small mb-0"))
    return dbc.Col(dbc.Card(dbc.CardBody(body), className="h-100"), md=True)


head_dn = html.Div(
    [
        dcc.Store(id=f"store-{type_page}", storage_type="memory"),
        dcc.Store(id=f"store-enp-{type_page}", storage_type="memory"),
        dcc.Store(id=f"store-card-{type_page}", storage_type="memory"),
        dcc.Store(id=f"store-np-mode-{type_page}", data="detail", storage_type="memory"),
        dcc.Download(id=f"download-xlsx-{type_page}"),
        dbc.Row(
            [
                dbc.Col(
                    html.Button("Получить данные", id=f"btn-get-{type_page}", className="btn btn-primary"),
                    width="auto",
                ),
                dbc.Col(filter_years(type_page), width=1),
                dbc.Col(
                    dcc.Dropdown(
                        id=f"filter-cat-{type_page}",
                        options=[
                            {"label": "Все группы", "value": ""},
                            {"label": "БСК", "value": "БСК"},
                            {"label": "ОНКО", "value": "ОНКО"},
                            {"label": "СД", "value": "СД"},
                            {"label": "Прочие", "value": "Прочие"},
                        ],
                        value="",
                        clearable=False,
                        placeholder="Группа 168н",
                    ),
                    width=2,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id=f"filter-profile-{type_page}",
                        options=[
                            {"label": "Все профили", "value": ""},
                            {"label": "Терапия", "value": "Терапия"},
                        ],
                        value="",
                        clearable=False,
                    ),
                    width=2,
                ),
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
                        id=f"loading-status-{type_page}",
                        type="circle",
                        color="#0d6efd",
                        children=html.Div(
                            id=f"load-status-{type_page}",
                            className="text-muted",
                            children="Нажмите «Получить данные»",
                        ),
                    ),
                    width=True,
                ),
            ],
            align="center",
            className="mb-2",
        ),
        html.Div(
            id=f"loading-banner-{type_page}",
            className="alert alert-info py-2 mb-2",
            style={"display": "none"},
            children=[
                dbc.Spinner(size="sm", color="primary", spinner_class_name="me-2"),
                html.Span("Загрузка данных ИСЗЛ… это может занять минуту"),
            ],
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H6("Карточка пациента", className="mb-1"),
                    html.P(
                        "Поиск по ЕНП/ФИО → все диагнозы (ldwID), периоды и группа 168н; "
                        "есть ли в ИСЗЛ и Квазар; талоны ОМС текущего года; какие диагнозы ещё не закрыты.",
                        className="text-muted small mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Input(
                                    id=f"search-q-{type_page}",
                                    type="text",
                                    placeholder="ЕНП или ФИО (мин. 3 символа)",
                                    className="form-control",
                                    debounce=True,
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                html.Button("Найти", id=f"btn-search-{type_page}", className="btn btn-outline-secondary"),
                                width="auto",
                            ),
                            dbc.Col(
                                html.Button(
                                    "Excel карточки",
                                    id=f"btn-excel-card-{type_page}",
                                    className="btn btn-outline-success",
                                ),
                                width="auto",
                            ),
                        ],
                        align="center",
                    ),
                    dcc.Loading(
                        id=f"loading-search-{type_page}",
                        type="circle",
                        color="#0d6efd",
                        children=html.Div(
                            id=f"search-result-{type_page}",
                            className="mt-2",
                            children=_table(
                                pd.DataFrame(columns=SEARCH_COLS),
                                f"tbl-search-{type_page}",
                                page_size=10,
                                selectable=True,
                            ),
                        ),
                    ),
                    dcc.Loading(
                        id=f"loading-card-{type_page}",
                        type="circle",
                        color="#0d6efd",
                        children=html.Div(id=f"patient-card-{type_page}", className="mt-3"),
                    ),
                ]
            ),
            className="mb-3",
        ),
        dbc.Tabs(
            id=f"tabs-{type_page}",
            active_tab="tab-summary",
            children=[
                dbc.Tab(label="Сводка ИСЗЛ", tab_id="tab-summary"),
                dbc.Tab(label="Не прошедшие", tab_id="tab-not-passed"),
                dbc.Tab(label="Вне 168н → 305", tab_id="tab-305"),
                dbc.Tab(label="Нет в текущем / снять·внести", tab_id="tab-missing"),
                dbc.Tab(label="Квазар ↔ ИСЗЛ", tab_id="tab-kvazar"),
                dbc.Tab(label="Статус загрузки", tab_id="tab-status"),
            ],
        ),
        dcc.Loading(
            id=f"loading-tabs-{type_page}",
            type="default",
            color="#0d6efd",
            children=html.Div(id=f"tab-body-{type_page}", className="mt-3"),
        ),
    ]
)


@app.callback(
    Output(f"store-{type_page}", "data"),
    Output(f"load-status-{type_page}", "children"),
    Output(f"loading-banner-{type_page}", "style"),
    Output(f"btn-get-{type_page}", "disabled"),
    Input(f"btn-get-{type_page}", "n_clicks"),
    State(f"dropdown-year-{type_page}", "value"),
    State(f"filter-cat-{type_page}", "value"),
    State(f"filter-profile-{type_page}", "value"),
    prevent_initial_call=True,
)
def load_dn_data(n_clicks, year, category, profile):
    if not n_clicks:
        raise PreventUpdate
    year = int(year or datetime.now().year)
    hide_banner = {"display": "none"}
    try:
        summary = build_summary(engine, year)
        not_passed = build_not_passed(engine, year, category or "", profile or "")
        not_passed_grouped = build_not_passed_grouped(engine, year, category or "", profile or "")
        out168 = build_out_of_168n(engine, year)
        missing = build_missing_prior(engine, year)
        dropped = build_dropped_diagnoses(engine, year)
        kv_stats = build_kvazar_stats(engine, year)
        kv_only = build_kvazar_not_in_iszl(engine, year)
        iszl_only = build_iszl_not_in_kvazar(engine, year)
        logs = build_etl_status(engine)
        payload = {
            "year": year,
            "summary": summary,
            "not_passed": not_passed.to_dict("records") if not not_passed.empty else [],
            "not_passed_grouped": not_passed_grouped.to_dict("records") if not not_passed_grouped.empty else [],
            "out168": out168.to_dict("records") if not out168.empty else [],
            "missing": missing.to_dict("records") if not missing.empty else [],
            "dropped": dropped.to_dict("records") if not dropped.empty else [],
            "kv_stats": kv_stats,
            "kv_only": kv_only.to_dict("records") if not kv_only.empty else [],
            "iszl_only": iszl_only.to_dict("records") if not iszl_only.empty else [],
            "logs": logs.to_dict("records") if not logs.empty else [],
        }
        status = (
            f"ИСЗЛ {year}: {summary.get('iszl_diag_rows', 0)} диагнозов "
            f"({summary.get('iszl_enp', 0)} пациентов), "
            f"выполнено {summary.get('completed_rows', 0)} ({summary.get('pct_completed', 0)}%), "
            f"не прошедшие {summary.get('not_passed_rows', 0)}, "
            f"вне 168н {summary.get('out_of_168n', 0)}"
        )
        return payload, status, hide_banner, False
    except Exception as e:
        return no_update, f"Ошибка: {e}", hide_banner, False


# Сразу при клике — баннер и блокировка кнопки (пока сервер считает)
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        return [{"display": "block"}, true];
    }
    """,
    Output(f"loading-banner-{type_page}", "style", allow_duplicate=True),
    Output(f"btn-get-{type_page}", "disabled", allow_duplicate=True),
    Input(f"btn-get-{type_page}", "n_clicks"),
    prevent_initial_call=True,
)


@app.callback(
    Output(f"search-result-{type_page}", "children"),
    Output(f"store-enp-{type_page}", "data", allow_duplicate=True),
    Input(f"btn-search-{type_page}", "n_clicks"),
    State(f"search-q-{type_page}", "value"),
    prevent_initial_call=True,
)
def do_search(n, q):
    if not n:
        raise PreventUpdate
    df = search_patients(engine, q or "")
    if df.empty:
        return html.Div(
            [
                html.Div("Ничего не найдено", className="text-muted mb-1"),
                _table(pd.DataFrame(columns=SEARCH_COLS), f"tbl-search-{type_page}", page_size=10, selectable=True),
            ]
        ), None
    return _table(df, f"tbl-search-{type_page}", page_size=10, selectable=True), None


@app.callback(
    Output(f"store-enp-{type_page}", "data"),
    Output(f"store-card-{type_page}", "data"),
    Output(f"patient-card-{type_page}", "children"),
    Input(f"tbl-search-{type_page}", "selected_rows"),
    State(f"tbl-search-{type_page}", "data"),
    State(f"dropdown-year-{type_page}", "value"),
    prevent_initial_call=True,
)
def select_patient(selected, data, year):
    if not selected or not data:
        raise PreventUpdate
    row = data[selected[0]]
    enp = row.get("ЕНП") or row.get("enp")
    year = int(year or datetime.now().year)
    meta = patient_meta(engine, enp, year)
    card_df = patient_card(engine, enp, year)
    fio = meta.get("fio") or row.get("ФИО") or row.get("fio") or ""
    badges = dbc.Row(
        [
            dbc.Col(html.Span(f"ИСЗЛ ({year}): {'да' if meta.get('in_iszl_year') else 'нет'}", className="badge bg-primary me-1"), width="auto"),
            dbc.Col(html.Span(f"ИСЗЛ (все годы): {'да' if meta.get('in_iszl_any') else 'нет'}", className="badge bg-secondary me-1"), width="auto"),
            dbc.Col(html.Span(f"Квазар: {'да' if meta.get('in_kvazar') else 'нет'}", className="badge bg-info me-1"), width="auto"),
            dbc.Col(html.Span(f"Талонов ОМС в {year}: {meta.get('talons_year') or 0}", className="badge bg-success"), width="auto"),
        ],
        className="mb-2 g-1",
    )
    header = html.Div(
        [
            html.H6(f"{fio} · ЕНП {enp} · участок {meta.get('lpuuch') or row.get('Участок') or '—'}"),
            badges,
            html.P(
                "Строка = диагноз (ldwID). Месяц плана — последний в выбранном году. "
                "«В 168н» — код есть в справочнике 168н. "
                "«Статус»: есть ли диагноз в ИСЗЛ за год + есть ли талон ОМС. "
                "«Не пройден» = в плане ИСЗЛ, талона цели 3 нет. "
                "«Не закрыт» — нет даты снятия и нет прохождения.",
                className="text-muted small",
            ),
        ]
    )
    store_card = card_df.to_dict("records") if not card_df.empty else []
    return enp, {"year": year, "enp": enp, "fio": fio, "rows": store_card}, html.Div(
        [header, _table(card_df, f"tbl-card-{type_page}", page_size=30)]
    )


@app.callback(
    Output(f"tab-body-{type_page}", "children"),
    Input(f"tabs-{type_page}", "active_tab"),
    Input(f"store-{type_page}", "data"),
    State(f"store-np-mode-{type_page}", "data"),
)
def render_tab(active_tab, store, np_mode):
    store = store or {}
    year = store.get("year") or "—"
    np_mode = np_mode or "detail"

    if active_tab == "tab-summary":
        s = store.get("summary") or {}
        by_cat = pd.DataFrame(s.get("by_category") or [])
        cards = dbc.Row(
            [
                _metric("Диагнозов в ИСЗЛ", s.get("iszl_diag_rows", 0), f"год {year}, по ldwID (посл. месяц)"),
                _metric("Пациентов в ИСЗЛ", s.get("iszl_enp", 0), "уникальных ЕНП"),
                _metric("Выполнено (талон 3)", f"{s.get('pct_completed', 0)}%", f"{s.get('completed_rows', 0)} диагнозов"),
                _metric("Не прошедшие", s.get("not_passed_rows", 0), "168н без талона"),
                _metric("Вне 168н → 305", s.get("out_of_168n", 0), "контроль цели 305"),
            ],
            className="mb-3 g-2",
        )
        return html.Div(
            [
                cards,
                html.H6("По группам 168н (ИСЗЛ)"),
                _table(by_cat, f"tbl-cat-{type_page}"),
            ]
        )

    if active_tab == "tab-not-passed":
        grouped = np_mode == "grouped"
        df = pd.DataFrame(
            store.get("not_passed_grouped" if grouped else "not_passed") or []
        )
        hint = (
            "Строка = пациент + профиль. Другой профиль — отдельная строка. "
            "Основной МКБ по группе: БСК > ОНКО > СД > Прочие; рядом сопутствующие МКБ того же профиля. "
            "Excel — выбранный режим."
            if grouped
            else "Детальный список по каждому диагнозу (ldwID). Excel — текущий режим."
        )
        return html.Div(
            [
                html.P(
                    f"ИСЗЛ {year}: диагнозы 168н без талона цели 3. "
                    "Код МКБ один раз (в выгрузке ИСЗЛ название = код).",
                    className="text-muted",
                ),
                dbc.RadioItems(
                    id=f"np-mode-{type_page}",
                    options=[
                        {"label": "Детально (по диагнозу)", "value": "detail"},
                        {
                            "label": "По пациенту и профилю (основной + сопутствующие)",
                            "value": "grouped",
                        },
                    ],
                    value=np_mode,
                    inline=True,
                    className="mb-2",
                ),
                html.P(id=f"np-hint-{type_page}", className="text-muted small", children=hint),
                html.Div(
                    id=f"np-table-host-{type_page}",
                    children=_table(df, f"tbl-np-{type_page}"),
                ),
            ]
        )

    if active_tab == "tab-305":
        return html.Div(
            [
                html.P(
                    "МКБ вне справочника 168н (по последнему месяцу плана) — контроль подачи цели 305.",
                    className="text-muted",
                ),
                _table(pd.DataFrame(store.get("out168") or []), f"tbl-305-{type_page}"),
            ]
        )

    if active_tab == "tab-missing":
        return html.Div(
            [
                html.H6("Нет в текущем году"),
                html.P(
                    f"Пациенты, которые есть в ИСЗЛ за предыдущие годы, но отсутствуют в {year}. "
                    "Строки по диагнозу (ldwID).",
                    className="text-muted",
                ),
                _table(pd.DataFrame(store.get("missing") or []), f"tbl-miss-{type_page}"),
                html.H6("Снять / внести", className="mt-3"),
                html.P(
                    f"Пациент есть в ИСЗЛ {year}, но диагноз (ldwID), который был в предыдущие годы, "
                    "в текущем году отсутствует — проверить снятие в ИСЗЛ или внесение в план.",
                    className="text-muted",
                ),
                _table(pd.DataFrame(store.get("dropped") or []), f"tbl-drop-{type_page}"),
            ]
        )

    if active_tab == "tab-kvazar":
        st = store.get("kv_stats") or {}
        metrics = dbc.Row(
            [
                _metric("Пар в ИСЗЛ", st.get("iszl_pairs", 0)),
                _metric("Пар в Квазар", st.get("kvazar_pairs", 0)),
                _metric("Совпало пар", st.get("both_pairs", 0)),
                _metric("ИСЗЛ→Квазар", f"{st.get('pct_iszl_in_kvazar', 0)}%", "доля пар ИСЗЛ, найденных в Квазар"),
                _metric("Квазар→ИСЗЛ", f"{st.get('pct_kvazar_in_iszl', 0)}%", "доля пар Квазар, найденных в ИСЗЛ"),
                _metric("ЕНП пересечение", f"{st.get('pct_enp_overlap_iszl', 0)}% / {st.get('pct_enp_overlap_kvazar', 0)}%", "от ИСЗЛ / от Квазар"),
            ],
            className="mb-3 g-2",
        )
        return html.Div(
            [
                metrics,
                html.H6("Есть в Квазар, нет в ИСЗЛ"),
                _table(pd.DataFrame(store.get("kv_only") or []), f"tbl-kv-only-{type_page}"),
                html.H6("Есть в ИСЗЛ, нет в Квазар", className="mt-3"),
                html.P(
                    f"По плану ИСЗЛ {year} (ldwID, последний месяц). В таблице — группа 168н и участок.",
                    className="text-muted",
                ),
                _table(pd.DataFrame(store.get("iszl_only") or []), f"tbl-iszl-only-{type_page}"),
            ]
        )

    if active_tab == "tab-status":
        return _table(pd.DataFrame(store.get("logs") or []), f"tbl-log-{type_page}")

    return html.Div("Нажмите «Получить данные».")


@app.callback(
    Output(f"store-np-mode-{type_page}", "data"),
    Output(f"np-table-host-{type_page}", "children"),
    Output(f"np-hint-{type_page}", "children"),
    Input(f"np-mode-{type_page}", "value"),
    State(f"store-{type_page}", "data"),
    prevent_initial_call=True,
)
def switch_np_mode(mode, store):
    store = store or {}
    grouped = mode == "grouped"
    df = pd.DataFrame(store.get("not_passed_grouped" if grouped else "not_passed") or [])
    hint = (
        "Строка = пациент + профиль. Другой профиль — отдельная строка. "
        "Основной МКБ по группе: БСК > ОНКО > СД > Прочие; рядом сопутствующие МКБ того же профиля."
        if grouped
        else "Детальный список по каждому диагнозу (ldwID). Excel — текущий режим."
    )
    return mode or "detail", _table(df, f"tbl-np-{type_page}"), hint


def _sheets_from_store(store: dict, np_mode: str = "detail") -> dict[str, pd.DataFrame]:
    np_key = "not_passed_grouped" if np_mode == "grouped" else "not_passed"
    np_sheet = "Не прошедшие по пациенту" if np_mode == "grouped" else "Не прошедшие"
    return {
        np_sheet: pd.DataFrame(store.get(np_key) or []),
        "Вне 168н 305": pd.DataFrame(store.get("out168") or []),
        "Нет в текущем": pd.DataFrame(store.get("missing") or []),
        "Снять внести": pd.DataFrame(store.get("dropped") or []),
        "Квазар нет ИСЗЛ": pd.DataFrame(store.get("kv_only") or []),
        "ИСЗЛ нет Квазар": pd.DataFrame(store.get("iszl_only") or []),
        "Статус загрузки": pd.DataFrame(store.get("logs") or []),
    }


@app.callback(
    Output(f"download-xlsx-{type_page}", "data"),
    Input(f"btn-excel-{type_page}", "n_clicks"),
    Input(f"btn-excel-all-{type_page}", "n_clicks"),
    Input(f"btn-excel-card-{type_page}", "n_clicks"),
    State(f"store-{type_page}", "data"),
    State(f"store-card-{type_page}", "data"),
    State(f"tabs-{type_page}", "active_tab"),
    State(f"store-np-mode-{type_page}", "data"),
    prevent_initial_call=True,
)
def export_excel(n_tab, n_all, n_card, store, card_store, active_tab, np_mode):
    from dash import ctx

    if not ctx.triggered_id:
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

    year = (store or {}).get("year") or datetime.now().year
    np_mode = np_mode or "detail"

    if ctx.triggered_id == f"btn-excel-card-{type_page}":
        if not card_store or not card_store.get("rows"):
            raise PreventUpdate
        enp = card_store.get("enp") or "patient"
        sheets = {"Карточка": pd.DataFrame(card_store.get("rows") or [])}
        return send_bytes(lambda b: to_excel(b, sheets), f"dn_card_{enp}_{year}.xlsx")

    if not store:
        raise PreventUpdate
    all_sheets = _sheets_from_store(store, np_mode)
    np_sheet = "Не прошедшие по пациенту" if np_mode == "grouped" else "Не прошедшие"

    if ctx.triggered_id == f"btn-excel-all-{type_page}":
        # оба режима не прошедших
        sheets = dict(all_sheets)
        sheets["Не прошедшие детально"] = pd.DataFrame(store.get("not_passed") or [])
        sheets["Не прошедшие по пациенту"] = pd.DataFrame(store.get("not_passed_grouped") or [])
        sheets.pop("Не прошедшие", None)
        return send_bytes(lambda b: to_excel(b, sheets), f"dn_iszl_all_{year}.xlsx")

    tab_map = {
        "tab-not-passed": {np_sheet: all_sheets[np_sheet]},
        "tab-305": {"Вне 168н 305": all_sheets["Вне 168н 305"]},
        "tab-missing": {
            "Нет в текущем": all_sheets["Нет в текущем"],
            "Снять внести": all_sheets["Снять внести"],
        },
        "tab-kvazar": {
            "Квазар нет ИСЗЛ": all_sheets["Квазар нет ИСЗЛ"],
            "ИСЗЛ нет Квазар": all_sheets["ИСЗЛ нет Квазар"],
        },
        "tab-status": {"Статус загрузки": all_sheets["Статус загрузки"]},
        "tab-summary": {
            "По группам": pd.DataFrame((store.get("summary") or {}).get("by_category") or []),
        },
    }
    sheets = tab_map.get(active_tab) or all_sheets
    suffix = "grouped" if (active_tab == "tab-not-passed" and np_mode == "grouped") else active_tab
    return send_bytes(lambda b: to_excel(b, sheets), f"dn_iszl_{suffix}_{year}.xlsx")
