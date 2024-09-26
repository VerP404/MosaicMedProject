from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app

from services.MosaicMed.pages.economic_reports.stationary.tab1 import stationary_tab1

type_page = "stationary"
# вкладки
stationary = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчеты по стационарам", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='КСГ по корпусам', value='tab1', selected_className='custom-tab--selected'),

                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id=f'tabs-content-dtr-{type_page}')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output(f'tabs-content-dtr-{type_page}', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return stationary_tab1
    else:
        return html.H2('Страница не выбрана..')
