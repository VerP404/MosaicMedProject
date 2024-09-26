from dash import html, dcc, Output, Input
from services.MosaicMed.app import app
from services.MosaicMed.pages.WO_coupons.status_talon.tab1 import tab1_layout_other_status
from services.MosaicMed.pages.WO_coupons.status_talon.tab2 import tab2_layout_other_status
from services.MosaicMed.pages.WO_coupons.status_talon.tab3 import tab3_layout_other_status
from services.MosaicMed.pages.WO_coupons.status_talon.tab4 import tab4_layout_other_status
from services.MosaicMed.pages.WO_coupons.status_talon.tab5 import tab5_layout_other_status
from services.MosaicMed.pages.WO_coupons.status_talon.tab6 import tab6_layout_other_status
from services.MosaicMed.pages.WO_coupons.status_talon.tab7 import tab7_layout_other_status

# вкладки
app_tabs_talon_wo = html.Div(
    [
        html.Div(
            [
                dcc.Tabs(
                    [
                        dcc.Tab(label='Все цели', value='tab1',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Специальности по целям', value='tab2',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Цель по корпусам', value='tab3',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Корпус и специальность по целям', value='tab4',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Талоны по дате окончания лечения и корпусам', value='tab5',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Цель и диагноз по корпусам', value='tab6',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Пациенты с диагнозом', value='tab7',
                                selected_className='custom-tab--selected'),
                    ],
                    id='tabs1',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id='tabs-content-other-reports-status-talon')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output('tabs-content-other-reports-status-talon', 'children'),
    [Input('tabs1', 'value')]
)
def switch_tab(tab_choses):
    if tab_choses == 'tab1':
        return tab1_layout_other_status
    if tab_choses == 'tab2':
        return tab2_layout_other_status
    if tab_choses == 'tab3':
        return tab3_layout_other_status
    if tab_choses == 'tab4':
        return tab4_layout_other_status
    if tab_choses == 'tab5':
        return tab5_layout_other_status
    if tab_choses == 'tab6':
        return tab6_layout_other_status
    if tab_choses == 'tab7':
        return tab7_layout_other_status
    else:
        return html.H2('Страница в разработке')
