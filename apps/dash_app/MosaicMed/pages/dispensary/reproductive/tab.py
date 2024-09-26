from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.dispensary.reproductive.tab1 import tab1_reproductive
from services.MosaicMed.pages.dispensary.reproductive.tab2 import tab2_reproductive
from services.MosaicMed.pages.dispensary.reproductive.tab3 import tab3_reproductive

# вкладки
app_tabs_reproductive = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчеты по репродуктивному здоровью", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Прикрепленное население', value='tab1',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='По типу и полу', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список пациентов с отметкой о прохождении', value='tab3',
                                selected_className='custom-tab--selected'),
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id='tabs-content-reproductive')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output('tabs-content-reproductive', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_reproductive
    if tab_chose == 'tab2':
        return tab2_reproductive
    if tab_chose == 'tab3':
        return tab3_reproductive
    else:
        return html.H2('Страница в разработке')
