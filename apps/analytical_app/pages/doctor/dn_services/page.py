from dash import Input, Output, State, callback_context, dcc, html
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.elements import card_table
from apps.analytical_app.query_executor import engine
from apps.analytical_app.pages.doctor.dn_services.query import (
    diagnoses_for_specialty_query,
    diagnoses_options_query,
    services_for_diagnoses_query,
    specialties_options_query,
    specialties_for_diagnosis_query,
)


type_page = "doctor-dn-services"


def _fetch_options(query, params=None):
    with engine.connect() as connection:
        rows = connection.execute(query, params or {}).fetchall()
    return [{"label": row[1], "value": row[0]} for row in rows]


initial_diagnosis_options = _fetch_options(diagnoses_options_query())
initial_specialty_options = _fetch_options(specialties_options_query())


doctor_dn_services = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Подбор услуг ДН"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Основной диагноз", className="fw-bold mb-2"),
                                            dcc.Dropdown(
                                                id=f"dropdown-main-diagnosis-{type_page}",
                                                options=initial_diagnosis_options,
                                                placeholder="Выберите основной диагноз...",
                                                clearable=True,
                                                searchable=True,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Специальность", className="fw-bold mb-2"),
                                            dcc.Dropdown(
                                                id=f"dropdown-specialty-{type_page}",
                                                options=initial_specialty_options,
                                                placeholder="Выберите специальность...",
                                                clearable=True,
                                                searchable=True,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Сопутствующие диагнозы", className="fw-bold mb-2"),
                                            dcc.Dropdown(
                                                id=f"dropdown-additional-diagnoses-{type_page}",
                                                options=[],
                                                placeholder="Доступно после выбора специальности...",
                                                clearable=True,
                                                searchable=True,
                                                multi=True,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ]
                            ),
                            html.Hr(),
                            html.Div(
                                id=f"selection-summary-{type_page}",
                                className="selected-filters-block",
                                style={
                                    "margin": "10px 0 0 0",
                                    "padding": "10px",
                                    "border": "1px solid #ccc",
                                    "border-radius": "5px",
                                },
                            ),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "padding": "0rem",
                        "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                        "border-radius": "10px",
                    },
                ),
                width=12,
            ),
            style={"margin": "0 auto", "padding": "0rem"},
        ),
        html.Br(),
        card_table(
            f"result-table-{type_page}",
            "Услуги при проведении диспансерного наблюдения",
            page_size=20,
        ),
    ],
    style={"padding": "0rem"},
)


@app.callback(
    Output(f"dropdown-main-diagnosis-{type_page}", "options"),
    Output(f"dropdown-main-diagnosis-{type_page}", "value"),
    Output(f"dropdown-specialty-{type_page}", "options"),
    Output(f"dropdown-specialty-{type_page}", "value"),
    Input(f"dropdown-main-diagnosis-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
)
def sync_main_diagnosis_and_specialty(main_diagnosis, specialty_name):
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    diagnosis_options = initial_diagnosis_options
    specialty_options = initial_specialty_options

    if main_diagnosis and specialty_name:
        diagnosis_options = _fetch_options(
            diagnoses_for_specialty_query(),
            {"specialty_name": specialty_name},
        )
        specialty_options = _fetch_options(
            specialties_for_diagnosis_query(),
            {"diagnosis_code": main_diagnosis},
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
            diagnoses_for_specialty_query(),
            {"specialty_name": specialty_name},
        )
        diagnosis_values = {opt["value"] for opt in diagnosis_options}
        if main_diagnosis not in diagnosis_values:
            main_diagnosis = None
        return diagnosis_options, main_diagnosis, specialty_options, specialty_name

    if triggered == f"dropdown-main-diagnosis-{type_page}" and main_diagnosis:
        specialty_options = _fetch_options(
            specialties_for_diagnosis_query(),
            {"diagnosis_code": main_diagnosis},
        )
        specialty_values = {opt["value"] for opt in specialty_options}
        if specialty_name not in specialty_values:
            specialty_name = None
        return diagnosis_options, main_diagnosis, specialty_options, specialty_name

    return diagnosis_options, main_diagnosis, specialty_options, specialty_name


@app.callback(
    Output(f"dropdown-additional-diagnoses-{type_page}", "options"),
    Output(f"dropdown-additional-diagnoses-{type_page}", "value"),
    Input(f"dropdown-specialty-{type_page}", "value"),
    State(f"dropdown-main-diagnosis-{type_page}", "value"),
)
def update_additional_diagnoses(specialty_name, main_diagnosis):
    if not specialty_name:
        return [], []
    options = _fetch_options(
        diagnoses_for_specialty_query(),
        {"specialty_name": specialty_name},
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
)
def show_dn_services(main_diagnosis, specialty_name, additional_diagnoses):
    if not main_diagnosis:
        return "Выберите основной диагноз.", [], []
    if not specialty_name:
        return "Выберите специальность для выбранного диагноза.", [], []

    diagnosis_codes = [main_diagnosis]
    if additional_diagnoses:
        diagnosis_codes.extend([code for code in additional_diagnoses if code and code != main_diagnosis])

    with engine.connect() as connection:
        rows = connection.execute(
            services_for_diagnoses_query(),
            {
                "specialty_name": specialty_name,
                "diagnosis_codes": diagnosis_codes,
            },
        ).fetchall()

    summary_parts = [
        html.Div([html.Strong("Основной диагноз: "), main_diagnosis]),
        html.Div([html.Strong("Специальность: "), specialty_name]),
    ]
    if len(diagnosis_codes) > 1:
        summary_parts.append(
            html.Div([html.Strong("Сопутствующие диагнозы: "), ", ".join(diagnosis_codes[1:])])
        )

    if not rows:
        summary_parts.append(html.Div("Для выбранной комбинации диагнозов и специальности услуги не найдены."))
        return summary_parts, [], []

    columns = [{"name": col, "id": col} for col in rows[0]._mapping.keys()]
    data = [dict(row._mapping) for row in rows]
    summary_parts.append(html.Div([html.Strong("Найдено услуг: "), str(len(data))]))
    total_cost = sum(
        float(row.get("Актуальная стоимость") or 0)
        for row in data
        if row.get("Актуальная стоимость") is not None
    )
    summary_parts.append(
        html.Div([html.Strong("Итоговая стоимость: "), f"{total_cost:,.2f}".replace(",", " ").replace(".", ",")])
    )
    return summary_parts, columns, data

