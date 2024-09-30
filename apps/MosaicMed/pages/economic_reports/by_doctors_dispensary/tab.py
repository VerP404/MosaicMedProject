from dash import html, dcc, Output, Input
from services.MosaicMed.app import app
from services.MosaicMed.pages.economic_reports.by_doctors_dispensary.tab1 import tab1_layout_by_doctor_dispensary
from services.MosaicMed.pages.economic_reports.by_doctors_dispensary.tab2 import tab2_layout_by_doctor_dispensary
from services.MosaicMed.pages.economic_reports.by_doctors_dispensary.tab3 import tab3_layout_by_doctor_dispensary

type_page = "by-doctor-dispensary"
# вкладки
app_tabs_by_doctor_dispensary = html.Div(
    [
        html.Div(
            [
                dcc.Tabs(
                    [
                        dcc.Tab(label='Взрослые', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Дети', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Репродуктивное', value='tab3', selected_className='custom-tab--selected'),
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
        return tab1_layout_by_doctor_dispensary
    elif tab_chose == 'tab2':
        return tab2_layout_by_doctor_dispensary
    elif tab_chose == 'tab3':
        return tab3_layout_by_doctor_dispensary
    else:
        return html.H2('Страница не выбрана..')
