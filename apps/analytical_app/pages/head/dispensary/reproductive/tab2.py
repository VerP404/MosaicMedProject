from dash import html, Output, Input, State, dcc, exceptions
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.components.filters import filter_years, update_buttons
from apps.analytical_app.elements import card_table
from apps.analytical_app.pages.head.dispensary.reproductive.query import  sql_query_reproductive_building_department
from apps.analytical_app.query_executor import engine

type_page = "tab2-dr"

reproductive_dr2 = html.Div(
    [
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader("Фильтры"),
                            dbc.Row(
                                [
                                    dbc.Col(update_buttons(type_page), width=2),
                                    dbc.Col(filter_years(type_page), width=1),
                                ]
                            ),
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        ),
        dcc.Loading(id=f'loading-output-{type_page}', type='default'),
        card_table(f'result-table1-{type_page}', "По целям", page_size=10),
    ],
    style={"padding": "0rem"}
)


@app.callback(
    [Output(f'result-table1-{type_page}', 'columns'),
     Output(f'result-table1-{type_page}', 'data'),
     Output(f'loading-output-{type_page}', 'children')],
    [Input(f'update-button-{type_page}', 'n_clicks')],
    [State(f'dropdown-year-{type_page}', 'value'),
     ]
)
def update_table(n_clicks, selected_year):
    # Если кнопка не была нажата, обновление не происходит
    if n_clicks is None:
        raise exceptions.PreventUpdate

    loading_output = html.Div([dcc.Loading(type="default")])
    print(sql_query_reproductive_building_department(
            selected_year,
            months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
            inogorod=None,
            sanction=None,
            amount_null=None,
            building=None,
            profile=None,
            doctor=None,
            input_start=None,
            input_end=None,
            treatment_start=None,
            treatment_end=None
        ))
    columns1, data1 = TableUpdater.query_to_df(
        engine,
        sql_query_reproductive_building_department(
            selected_year,
            months_placeholder='1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
            inogorod=None,
            sanction=None,
            amount_null=None,
            building=None,
            profile=None,
            doctor=None,
            input_start=None,
            input_end=None,
            treatment_start=None,
            treatment_end=None
        )
    )

    return columns1, data1, loading_output
