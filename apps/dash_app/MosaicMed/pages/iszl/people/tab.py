from dash import html, dcc, Output, Input
from services.MosaicMed.app import app

from services.MosaicMed.pages.iszl.people.tab1 import tab1_layout_people_iszl
from services.MosaicMed.pages.iszl.people.tab2 import tab2_layout_people_iszl
from services.MosaicMed.pages.iszl.people.tab3 import tab3_layout_people_iszl
from services.MosaicMed.pages.iszl.people.tab4 import tab4_layout_people_iszl
from services.MosaicMed.pages.iszl.people.tab5 import tab5_layout_people_iszl

type_page = "iszl"
# вкладки
app_tabs_people_iszl = html.Div(
    [
        html.Div(
            [
                dcc.Tabs(
                    [
                        dcc.Tab(label='Половозрастная структура', value='tab1',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Неверные участки для подгрузки в ИСЗЛ', value='tab2',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список пациентов ИСЗЛ с участком для распределения', value='tab3',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Половозрастная структура по 168н', value='tab4',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Половозрастная структура по 168н с выставленными талонами', value='tab5',
                                selected_className='custom-tab--selected'),

                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id=f'tabs-content-{type_page}')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output(f'tabs-content-{type_page}', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_layout_people_iszl
    elif tab_chose == 'tab2':
        return tab2_layout_people_iszl
    elif tab_chose == 'tab3':
        return tab3_layout_people_iszl
    elif tab_chose == 'tab4':
        return tab4_layout_people_iszl
    elif tab_chose == 'tab5':
        return tab5_layout_people_iszl
    else:
        return html.H2('Страница в разработке..')
