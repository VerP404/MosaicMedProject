from dash import html


def generate_table(dataframe, max_rows=10):
    return html.Table(
        className="card-table",
        children=[
            # Header
            html.Thead(html.Tr([html.Th(col, className='table-cell table-header') for col in dataframe.columns])),

            # Body
            html.Tbody([
                html.Tr([
                    html.Td(dataframe.iloc[i][col], className='table-cell',
                            style={'textAlign': 'left'} if col == dataframe.columns[0] else {'textAlign': 'center'})
                    for col in dataframe.columns
                ]) for i in range(min(len(dataframe), max_rows))
            ])
        ]
    )
