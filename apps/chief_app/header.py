from dash import html


def header_func(_title_text, _date_update, app):
    return html.Div([
        html.Div([
            html.Img(src=app.get_asset_url('logo-vgp3.png'),
                     id='logo-vgp3-image',
                     style={
                         "height": "100px",
                         "width": "auto",
                     },
                     )
        ],
            className="one-third column",
        ),
        html.Div([
            html.Div([
                html.H3("БУЗ ВО ВГП №3",
                        style={"margin-bottom": "0px",
                               'color': 'white'}),
                html.H5(_title_text,
                        style={"margin-top": "0px",
                               'color': 'white'}),
            ])
        ], className="one-half column", id="title"),
        html.Div([
            html.H6('Обновлено: ' + f'{_date_update}',
                    style={'color': 'white'}),
            html.Div(id='current-date-output', style={"color": "white", 'font-size': '30px'})

        ], className="one-third column", id='title1'),

    ], id="header",
        className="row flex-display")

