from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.doctors_talon.doctors_list.tab1 import tab1_doctor_talon_list
from services.MosaicMed.pages.doctors_talon.doctors_list.tab2 import tab2_doctor_talon_list
from services.MosaicMed.pages.doctors_talon.doctors_list.tab3 import tab3_doctor_talon_list

type_page = 'doctors-talon-list'

# вкладки
app_tabs_doctors_list = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по врачам. Список по подразделениям", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='По отчетному месяцу', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='По дате лечения', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='По дате формирования', value='tab3', selected_className='custom-tab--selected'),
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id=f'tabs-{type_page}')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output(f'tabs-{type_page}', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_doctor_talon_list
    elif tab_chose == 'tab2':
        return tab2_doctor_talon_list
    elif tab_chose == 'tab3':
        return tab3_doctor_talon_list
    else:
        return html.H2('Страница не выбрана..')
