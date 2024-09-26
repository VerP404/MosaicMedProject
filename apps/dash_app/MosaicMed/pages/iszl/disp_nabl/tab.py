from dash import html, dcc, Output, Input
from services.MosaicMed.app import app
from services.MosaicMed.pages.iszl.disp_nabl.tab1 import tab1_layout_iszl_disp_nab_svod
from services.MosaicMed.pages.iszl.disp_nabl.tab2 import tab2_layout_iszl_disp_nab_list
from services.MosaicMed.pages.iszl.disp_nabl.tab3 import tab3_layout_disp_nab_fgs
from services.MosaicMed.pages.iszl.disp_nabl.tab4 import tab4_layout_disp_nab_cel_3
from services.MosaicMed.pages.iszl.disp_nabl.tab5 import tab4_layout_disp_nab_pr

type_page = "iszl-disp-nab"
# вкладки
app_tabs_iszl_disp_nab = html.Div(
    [
        html.Div(
            [
                dcc.Tabs(
                    [
                        dcc.Tab(label='Сводная информация', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список пациентов из ИСЗЛ по 168н, посещавших поликлинику, но без талона цели 3', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список пациентов из ИСЗЛ по 168н, с отметкой о записи на ЭГДС/колоноскопию', value='tab3', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Список пациентов из ИСЗЛ с талонами ОМС', value='tab4', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Пациенты для приглашения', value='tab5', selected_className='custom-tab--selected'),
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
        return tab1_layout_iszl_disp_nab_svod
    elif tab_chose == 'tab2':
        return tab2_layout_iszl_disp_nab_list
    elif tab_chose == 'tab3':
        return tab3_layout_disp_nab_fgs
    elif tab_chose == 'tab4':
        return tab4_layout_disp_nab_cel_3
    elif tab_chose == 'tab5':
        return tab4_layout_disp_nab_pr

    else:
        return html.H2('Страница в разработке..')
