from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.dispensary.adults.tab1 import tab1_layout_da
from services.MosaicMed.pages.dispensary.adults.tab2 import tab2_layout_da
from services.MosaicMed.pages.dispensary.adults.tab3 import tab3_layout_da
from services.MosaicMed.pages.dispensary.adults.tab4 import tab4_layout_da
from services.MosaicMed.pages.dispensary.adults.tab5 import tab5_layout_da
from services.MosaicMed.pages.dispensary.adults.tab6 import tab6_layout_da
from services.MosaicMed.pages.dispensary.adults.tab7 import tab7_layout_da
from services.MosaicMed.pages.dispensary.adults.tab8 import tab8_layout_da

# вкладки
app_tabs_da = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по диспансеризации взрослых", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='По корпусам и видам', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='По корпусам и статусам', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Диспансеризация и профосмотры по возрастам', value='tab3', selected_className='custom-tab--selected'),
                        dcc.Tab(label='ДВ4 по возрастам', value='tab4', selected_className='custom-tab--selected'),
                        dcc.Tab(label='ОПВ по возрастам', value='tab5', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Внесение в Флюоромониторинг', value='tab6', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список не прошедших ДВ4 и ОПВ', value='tab7', selected_className='custom-tab--selected'),
                        dcc.Tab(label='ДВ4 стоимость', value='tab8', selected_className='custom-tab--selected'),
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id='tabs-content-da')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output('tabs-content-da', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_layout_da
    elif tab_chose == 'tab2':
        return tab2_layout_da
    elif tab_chose == 'tab3':
        return tab3_layout_da
    elif tab_chose == 'tab4':
        return tab4_layout_da
    elif tab_chose == 'tab5':
        return tab5_layout_da
    elif tab_chose == 'tab6':
        return tab6_layout_da
    elif tab_chose == 'tab7':
        return tab7_layout_da
    elif tab_chose == 'tab8':
        return tab8_layout_da
    else:
        return html.H2('Страница в разработке')
