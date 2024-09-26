from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.economic_reports.by_doctors.tab1 import tab1_layout_by_doctor
from services.MosaicMed.pages.economic_reports.by_doctors.tab2 import tab2_layout_by_doctor

type_page = "by-doctor"
# вкладки
app_tabs_by_doctor = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчет по врачам", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Общий', value='tab1', selected_className='custom-tab--selected'),
                        dcc.Tab(label='Стационары', value='tab2', selected_className='custom-tab--selected'),
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
        return tab1_layout_by_doctor
    elif tab_chose == 'tab2':
        return tab2_layout_by_doctor
    else:
        return html.H2('Страница не выбрана..')
