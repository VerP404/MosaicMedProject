import base64
import io
import pandas as pd
from dash import html, dcc, Output, Input, dash_table, State

from services.MosaicMed.app import app
from services.MosaicMed.pages.other_reports.emergency.app_neot import neotlojka_data, neotlojka_pacient_last_file

type_page = "emergency"

tab_layout_other_emergency = html.Div([
    html.H3('Отчет по неотложной медицинской помощи с разбивкой по участкам и нозологическим группам',
            className='label'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Нажмите или перетащите файл, выгруженный из журнала ЭПМЗ МИС Квазар (Тип ЭПМЗ - Амбулаторный случай, Цель обслуживания - 22',
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),
    html.Div(id='output-data-upload'),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('cp1251')), sep=';', dtype='str', on_bad_lines='skip')

    # Сбрасываем индекс
    df.reset_index(drop=True, inplace=True)

    path_naselenie = r'\\Srv-main02\_it_reports\Download ISZL\people'  # 10.36.29.5 Srv-main02
    last_naselenie_file, last_naselenie = neotlojka_pacient_last_file(path_naselenie)
    df_neo = neotlojka_data(df, last_naselenie_file)

    return html.Div([
        html.H5(filename),
        html.H6(last_naselenie_file),
        html.H6('*Для обновления файла населения обратитесь в отдел АСУ'),

        dash_table.DataTable(
            df_neo.to_dict('records'),
            [{'name': i, 'id': i} for i in df_neo.columns],
            export_format='xlsx',
            export_headers='display',
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode='multi',
        )
    ])


@app.callback([Output('output-data-upload', 'children'),
              Output(f'loading-output-{type_page}', 'children')],
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        loading_output = html.Div([dcc.Loading(type="default")])
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children, loading_output
    else:
        return [], []
