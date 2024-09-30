from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.it_department.cel_3.tab1 import tab1_layout_cel_3

# вкладки
app_tabs_cel3 = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по диспансеризации взрослых", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Проведено ДН по БСК более 1 раза в году', value='tab1', selected_className='custom-tab--selected'),
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id='tabs-content-cel3')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output('tabs-content-cel3', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_layout_cel_3
    else:
        return html.H2('Страница в разработке')
