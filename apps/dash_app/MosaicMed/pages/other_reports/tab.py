from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.other_reports.cardiology_report.cardiology_report import tab_layout_other_cardiology
from services.MosaicMed.pages.other_reports.dispensary_visits.dispensary_visits import app_other_dd_visits
from services.MosaicMed.pages.other_reports.emergency.emergency import tab_layout_other_emergency
from services.MosaicMed.pages.other_reports.obr_epmz.obr_epmz import tab_layout_other_obr_epmz
from services.MosaicMed.pages.other_reports.result_pneumonia.result_pneumonia import tab_layout_other_rp
from services.MosaicMed.pages.other_reports.sharapova.sharapova import tab_layout_other_sharapova
from services.MosaicMed.pages.other_reports.visits.visits import tab_layout_other_visits
from services.MosaicMed.pages.other_reports.vop.vop import tab_layout_other_vop

# вкладки
app_tabs_other_reports = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Отчеты", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Отчет по пневмониям в талонах ОМС', value='tab1',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Отчет по количеству посещений пациентами', value='tab2',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Неотложка', value='tab4',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Посещения пациентов в рамках ДВ4 и ОПВ', value='tab5',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Отчет по ВОП', value='tab6',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Отчет по записанным и ЭПМЗ', value='tab7',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Отчет Шараповой', value='tab8',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Кардиологический отчет', value='tab9',
                                selected_className='custom-tab--selected'),
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id='tabs-content-other-reports')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output('tabs-content-other-reports', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab_layout_other_rp
    elif tab_chose == 'tab2':
        return tab_layout_other_visits
    elif tab_chose == 'tab4':
        return tab_layout_other_emergency
    elif tab_chose == 'tab5':
        return app_other_dd_visits
    elif tab_chose == 'tab6':
        return tab_layout_other_vop
    elif tab_chose == 'tab7':
        return tab_layout_other_obr_epmz
    elif tab_chose == 'tab8':
        return tab_layout_other_sharapova
    elif tab_chose == 'tab9':
        return tab_layout_other_cardiology
    else:
        return html.H2('Страница в разработке')
