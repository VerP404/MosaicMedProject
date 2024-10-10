from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from apps.analytical_app.app import app
from apps.analytical_app.query_executor import execute_query


# Получение причин аннулирования
def get_invalidation_reasons():
    query = "SELECT id, reason_text FROM reports_invalidationreason"
    result = execute_query(query)
    return [{'label': row[1], 'value': row[0]} for row in result]


# Получение целей ОМС
def get_goals():
    query = """
    SELECT target.id, general.code 
    FROM oms_reference_medicalorganizationomstarget AS target
    JOIN oms_reference_generalomstarget AS general
    ON target.general_target_id = general.id
    WHERE target.is_active = TRUE
    """
    result = execute_query(query)
    return [{'label': row[1], 'value': row[0]} for row in result]


# Получение данных по умолчанию для OID МО
def get_default_oid_mo():
    query = "SELECT oid_mo FROM organization_medicalorganization LIMIT 1"
    result = execute_query(query)
    return result[0][0] if result else "Не задано"


# Получение данных для таблицы DeleteEmd
def get_delete_emd_data():
    query = """
    SELECT org.oid_mo, delete_emd.oid_document, delete_emd.creation_date, delete_emd.registration_date, 
           delete_emd.reestr_number, delete_emd.local_identifier, delete_emd.reason_not_actual_id, 
           delete_emd.document_number, delete_emd.patient, delete_emd.date_of_birth, 
           delete_emd.enp, delete_emd.goal_id, delete_emd.treatment_end 
    FROM reports_deleteemd AS delete_emd
    JOIN organization_medicalorganization AS org
    ON delete_emd.oid_medical_organization_id = org.id
    """
    result = execute_query(query)
    columns = ['oid_mo', 'oid_document', 'creation_date', 'registration_date', 'reestr_number',
               'local_identifier', 'reason_not_actual_id', 'document_number', 'patient', 'date_of_birth', 'enp',
               'goal_id', 'treatment_end']
    return [dict(zip(columns, row)) for row in result]


admin_delete_emd = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ЭМД: аннулирование - Заполнение данных"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='delete-emd-table',
                        columns=[
                            {'name': 'OID МО', 'id': 'oid_mo', 'editable': False},
                            {'name': 'OID документа', 'id': 'oid_document', 'editable': True},
                            {'name': 'Дата создания', 'id': 'creation_date', 'editable': True},
                            {'name': 'Дата регистрации', 'id': 'registration_date', 'editable': True},
                            {'name': 'Номер в реестре РЭМД', 'id': 'reestr_number', 'editable': True},
                            {'name': 'Локальный идентификатор', 'id': 'local_identifier', 'editable': True},
                            {'name': 'Причина признания ЭМД не актуальным', 'id': 'reason_not_actual_id',
                             'editable': True},
                            {'name': 'Номер документа, оформленного взамен', 'id': 'document_number', 'editable': True},
                            {'name': 'Пациент', 'id': 'patient', 'editable': True},
                            {'name': 'Дата рождения', 'id': 'date_of_birth', 'editable': True},
                            {'name': 'ЕНП', 'id': 'enp', 'editable': True},
                            {'name': 'Цель ОМС', 'id': 'goal_id', 'editable': True},
                            {'name': 'Окончание лечения', 'id': 'treatment_end', 'editable': True},
                        ],
                        data=get_delete_emd_data(),
                        editable=True,
                        row_deletable=True,
                        style_table={'overflowX': 'auto'},  # Включение горизонтальной прокрутки
                        style_cell={'textAlign': 'left'},  # Выровненные по левому краю ячейки
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        }
                    )
                ])
            ]),
            dbc.Card([
                dbc.CardHeader("Добавить новую запись"),
                dbc.CardBody([
                    dcc.Input(id='oid_medical_organization_hidden', type='hidden', value=get_default_oid_mo()),
                    dcc.Input(id='oid_document', placeholder='OID документа', type='text', className='form-control',
                              style={'margin-bottom': '10px'}),
                    dcc.DatePickerSingle(id='creation_date', placeholder='Дата создания', className='form-control',
                                         style={'margin-bottom': '10px'}),
                    dcc.DatePickerSingle(id='registration_date', placeholder='Дата регистрации',
                                         className='form-control', style={'margin-bottom': '10px'}),
                    dcc.Input(id='reestr_number', placeholder='Номер в реестре РЭМД', type='text',
                              className='form-control', style={'margin-bottom': '10px'}),
                    dcc.Input(id='local_identifier', placeholder='Локальный идентификатор', type='text',
                              className='form-control', style={'margin-bottom': '10px'}),
                    dcc.Dropdown(id='reason_not_actual', options=[], placeholder='Причина аннулирования',
                                 className='form-control', style={'margin-bottom': '10px'}),
                    dcc.Input(id='document_number', placeholder='Номер документа взамен', type='text',
                              className='form-control', style={'margin-bottom': '10px'}),
                    dcc.Input(id='patient', placeholder='Пациент', type='text', className='form-control',
                              style={'margin-bottom': '10px'}),
                    dcc.DatePickerSingle(id='date_of_birth', placeholder='Дата рождения', className='form-control',
                                         style={'margin-bottom': '10px'}),
                    dcc.Input(id='enp', placeholder='ЕНП', type='text', className='form-control',
                              style={'margin-bottom': '10px'}),
                    dcc.Dropdown(id='goal', options=[], placeholder='Цель ОМС', className='form-control',
                                 style={'margin-bottom': '10px'}),
                    dcc.DatePickerSingle(id='treatment_end', placeholder='Окончание лечения', className='form-control',
                                         style={'margin-bottom': '10px'}),
                    html.Button('Добавить запись', id='submit-val', n_clicks=0, className='btn btn-primary')
                ])
            ], style={'margin-top': '20px'})
        ])
    ])
], fluid=True)


# Обновление компонента с выпадающим списком
@app.callback(
    [Output('reason_not_actual', 'options'),
     Output('goal', 'options')],
    [Input('submit-val', 'n_clicks')]
)
def update_dropdowns(n_clicks):
    # Получение опций для dropdown'ов
    reasons = get_invalidation_reasons()
    goals = get_goals()

    # Возвращаем данные для обновления dropdown'ов
    return reasons, goals


# Callback для добавления новой записи
@app.callback(
    Output('output-state', 'children'),
    [Input('submit-val', 'n_clicks')],
    [
        State('oid_medical_organization_hidden', 'value'),  # Используем value вместо children
        State('oid_document', 'value'),
        State('creation_date', 'date'),
        State('registration_date', 'date'),
        State('reestr_number', 'value'),
        State('local_identifier', 'value'),
        State('reason_not_actual', 'value'),
        State('document_number', 'value'),
        State('patient', 'value'),
        State('date_of_birth', 'date'),
        State('enp', 'value'),
        State('goal', 'value'),
        State('treatment_end', 'date')
    ]
)
def add_record(n_clicks, oid_medical_organization, oid_document, creation_date, registration_date,
               reestr_number, local_identifier, reason_not_actual, document_number,
               patient, date_of_birth, enp, goal, treatment_end):
    if n_clicks > 0:
        query = """
        INSERT INTO reports_deleteemd 
        (oid_medical_organization_id, oid_document, creation_date, registration_date, reestr_number, local_identifier, 
        reason_not_actual_id, document_number, patient, date_of_birth, enp, goal_id, treatment_end)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (oid_medical_organization, oid_document, creation_date, registration_date, reestr_number,
                  local_identifier, reason_not_actual, document_number, patient, date_of_birth, enp, goal,
                  treatment_end)
        execute_query(query, params)
        return 'Запись добавлена!'
    return ''

