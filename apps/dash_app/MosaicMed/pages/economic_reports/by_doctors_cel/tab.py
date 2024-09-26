from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.economic_reports.by_doctors_cel.tab1 import tab1_layout_by_doctor_cel_mest
from services.MosaicMed.pages.economic_reports.by_doctors_cel.tab2 import tab1_layout_by_doctor_cel_inog
from services.MosaicMed.pages.economic_reports.by_doctors_cel.tab3 import tab1_layout_by_doctor_cel_stac

type_page = "by-doctor-cel"
# вкладки
app_tabs_by_doctor_cel = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по врачам", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Местные', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Иногородние', value='tab2', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Стационары', value='tab3', selected_className='custom-tab--selected'),
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
        return tab1_layout_by_doctor_cel_mest
    elif tab_chose == 'tab2':
        return tab1_layout_by_doctor_cel_inog
    elif tab_chose == 'tab3':
        return tab1_layout_by_doctor_cel_stac
    else:
        return html.H2('Страница не выбрана..')
