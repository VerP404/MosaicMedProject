"""Вкладка «Исправление талонов»: сверка услуг с матрицей и ZIP для BrowserAuto."""

from __future__ import annotations

import base64
from calendar import monthrange
from datetime import date, datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dash_table, dcc, html, no_update
from dash.dcc import send_bytes
from dash.exceptions import PreventUpdate

from apps.analytical_app.query_executor import engine
from apps.dn_matrix.runtime import ensure_django

EDITABLE_STATUS_DEFAULT = ["1", "5", "6", "7", "8", "18", "19"]
STATUS_OPTIONS = [
    {"label": "1", "value": "1"},
    {"label": "2", "value": "2"},
    {"label": "3", "value": "3"},
    {"label": "4", "value": "4"},
    {"label": "5", "value": "5"},
    {"label": "6", "value": "6"},
    {"label": "7", "value": "7"},
    {"label": "8", "value": "8"},
    {"label": "12", "value": "12"},
    {"label": "18", "value": "18"},
    {"label": "19", "value": "19"},
]


def _month_bounds(today: date | None = None) -> tuple[date, date]:
    day = today or date.today()
    return date(day.year, day.month, 1), date(day.year, day.month, monthrange(day.year, day.month)[1])


def _parse_iso_date(raw) -> date | None:
    if not raw:
        return None
    text = str(raw)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _decode_upload(contents: str) -> bytes:
    if not contents:
        return b""
    if "base64," in contents:
        return base64.b64decode(contents.split("base64,", 1)[1])
    return base64.b64decode(contents)


def _status_alert(text: str, *, danger: bool) -> html.Div:
    klass = "alert alert-danger py-2 mb-0" if danger else "alert alert-success py-2 mb-0"
    return html.Div(text, className=klass)


def _table(df: pd.DataFrame, table_id: str, *, page_size: int = 20) -> dash_table.DataTable:
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
        style_data_conditional=[
            {
                "if": {"filter_query": '{Исправить} = "да"'},
                "backgroundColor": "#e8f5e9",
            }
        ],
    )


def _file_status_text(file_store: dict | None) -> str:
    file_store = file_store or {}
    if file_store.get("error"):
        return str(file_store["error"])
    name = file_store.get("filename") or ""
    if file_store.get("contents"):
        return f"Файл услуг «{name}» загружен. Нажмите «Сверить»."
    return "Загрузите detail_services (CSV/Excel из Web.ОМС → Услуги)."


def fix_upload_panel(type_page: str, file_store: dict | None = None) -> html.Div:
    """Upload вне dcc.Loading: иначе смена вкладки/спиннер глотает файл."""
    return html.Div(
        id=f"fix-upload-panel-{type_page}",
        style={"display": "none"},
        className="mb-3",
        children=[
            html.H6("Файл услуг (detail_services)", className="mb-2"),
            html.P(
                "Выгрузка Web.ОМС: Услуги. Нужны колонки «Талон», «Код услуги»; "
                "даты начала/окончания, количество, врач — если есть. "
                "Строки с суммой 0 пропускаются. Журнал талонов и ИСЗЛ берутся из базы.",
                className="text-muted small mb-2",
            ),
            dcc.Upload(
                id=f"upload-fix-{type_page}",
                children=html.Div(
                    [
                        html.I(className="bi bi-cloud-upload me-2"),
                        "Перетащите CSV/Excel detail_services или нажмите для выбора",
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
                id=f"fix-file-status-{type_page}",
                className="text-muted small mt-2",
                children=_file_status_text(file_store),
            ),
        ],
    )


def render_fix_tab(type_page: str, store: dict | None, file_store: dict | None, report_store: dict | None) -> html.Div:
    ensure_django()
    from apps.dn_matrix.services.workspace import edition_options

    start, end = _month_bounds()
    editions = [{"label": "По дате окончания талона", "value": "auto"}] + edition_options()
    preview = pd.DataFrame((report_store or {}).get("preview") or [])
    status_text = (report_store or {}).get("status") or (
        "Журнал и ИСЗЛ — из базы. Загрузите файл услуг, укажите даты окончания лечения и нажмите «Сверить»."
    )

    return html.Div(
        [
            html.P(
                "Первый режим: исправление услуг. Сверяем факт из файла с матрицей "
                "(DS1 журнала, DS2 = журнал + ИСЗЛ, которые можно вести по этой специальности). "
                "Пакет — два Excel в ZIP для BrowserAuto/исправление_услуг: "
                "в колонке «Талон» номер из журнала WEB.ОМС (тот же в шапке и в услугах), "
                "колонка «талон_омс» дублирует его для открытия в Web.ОМС. "
                "Даты услуг не выдумываем: берём из детализации; для новых кодов — дата уже существующей услуги.",
                className="text-muted",
            ),
            dbc.RadioItems(
                id=f"fix-mode-{type_page}",
                options=[{"label": "Исправление услуг", "value": "services"}],
                value="services",
                inline=True,
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Окончание лечения", className="fw-bold small"),
                            dcc.DatePickerRange(
                                id=f"fix-dates-{type_page}",
                                start_date=start.isoformat(),
                                end_date=end.isoformat(),
                                display_format="DD.MM.YYYY",
                                first_day_of_week=1,
                            ),
                            html.Div(
                                className="text-muted small",
                                children="Фильтр по дате окончания талона цели 3 в журнале WEB.ОМС.",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Подразделения", className="fw-bold small"),
                            dcc.Dropdown(
                                id=f"fix-dept-{type_page}",
                                options=[],
                                multi=True,
                                placeholder="Все подразделения",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Статусы", className="fw-bold small"),
                            dcc.Dropdown(
                                id=f"fix-status-filter-{type_page}",
                                options=STATUS_OPTIONS,
                                value=list(EDITABLE_STATUS_DEFAULT),
                                multi=True,
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
                            html.Label("Редакция матрицы", className="fw-bold small"),
                            dcc.Dropdown(
                                id=f"fix-edition-{type_page}",
                                options=editions,
                                value="auto",
                                clearable=False,
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label(" ", className="fw-bold small d-block"),
                            html.Button(
                                "Сверить",
                                id=f"btn-fix-run-{type_page}",
                                className="btn btn-primary me-2",
                            ),
                            html.Button(
                                "Скачать пакет",
                                id=f"btn-fix-download-{type_page}",
                                className="btn btn-success",
                            ),
                        ],
                        md=8,
                    ),
                ],
                className="mb-3 g-2 align-items-end",
            ),
            html.Div(id=f"fix-run-msg-{type_page}", className="small mb-3", children=_status_alert(status_text, danger=False)),
            html.H6("Сверка"),
            html.P(
                "«Исправить = да» — расхождение, выбранный статус, есть ожидаемые услуги. "
                "В пакет попадают только такие строки. "
                "Если «Факт» = «нет в файле», этого талона нет в CSV: «Недостаёт» тогда равен всей матрице. "
                "DS2 — сопутствующие из журнала (полный МКБ, без усечения I11.9→I11). "
                "«DS2 журнал+ИСЗЛ» — то, по чему считаются услуги и что уйдёт в Excel. "
                "Это не дубль колонок. Даты талона и услуг в Excel — как в журнале/файле.",
                className="text-muted small",
            ),
            _table(preview, f"tbl-fix-{type_page}", page_size=25),
        ]
    )


def register_fix_callbacks(app, type_page: str) -> None:
    @app.callback(
        Output(f"fix-upload-panel-{type_page}", "style"),
        Input(f"tabs-{type_page}", "active_tab"),
    )
    def toggle_fix_upload_panel(tab):
        if tab == "tab-fix":
            return {"display": "block", "marginTop": "12px", "marginBottom": "8px"}
        return {"display": "none"}

    @app.callback(
        Output(f"store-fix-file-{type_page}", "data"),
        Output(f"fix-file-status-{type_page}", "children"),
        Input(f"upload-fix-{type_page}", "contents"),
        State(f"upload-fix-{type_page}", "filename"),
        prevent_initial_call=True,
    )
    def keep_fix_file(contents, filename):
        if not contents:
            raise PreventUpdate
        payload = {"filename": filename or "", "contents": contents}
        return payload, _file_status_text(payload)

    @app.callback(
        Output(f"fix-dept-{type_page}", "options"),
        Input(f"tabs-{type_page}", "active_tab"),
        Input(f"dropdown-year-{type_page}", "value"),
        State(f"store-{type_page}", "data"),
    )
    def load_fix_departments(tab, year, store):
        if tab != "tab-fix":
            raise PreventUpdate
        ensure_django()
        from sqlalchemy import text

        from apps.analytical_app.pages.head.dn.query import sql_goal3_talon_departments

        year = int(year or (store or {}).get("year") or datetime.now().year)
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(sql_goal3_talon_departments(year))).fetchall()
            return [{"label": r[0], "value": r[0]} for r in rows]
        except Exception:
            return []

    @app.callback(
        Output(f"store-fix-report-{type_page}", "data"),
        Output(f"tbl-fix-{type_page}", "columns"),
        Output(f"tbl-fix-{type_page}", "data"),
        Output(f"fix-run-msg-{type_page}", "children"),
        Input(f"btn-fix-run-{type_page}", "n_clicks"),
        State(f"store-fix-file-{type_page}", "data"),
        State(f"fix-dates-{type_page}", "start_date"),
        State(f"fix-dates-{type_page}", "end_date"),
        State(f"fix-dept-{type_page}", "value"),
        State(f"fix-status-filter-{type_page}", "value"),
        State(f"fix-edition-{type_page}", "value"),
        State(f"dropdown-year-{type_page}", "value"),
        prevent_initial_call=True,
    )
    def run_fix(
        n_clicks,
        file_store,
        start_date,
        end_date,
        departments,
        statuses,
        edition_id,
        year,
    ):
        if not n_clicks:
            raise PreventUpdate
        ensure_django()
        from apps.dn_matrix.services.ticket_fix import run_service_fix_report, tickets_to_store

        file_store = file_store or {}
        contents = file_store.get("contents")
        if not contents:
            empty = [{"name": "Сообщение", "id": "Сообщение"}]
            data = [{"Сообщение": "нет данных"}]
            return no_update, empty, data, _status_alert("Сначала загрузите файл услуг.", danger=True)

        date_from = _parse_iso_date(start_date)
        date_to = _parse_iso_date(end_date)
        if not date_from or not date_to:
            empty = [{"name": "Сообщение", "id": "Сообщение"}]
            return no_update, empty, [{"Сообщение": "нет данных"}], _status_alert("Укажите интервал дат.", danger=True)
        if date_to < date_from:
            empty = [{"name": "Сообщение", "id": "Сообщение"}]
            return no_update, empty, [{"Сообщение": "нет данных"}], _status_alert(
                "Дата окончания раньше начала.", danger=True
            )

        year = int(year or datetime.now().year)
        ed = None if edition_id in (None, "", "auto") else int(edition_id)
        status_list = [str(s).strip() for s in (statuses or []) if str(s).strip()]
        if not status_list:
            empty = [{"name": "Сообщение", "id": "Сообщение"}]
            return no_update, empty, [{"Сообщение": "нет данных"}], _status_alert(
                "Выберите хотя бы один статус.", danger=True
            )
        try:
            tickets, preview, warnings = run_service_fix_report(
                engine,
                year=year,
                date_from=date_from,
                date_to=date_to,
                departments=list(departments or []) or None,
                statuses=status_list,
                detail_bytes=_decode_upload(contents),
                detail_filename=file_store.get("filename") or "",
                edition_id=ed,
            )
        except Exception as exc:
            empty = [{"name": "Сообщение", "id": "Сообщение"}]
            return no_update, empty, [{"Сообщение": "нет данных"}], _status_alert(f"Ошибка сверки: {exc}", danger=True)

        status = " ".join(warnings) if warnings else "Сверка выполнена."
        payload = {
            "tickets": tickets_to_store(tickets),
            "preview": preview,
            "status": status,
        }
        if preview:
            cols = [{"name": str(c), "id": str(c)} for c in preview[0].keys()]
            data = [{k: "" if v is None else str(v) for k, v in row.items()} for row in preview]
        else:
            cols = [{"name": "Сообщение", "id": "Сообщение"}]
            data = [{"Сообщение": "нет данных"}]
        danger = not tickets or not any(t.fixable for t in tickets)
        return payload, cols, data, _status_alert(status, danger=danger)

    @app.callback(
        Output(f"download-fix-{type_page}", "data"),
        Output(f"fix-run-msg-{type_page}", "children", allow_duplicate=True),
        Input(f"btn-fix-download-{type_page}", "n_clicks"),
        State(f"store-fix-report-{type_page}", "data"),
        prevent_initial_call=True,
    )
    def download_fix(n_clicks, report_store):
        if not n_clicks:
            raise PreventUpdate
        ensure_django()
        from apps.dn_matrix.services.ticket_fix import build_fix_export_zip, tickets_from_store

        tickets = tickets_from_store((report_store or {}).get("tickets") or [])
        if not tickets:
            return no_update, _status_alert("Сначала нажмите «Сверить».", danger=True)
        try:
            zip_bytes, stamp = build_fix_export_zip(tickets, only_fixable=True)
        except ValueError as exc:
            return no_update, _status_alert(str(exc), danger=True)
        except Exception as exc:
            return no_update, _status_alert(f"Ошибка пакета: {exc}", danger=True)
        n = sum(1 for t in tickets if t.fixable)
        return send_bytes(zip_bytes, f"dn_fix_services_{stamp}.zip"), _status_alert(
            f"Пакет: {n} талонов для BrowserAuto (исправление услуг).",
            danger=False,
        )
