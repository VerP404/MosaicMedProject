from datetime import datetime

from dash import html

# Переменная для хранения времени первого запуска
initial_time = datetime.now().strftime('%d.%m.%Y %H:%M')


def get_current_date_update():
    now = datetime.now()
    hour = now.hour

    # Определяем ближайшее время обновления
    if hour < 8:
        update_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    elif hour < 12:
        update_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
    elif hour < 16:
        update_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    else:
        update_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        update_time = update_time.replace(day=now.day + 1)

    return update_time.strftime('%d.%m.%Y %H:%M')


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
