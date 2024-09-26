from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.doctors_talon.doctor.tab1 import tab1_doctor_talon_layout
from services.MosaicMed.pages.doctors_talon.doctor.tab2 import tab2_doctor_talon_layout
from services.MosaicMed.pages.doctors_talon.doctor.tab3 import tab3_doctor_talon_layout

type_page = 'doctors-talon'

# вкладки
app_tabs_doctors = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по врачам", color="primary"),
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
        return tab1_doctor_talon_layout
    elif tab_chose == 'tab2':
        return tab2_doctor_talon_layout
    elif tab_chose == 'tab3':
        return tab3_doctor_talon_layout
    else:
        return html.H2('Страница не выбрана..')
