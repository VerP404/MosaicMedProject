from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.eln.tab1 import tab1_eln
from services.MosaicMed.pages.eln.tab2 import tab2_eln

type_page = "eln"
# вкладки
app_tabs_eln = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчеты по листам нетрудоспособности", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Отчет по пациентам с большим количествам ЛН', value='tab1',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Пациенты с открытыми ЛН и запись на прием', value='tab2',
                                selected_className='custom-tab--selected'),
                    ],
                    id=f'tabs-{type_page}',
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
    [Input(f'tabs-{type_page}', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab1_eln
    elif tab_chose == 'tab2':
        return tab2_eln
    else:
        return html.H2('Страница в разработке')
