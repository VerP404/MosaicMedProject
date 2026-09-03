"""Вкладка простановки услуг ДН: файл или выбор непрошедших → ZIP из двух Excel."""

from __future__ import annotations

import base64
from datetime import date, datetime
from calendar import monthrange

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dash_table, dcc, html, no_update
from dash.dcc import send_bytes
from dash.exceptions import PreventUpdate

from apps.analytical_app.query_executor import engine
from apps.dn_matrix.runtime import ensure_django


def _month_bounds(today: date | None = None) -> tuple[date, date]:
    day = today or date.today()
    return date(day.year, day.month, 1), date(day.year, day.month, monthrange(day.year, day.month)[1])


def _table(df: pd.DataFrame, table_id: str, *, page_size: int = 20, selectable: str | bool = False) -> dash_table.DataTable:
    if df is None or df.empty:
        cols = [{"name": "Сообщение", "id": "Сообщение"}]
        data = [{"Сообщение": "нет данных"}]
    else:
        cols = [{"name": str(c), "id": str(c)} for c in df.columns]
        data = df.fillna("").astype(str).to_dict("records")
    if selectable == "multi":
        row_selectable = "multi"
    elif selectable:
        row_selectable = "single"
    else:
        row_selectable = False
    return dash_table.DataTable(
        id=table_id,
        columns=cols,
        data=data,
        page_size=page_size,
        filter_action="native",
        sort_action="native",
        row_selectable=row_selectable,
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": 12, "padding": "4px 8px", "textAlign": "left", "minWidth": 80},
        style_header={"fontWeight": "bold"},
    )


def _file_status_text(file_store: dict | None) -> str:
    file_store = file_store or {}
    rows = file_store.get("rows") or []
    name = file_store.get("filename") or ""
    warns = file_store.get("warnings") or []
    if file_store.get("error"):
        return str(file_store["error"])
    if not rows:
        if warns:
            return "Файл не загружен. " + " ".join(str(w) for w in warns[:3])
        return "Файл не загружен."
    head = f"Файл «{name}»: {len(rows)} строк с ЕНП."
    if warns:
        return head + " " + warns[0]
    return head


def bundle_upload_panel(type_page: str, file_store: dict | None = None) -> html.Div:
    """Upload вне dcc.Loading: иначе смена вкладки/спиннер глотает файл."""
    return html.Div(
        id=f"bundle-upload-panel-{type_page}",
        style={"display": "none"},
        className="mb-3",
        children=[
            html.H6("Файл для простановки", className="mb-2"),
            html.P(
                "Колонки: ЕНП, ds1, ds2 (необязательно), врач, корпус, Дата начала, Дата окончания. "
                "Даты вроде 06-07-26 допустимы. Если диагнозов нет — подставятся из непрошедших.",
                className="text-muted small mb-2",
            ),
            dcc.Upload(
                id=f"upload-bundle-{type_page}",
                children=html.Div(
                    [
                        html.I(className="bi bi-cloud-upload me-2"),
                        "Перетащите Excel/CSV или нажмите для выбора",
                    ]
                ),
                style={
                    "width": "100%",
                    "height": "72px",
                    "lineHeight": "70px",
                    "borderWidth": "2px",
                    "borderStyle": "dashed",
                    "borderRadius": "10px",
                    "textAlign": "center",
                    "cursor": "pointer",
                    "backgroundColor": "#f8f9fa",
                },
                multiple=False,
            ),
            html.Div(
                id=f"bundle-file-status-{type_page}",
                className="text-muted small mt-2",
                children=_file_status_text(file_store),
            ),
        ],
    )


def render_bundle_tab(type_page: str, store: dict | None, file_store: dict | None) -> html.Div:
    ensure_django()
    from apps.dn_matrix.services.workspace import default_edition, edition_options

    store = store or {}
    file_store = file_store or {}
    grouped_df = pd.DataFrame(store.get("not_passed_grouped") or [])
    start, end = _month_bounds()
    editions = edition_options()
    initial = default_edition()
    edition_value = initial.id if initial else None

    return html.Div(
        [
            html.P(
                "Два Excel в ZIP, как в портале: талоны и услуги, связь по колонке «Талон». "
                "Основной и сопутствующие диагнозы, категория по основному МКБ, услуги матрицы. "
                "Для диспансерного приёма «Кол-во» = число явок — задайте его до выгрузки.",
                className="text-muted",
            ),
            dbc.RadioItems(
                id=f"bundle-source-{type_page}",
                options=[
                    {"label": "Из файла (ЕНП, код врача, корпус, даты)", "value": "file"},
                    {"label": "Из непрошедших (отметить строки)", "value": "not_passed"},
                    {"label": "Из посетивших поликлинику (журнал обращений)", "value": "clinic"},
                ],
                value="file",
                inline=True,
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(id=f"bundle-dates-label-{type_page}", children="Интервал явок", className="fw-bold small"),
                            dcc.DatePickerRange(
                                id=f"bundle-dates-{type_page}",
                                start_date=start.isoformat(),
                                end_date=end.isoformat(),
                                display_format="DD.MM.YYYY",
                                first_day_of_week=1,
                            ),
                            html.Div(
                                id=f"bundle-dates-hint-{type_page}",
                                className="text-muted small",
                                children="Файл: даты из колонок. Непрошедшие — этот интервал. Посетившие — даты приёма в журнале, явки ДН = приём + 5 раб. дней.",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Явки (кол-во приёма врача)", className="fw-bold small"),
                            dcc.Dropdown(
                                id=f"bundle-visits-{type_page}",
                                options=[
                                    {"label": "1 явка", "value": 1},
                                    {"label": "2 явки", "value": 2},
                                    {"label": "3 явки", "value": 3},
                                ],
                                value=3,
                                clearable=False,
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.Label("Шаг явок", className="fw-bold small"),
                            dcc.Dropdown(
                                id=f"bundle-step-{type_page}",
                                options=[
                                    {"label": "Подряд (раб. дни)", "value": 1},
                                    {"label": "Через день", "value": 2},
                                ],
                                value=1,
                                clearable=False,
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.Label("Редакция матрицы", className="fw-bold small"),
                            dcc.Dropdown(
                                id=f"bundle-edition-{type_page}",
                                options=editions,
                                value=edition_value,
                                clearable=False,
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="mb-2 g-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Код врача (если нет в файле / списке)", className="fw-bold small"),
                            dcc.Input(
                                id=f"bundle-doctor-{type_page}",
                                type="text",
                                placeholder="12345",
                                className="form-control",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Корпус", className="fw-bold small"),
                            dcc.Input(
                                id=f"bundle-corpus-{type_page}",
                                type="text",
                                placeholder="Корпус",
                                className="form-control",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label(" ", className="fw-bold small d-block"),
                            html.Button(
                                "Скачать пакет (2 Excel в ZIP)",
                                id=f"btn-bundle-download-{type_page}",
                                className="btn btn-primary",
                            ),
                        ],
                        md=5,
                    ),
                ],
                className="mb-3 g-2 align-items-end",
            ),
            html.Div(id=f"bundle-status-{type_page}", className="small mb-3"),
            html.Div(
                id=f"bundle-clinic-panel-{type_page}",
                style={"display": "none"},
                className="mb-3",
                children=[
                    html.H6("Посетившие поликлинику"),
                    html.P(
                        "Номер и дата приёма — из журнала обращений. "
                        "Если по группе диагнозов 168н уже есть талон цели 3 в статусах "
                        "1,2,3,4,5,6,7,8,12,18,19 — строка не нужна. "
                        "Явки: дата приёма + 5 рабочих дней, шаг как в поле выше, "
                        "без пересечения с датами журнала этого пациента.",
                        className="text-muted small",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Подразделения журнала", className="fw-bold small"),
                                    dcc.Dropdown(
                                        id=f"bundle-dept-{type_page}",
                                        options=[],
                                        multi=True,
                                        placeholder="Все подразделения",
                                    ),
                                ],
                                md=8,
                            ),
                            dbc.Col(
                                [
                                    html.Label(" ", className="fw-bold small d-block"),
                                    html.Button(
                                        "Показать посетивших",
                                        id=f"btn-bundle-clinic-{type_page}",
                                        className="btn btn-outline-primary",
                                    ),
                                ],
                                md=4,
                            ),
                        ],
                        className="mb-2 g-2 align-items-end",
                    ),
                    html.Div(id=f"bundle-clinic-status-{type_page}", className="text-muted small mb-2"),
                    _table(pd.DataFrame(), f"tbl-bundle-clinic-{type_page}", page_size=20, selectable="multi"),
                ],
            ),
            html.Div(
                id=f"bundle-np-panel-{type_page}",
                children=[
                    html.P(
                        "Файл загружается блоком над формой (ЕНП, ds1/ds2, врач, корпус, даты). "
                        "Ниже можно дополнительно отметить непрошедших.",
                        className="text-muted small",
                    ),
                    html.H6("Не прошедшие (по пациенту и профилю)"),
                    html.P(
                        "Отметьте строки чекбоксами. Если ничего не отмечено — в пакет пойдут все строки списка. "
                        "Нужно сначала нажать «Получить данные». Код врача, корпус и даты — поля выше "
                        "(в непрошедших обычно нет кода врача и периода талона).",
                        className="text-muted small",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Button(
                                    "Отметить все",
                                    id=f"btn-bundle-select-all-{type_page}",
                                    className="btn btn-outline-secondary btn-sm",
                                ),
                                width="auto",
                            ),
                            dbc.Col(
                                html.Button(
                                    "Снять отметки",
                                    id=f"btn-bundle-clear-{type_page}",
                                    className="btn btn-outline-secondary btn-sm",
                                ),
                                width="auto",
                            ),
                        ],
                        className="mb-2 g-2",
                    ),
                    _table(grouped_df, f"tbl-bundle-np-{type_page}", page_size=20, selectable="multi"),
                ],
            ),
        ]
    )


def _decode_upload(contents: str) -> bytes:
    if not contents:
        return b""
    if "base64," in contents:
        return base64.b64decode(contents.split("base64,", 1)[1])
    return base64.b64decode(contents)


def _parse_iso_date(raw) -> date | None:
    if not raw:
        return None
    text = str(raw)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def register_bundle_callbacks(app, type_page: str) -> None:
    @app.callback(
        Output(f"store-bundle-source-{type_page}", "data"),
        Input(f"bundle-source-{type_page}", "value"),
    )
    def sync_bundle_source(source):
        return source or "file"

    @app.callback(
        Output(f"bundle-upload-panel-{type_page}", "style"),
        Input(f"tabs-{type_page}", "active_tab"),
        Input(f"store-bundle-source-{type_page}", "data"),
    )
    def toggle_bundle_upload_panel(tab, source):
        if tab == "tab-bundle" and (source or "file") == "file":
            return {"display": "block", "marginTop": "12px", "marginBottom": "8px"}
        return {"display": "none"}

    @app.callback(
        Output(f"bundle-clinic-panel-{type_page}", "style"),
        Output(f"bundle-np-panel-{type_page}", "style"),
        Output(f"bundle-dates-label-{type_page}", "children"),
        Output(f"bundle-dates-hint-{type_page}", "children"),
        Input(f"bundle-source-{type_page}", "value"),
    )
    def toggle_bundle_source_panels(source):
        if source == "clinic":
            return (
                {"display": "block"},
                {"display": "none"},
                "Даты приёма в журнале",
                "Явки ДН: дата приёма + 5 рабочих дней, затем шаг из поля «Шаг явок». "
                "Даты из журнала этого пациента пропускаются.",
            )
        if source == "not_passed":
            return (
                {"display": "none"},
                {"display": "block"},
                "Интервал явок",
                "Непрошедшие: явки случайно внутри этого интервала.",
            )
        return (
            {"display": "none"},
            {"display": "block"},
            "Интервал явок",
            "Файл: даты из колонок, если пусто — этот интервал.",
        )

    @app.callback(
        Output(f"bundle-dept-{type_page}", "options"),
        Input(f"tabs-{type_page}", "active_tab"),
        Input(f"bundle-source-{type_page}", "value"),
    )
    def load_bundle_departments(tab, source):
        if tab != "tab-bundle" or source != "clinic":
            raise PreventUpdate
        ensure_django()
        from sqlalchemy import text

        from apps.analytical_app.pages.head.dn.query import sql_journal_departments

        try:
            with engine.connect() as conn:
                rows = conn.execute(text(sql_journal_departments())).fetchall()
            return [{"label": r[0], "value": r[0]} for r in rows]
        except Exception:
            return []

    @app.callback(
        Output(f"tbl-bundle-clinic-{type_page}", "columns"),
        Output(f"tbl-bundle-clinic-{type_page}", "data"),
        Output(f"bundle-clinic-status-{type_page}", "children"),
        Input(f"btn-bundle-clinic-{type_page}", "n_clicks"),
        State(f"bundle-dates-{type_page}", "start_date"),
        State(f"bundle-dates-{type_page}", "end_date"),
        State(f"bundle-dept-{type_page}", "value"),
        State(f"bundle-doctor-{type_page}", "value"),
        State(f"bundle-corpus-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        State(f"filter-cat-{type_page}", "value"),
        State(f"filter-profile-{type_page}", "value"),
        prevent_initial_call=True,
    )
    def preview_clinic_visitors(
        n_clicks,
        start_date,
        end_date,
        departments,
        doctor,
        corpus,
        year,
        category,
        profile,
    ):
        if not n_clicks:
            raise PreventUpdate
        date_from = _parse_iso_date(start_date)
        date_to = _parse_iso_date(end_date)
        if not date_from or not date_to:
            return [], [], "Укажите даты приёма."
        if date_to < date_from:
            return [], [], "Дата окончания раньше начала."
        ensure_django()
        from apps.dn_matrix.services.journal_visitors import fetch_clinic_visitors

        try:
            _items, preview, warnings = fetch_clinic_visitors(
                engine,
                year=int(year or datetime.now().year),
                date_from=date_from,
                date_to=date_to,
                departments=list(departments or []),
                default_doctor=(doctor or "").strip(),
                default_corpus=(corpus or "").strip(),
                category=category or "",
                profile=profile or "",
            )
        except Exception as exc:
            return [], [], f"Ошибка журнала: {exc}"
        df = pd.DataFrame(preview)
        if df.empty:
            cols = [{"name": "Сообщение", "id": "Сообщение"}]
            data = [{"Сообщение": "нет данных"}]
        else:
            cols = [{"name": str(c), "id": str(c)} for c in df.columns]
            data = df.fillna("").astype(str).to_dict("records")
        in_pack = sum(1 for r in preview if r.get("Статус") == "в пакет")
        msg = f"Найдено строк: {len(preview)}, в пакет: {in_pack}."
        if warnings:
            msg += " " + " ".join(warnings[:4])
        return cols, data, msg

    @app.callback(
        Output(f"store-bundle-file-{type_page}", "data"),
        Output(f"bundle-file-status-{type_page}", "children"),
        Input(f"upload-bundle-{type_page}", "contents"),
        State(f"upload-bundle-{type_page}", "filename"),
        prevent_initial_call=True,
    )
    def parse_bundle_file(contents, filename):
        if not contents:
            raise PreventUpdate
        ensure_django()
        from apps.dn_matrix.services.talon_bundle_input import parse_input_dataframe, read_upload_dataframe

        try:
            raw = _decode_upload(contents)
            df = read_upload_dataframe(raw, filename or "")
            rows, warnings = parse_input_dataframe(df)
        except Exception as exc:
            payload = {"filename": filename or "", "rows": [], "warnings": [str(exc)]}
            return payload, f"Не удалось прочитать файл: {exc}"
        payload = {"filename": filename or "", "rows": _serialize_file_rows(rows), "warnings": warnings}
        return payload, _file_status_text(payload)

    @app.callback(
        Output(f"tbl-bundle-np-{type_page}", "selected_rows"),
        Input(f"btn-bundle-select-all-{type_page}", "n_clicks"),
        Input(f"btn-bundle-clear-{type_page}", "n_clicks"),
        State(f"tbl-bundle-np-{type_page}", "data"),
        prevent_initial_call=True,
    )
    def toggle_bundle_selection(n_all, n_clear, data):
        from dash import ctx

        if ctx.triggered_id == f"btn-bundle-clear-{type_page}":
            return []
        if ctx.triggered_id == f"btn-bundle-select-all-{type_page}":
            return list(range(len(data or [])))
        raise PreventUpdate

    @app.callback(
        Output(f"download-bundle-{type_page}", "data"),
        Output(f"bundle-status-{type_page}", "children"),
        Input(f"btn-bundle-download-{type_page}", "n_clicks"),
        State(f"bundle-source-{type_page}", "value"),
        State(f"store-bundle-file-{type_page}", "data"),
        State(f"store-{type_page}", "data"),
        State(f"tbl-bundle-np-{type_page}", "data"),
        State(f"tbl-bundle-np-{type_page}", "selected_rows"),
        State(f"tbl-bundle-clinic-{type_page}", "data"),
        State(f"tbl-bundle-clinic-{type_page}", "selected_rows"),
        State(f"bundle-dept-{type_page}", "value"),
        State(f"bundle-dates-{type_page}", "start_date"),
        State(f"bundle-dates-{type_page}", "end_date"),
        State(f"bundle-visits-{type_page}", "value"),
        State(f"bundle-step-{type_page}", "value"),
        State(f"bundle-doctor-{type_page}", "value"),
        State(f"bundle-corpus-{type_page}", "value"),
        State(f"bundle-edition-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        State(f"filter-cat-{type_page}", "value"),
        State(f"filter-profile-{type_page}", "value"),
        prevent_initial_call=True,
    )
    def download_bundle(
        n_clicks,
        source,
        file_store,
        store,
        table_data,
        selected_rows,
        clinic_table,
        clinic_selected,
        departments,
        start_date,
        end_date,
        visits,
        visit_step,
        doctor,
        corpus,
        edition_id,
        year,
        category,
        profile,
    ):
        if not n_clicks:
            raise PreventUpdate
        ensure_django()
        from apps.dn_matrix.services.talon_bundle import (
            TalonBundleParams,
            build_talon_bundle,
            render_talon_bundle_zip,
        )
        from apps.dn_matrix.services.workspace import get_edition

        edition = get_edition(edition_id)
        if not edition:
            return no_update, _status_alert("Нет редакции матрицы. Сначала импортируйте JSON-пакет.", danger=True)

        date_from = _parse_iso_date(start_date)
        date_to = _parse_iso_date(end_date)
        if not date_from or not date_to:
            return no_update, _status_alert("Укажите интервал дат.", danger=True)
        if date_to < date_from:
            return no_update, _status_alert("Дата окончания раньше начала.", danger=True)

        doctor = (doctor or "").strip()
        corpus = (corpus or "").strip()
        visits = int(visits or 3)
        visit_step = int(visit_step or 1)
        year = int(year or datetime.now().year)
        store = store or {}
        warnings: list[str] = []

        try:
            if source == "file":
                items, warnings = _items_from_file(
                    file_store or {},
                    store,
                    year=year,
                    doctor=doctor,
                    corpus=corpus,
                    date_from=date_from,
                    date_to=date_to,
                )
            elif source == "clinic":
                items, warnings = _items_from_clinic(
                    year=year,
                    date_from=date_from,
                    date_to=date_to,
                    departments=list(departments or []),
                    doctor=doctor,
                    corpus=corpus,
                    category=category or "",
                    profile=profile or "",
                    preview_rows=clinic_table,
                    selected_rows=clinic_selected,
                )
            else:
                items, warnings = _items_from_selected(
                    store,
                    table_data,
                    selected_rows,
                    doctor=doctor,
                    corpus=corpus,
                    date_from=date_from,
                    date_to=date_to,
                )
        except Exception as exc:
            return no_update, _status_alert(f"Ошибка подготовки строк: {exc}", danger=True)

        if not items:
            return no_update, _status_alert("Нет строк для выгрузки. " + " ".join(warnings[:5]), danger=True)

        params = TalonBundleParams(
            date_from=date_from,
            date_to=date_to,
            visit_step=visit_step,
            visits=visits,
            edition=edition,
            header_defaults={"врач": doctor, "Корпус": corpus, "посещений в МО": str(visits)},
        )
        try:
            result = build_talon_bundle(items=items, params=params)
        except Exception as exc:
            return no_update, _status_alert(f"Ошибка сборки пакета: {exc}", danger=True)

        warnings.extend(result.get("warnings") or [])
        if not result.get("headers"):
            return no_update, _status_alert("Не удалось сформировать талоны. " + " ".join(warnings[:8]), danger=True)

        zip_bytes, stamp = render_talon_bundle_zip(
            headers=result["headers"],
            services=result["services"],
        )
        msg = (
            f"Готово: {result['talons_count']} талонов, {result['services_count']} услуг "
            f"(явок: {visits}, {edition.title})."
        )
        if warnings:
            shown = warnings[:8]
            more = f" Ещё {len(warnings) - 8}." if len(warnings) > 8 else ""
            msg += " Предупреждения: " + " ".join(shown) + more
        return send_bytes(zip_bytes, f"dn_talons_{stamp}.zip"), _status_alert(msg, danger=False)


def _serialize_file_rows(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        item = dict(row)
        if item.get("date_from"):
            item["date_from"] = item["date_from"].isoformat() if hasattr(item["date_from"], "isoformat") else item["date_from"]
        if item.get("date_to"):
            item["date_to"] = item["date_to"].isoformat() if hasattr(item["date_to"], "isoformat") else item["date_to"]
        if item.get("birth"):
            item["birth"] = item["birth"].isoformat() if hasattr(item["birth"], "isoformat") else item["birth"]
        out.append(item)
    return out


def _deserialize_file_rows(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows or []:
        item = dict(row)
        item["date_from"] = _parse_iso_date(item.get("date_from"))
        item["date_to"] = _parse_iso_date(item.get("date_to"))
        item["birth"] = _parse_iso_date(item.get("birth"))
        out.append(item)
    return out


def _items_from_file(file_store, store, *, year, doctor, corpus, date_from, date_to):
    from apps.analytical_app.pages.head.dn.services import build_not_passed_grouped_for_enps
    from apps.dn_matrix.services.talon_bundle import norm_enp
    from apps.dn_matrix.services.talon_bundle_input import enrich_file_rows_with_not_passed

    file_rows = _deserialize_file_rows((file_store or {}).get("rows") or [])
    warnings = list((file_store or {}).get("warnings") or [])
    if not file_rows:
        return [], ["Загрузите файл с ЕНП."]

    grouped = list((store or {}).get("not_passed_grouped") or [])
    have = {norm_enp(r.get("ЕНП") or r.get("enp")) for r in grouped}
    missing = [r["enp"] for r in file_rows if r.get("enp") and r["enp"] not in have and not r.get("ds1")]
    if missing:
        extra = build_not_passed_grouped_for_enps(engine, year, missing)
        if extra is not None and not extra.empty and "Ошибка" not in extra.columns:
            grouped.extend(extra.to_dict("records"))
        elif extra is not None and not extra.empty and "Ошибка" in extra.columns:
            warnings.append(str(extra.iloc[0].get("Ошибка") or "ошибка SQL непрошедших"))

    items, more = enrich_file_rows_with_not_passed(
        file_rows,
        grouped,
        grouped=True,
        default_doctor=doctor,
        default_corpus=corpus,
        default_date_from=date_from,
        default_date_to=date_to,
    )
    warnings.extend(more)
    return items, warnings


def _items_from_clinic(
    *,
    year,
    date_from,
    date_to,
    departments,
    doctor,
    corpus,
    category,
    profile,
    preview_rows,
    selected_rows,
):
    from apps.dn_matrix.services.journal_visitors import fetch_clinic_visitors
    from apps.dn_matrix.services.talon_bundle import norm_enp

    items, preview, warnings = fetch_clinic_visitors(
        engine,
        year=year,
        date_from=date_from,
        date_to=date_to,
        departments=departments,
        default_doctor=doctor,
        default_corpus=corpus,
        category=category,
        profile=profile,
    )
    if selected_rows and preview_rows:
        wanted = set()
        for idx in selected_rows:
            if 0 <= idx < len(preview_rows):
                row = preview_rows[idx]
                if str(row.get("Статус") or "") != "в пакет":
                    continue
                wanted.add((norm_enp(row.get("ЕНП")), str(row.get("Профиль") or ""), str(row.get("Основной МКБ") or "")))
        if wanted:
            items = [
                it
                for it in items
                if (norm_enp(it.enp), it.specialty or "", it.ds1 or "") in wanted
            ]
            if not items:
                warnings.append("Среди отмеченных нет строк «в пакет».")
    return items, warnings


def _items_from_selected(store, table_data, selected_rows, *, doctor, corpus, date_from, date_to):
    from apps.dn_matrix.services.talon_bundle_input import items_from_not_passed_rows

    grouped = list((store or {}).get("not_passed_grouped") or [])
    if selected_rows and table_data:
        rows = []
        for idx in selected_rows:
            if 0 <= idx < len(table_data):
                rows.append(table_data[idx])
    else:
        rows = grouped
    if not rows:
        return [], ["Нет непрошедших. Сначала «Получить данные», либо отметьте строки."]
    return items_from_not_passed_rows(
        rows,
        grouped=True,
        doctor=doctor,
        corpus=corpus,
        date_from=date_from,
        date_to=date_to,
    )


def _status_alert(text: str, *, danger: bool) -> html.Div:
    klass = "alert alert-danger py-2 mb-0" if danger else "alert alert-success py-2 mb-0"
    return html.Div(text, className=klass)
