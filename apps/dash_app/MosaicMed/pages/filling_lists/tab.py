from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from services.MosaicMed.app import app
from services.MosaicMed.pages.filling_lists.tab1 import tab_layout_add_contact_info
from services.MosaicMed.pages.filling_lists.tab2 import tab_layout_vokod
from services.MosaicMed.pages.filling_lists.tab3 import tab_layout_smo

type_tab = 'fil-list'
# вкладки
app_tabs_fil_list = html.Div(
    [
        html.Div(
            [
                dbc.Alert("Система заполнения списков", color="primary"),
                dcc.Tabs(
                    [
                        dcc.Tab(label='Добавление адреса и телефона', value='tab1',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Обработка списков ВОКОД', value='tab2',
                                selected_className='custom-tab--selected'),
                        dcc.Tab(label='Списки для проверок страховых', value='tab3',
                                selected_className='custom-tab--selected')
                    ],
                    id='tabs',
                    value='tab1',
                    parent_className='custom-tabs',
                    className='custom-tabs-container',
                ),
            ], className='tabs'
        ),
        html.Div(id=f'tabs-content-{type_tab}')
    ], className='tabs-app'
)


# возвращаем вкладки
@app.callback(
    Output(f'tabs-content-{type_tab}', 'children'),
    [Input('tabs', 'value')]
)
def switch_tab(tab_chose):
    if tab_chose == 'tab1':
        return tab_layout_add_contact_info
    elif tab_chose == 'tab2':
        return tab_layout_vokod
    elif tab_chose == 'tab3':
        return tab_layout_smo
    else:
        return html.H2('Страница не выбрана..')
