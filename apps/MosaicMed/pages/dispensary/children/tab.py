from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.dispensary.children.tab1 import tab1_layout_dc
from services.MosaicMed.pages.dispensary.children.tab2 import tab2_layout_dc
from services.MosaicMed.pages.dispensary.children.tab3 import tab3_layout_other_children_age_dispensary
from services.MosaicMed.pages.dispensary.children.tab4 import tab4_layout_other_children_list
from services.MosaicMed.pages.dispensary.children.tab5 import tab5_layout_children_list_not_pn

# вкладки
app_tabs_dc = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по диспансеризации детей", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='По корпусам', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Уникальные', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Профосмотр детей по возрастам', value='tab3', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Дети до 1.5 лет', value='tab4', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список прикрепленных детей без ПН1', value='tab5', selected_className='custom-tab--selected'),
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id='tabs-content-dc')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output('tabs-content-dc', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_layout_dc
    elif tab_chose == 'tab2':
        return tab2_layout_dc
    elif tab_chose == 'tab3':
        return tab3_layout_other_children_age_dispensary
    elif tab_chose == 'tab4':
        return tab4_layout_other_children_list
    elif tab_chose == 'tab5':
        return tab5_layout_children_list_not_pn
    else:
        return html.H2('Страница в разработке')
