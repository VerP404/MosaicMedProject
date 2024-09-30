import dash_bootstrap_components as dbc
from dash import html, Output, Input, dash_table


def card_table(id_table, card_header, page_size=None):
    table_kwargs = {
        'id': id_table,
        'editable': False,
        'filter_action': "native",
        'sort_action': "native",
        'sort_mode': 'multi',
        'export_format': 'xlsx',
        'export_headers': 'display',
        'style_table': {'overflowX': 'auto'},
        'style_cell': {'minWidth': '0px', 'maxWidth': '180px', 'whiteSpace': 'normal'}
    }

    if page_size is not None:
        table_kwargs['page_size'] = page_size

    return (
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.CardHeader(card_header),
                            html.Div(
                                dash_table.DataTable(**table_kwargs),
                                style={"maxWidth": "100%", "overflowX": "auto"}
                            )
                        ]
                    ),
                    style={"width": "100%", "padding": "0rem", "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2)",
                           "border-radius": "10px"}
                ),
                width=12
            ),
            style={"margin": "0 auto", "padding": "0rem"}
        )
    )

