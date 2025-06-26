import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, Patch
import dash_ag_grid as dag
import pandas as pd

from apps.analytical_app.callback import TableUpdater
from apps.analytical_app.pages.head.dispensary.children.query import query_uniq
from apps.analytical_app.query_executor import engine
from apps.analytical_app.app import app

type_page = "children-unique"

children_unique = html.Div([
    html.H3('Уникальные дети в профосмотрах', className='label'),
    dcc.Dropdown(
        id=f'year-dropdown-{type_page}',
        options=[{'label': str(year), 'value': str(year)} for year in range(2020, 2031)],
        value='2025',
        clearable=False,
        placeholder="Выберите год",
        style={"width": "150px", "display": "inline-block", "marginRight": "20px"}
    ),
    dbc.Button(id=f'get-data-button-{type_page}', n_clicks=0, children='Получить данные'),
    dcc.Loading(id=f'loading-output-{type_page}', type='default'),

    dag.AgGrid(
        licenseKey='asd',
        id=f'result-table-{type_page}',
        columnDefs=[],  # зададим в callback
        rowData=[],     # зададим в callback

        # Оформление контейнера таблицы
        style={"height": "700px", "width": "100%"},

        # Общие настройки колонок
        defaultColDef={
            "sortable": True,
            "filter": True,
            "resizable": True,
            "suppressAggFuncInHeader": True,
            "minWidth": 50
        },
        enableEnterpriseModules=True,

        # Дополнительные опции задаем через dashGridOptions
        dashGridOptions={
            "suppressAggFuncInHeader": True,
            "autoGroupColumnDef": {
                "headerName": "Группа",
                "minWidth": 250
            },
            # Свернуть группу "Статусы" по умолчанию (groupId указан в columnDefs)
            "columnState": [
                {"colId": "statusesGroup", "open": False}
            ]
        }
    )
], className='block')


@app.callback(
    [
        Output(f'result-table-{type_page}', 'columnDefs'),
        Output(f'result-table-{type_page}', 'rowData'),
        Output(f'loading-output-{type_page}', 'children')
    ],
    [
        Input(f'get-data-button-{type_page}', 'n_clicks'),
        Input(f'year-dropdown-{type_page}', 'value')
    ]
)
def update_table_dd(n_clicks, selected_year):
    if not n_clicks:
        return [], [], ""

    loading_output = dcc.Loading(type="default")
    columns, data = TableUpdater.query_to_df(engine, query_uniq(selected_year))

    # Приводим названия колонок к короткому виду (убираем sum(...))
    if columns and isinstance(columns, list) and isinstance(columns[0], dict):
        for col in columns:
            if 'headerName' in col and isinstance(col['headerName'], str) and col['headerName'].startswith('sum(') and col['headerName'].endswith(')'):
                col['headerName'] = col['headerName'][4:-1]
            if 'field' in col and isinstance(col['field'], str) and col['field'].startswith('sum(') and col['field'].endswith(')'):
                col['field'] = col['field'][4:-1]
    if data and isinstance(data, list) and isinstance(data[0], dict):
        for row in data:
            for k in list(row.keys()):
                if k.startswith('sum(') and k.endswith(')'):
                    row[k[4:-1]] = row.pop(k)

    if data:
        column_defs = [
            {
                "headerName": "Группировка",
                "children": [
                    {
                        "headerName": "Отделение",
                        "field": "department",
                        "rowGroup": True,
                        "hide": True,
                        "width": 300,
                        "pinned": "left",
                    },
                    {
                        "headerName": "Месяц",
                        "field": "month",
                        "rowGroup": True,
                        "hide": True
                    }
                ]
            },
            {
                "headerName": "Показатели",
                "children": [
                    {
                        "headerName": "Оплачено",
                        "field": "Оплачено",
                        "aggFunc": "sum",
                        "type": "numericColumn",
                    },
                    {
                        "headerName": "В работе",
                        "field": "В работе",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "Отказано",
                        "field": "Отказано",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "Отменено",
                        "field": "Отменено",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    }
                ]
            },
            {
                "headerName": "Итого",
                "children": [
                    {
                        "headerName": "Всего",
                        "field": "total_count",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    }
                ]
            },
            {
                # Присваиваем groupId для возможности свернуть группу
                "headerName": "Статусы",
                "groupId": "statusesGroup",
                "marryChildren": True,
                "children": [
                    {
                        "headerName": "1",
                        "field": "1",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "2",
                        "field": "2",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "3",
                        "field": "3",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "4",
                        "field": "4",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "5",
                        "field": "5",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "6",
                        "field": "6",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "7",
                        "field": "7",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "8",
                        "field": "8",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "12",
                        "field": "12",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "13",
                        "field": "13",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "17",
                        "field": "17",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    },
                    {
                        "headerName": "0",
                        "field": "0",
                        "aggFunc": "sum",
                        "type": "numericColumn"
                    }
                ]
            }
        ]
        return column_defs, data, loading_output
    else:
        return [], [], loading_output


@app.callback(
    Output(f'result-table-{type_page}', 'dashGridOptions'),
    Input(f'result-table-{type_page}', 'virtualRowData')
)
def update_pinned_bottom(data):
    if not data:
        return {}
    dff = pd.DataFrame(data)
    numeric_cols = ["Оплачено", "В работе", "Отказано", "Отменено", "1", "2", "3", "4", "5", "6", "7", "8", "12", "13",
                    "17", "0", "total_count"]
    sums = dff[numeric_cols].sum()
    summary = {"department": "ИТОГО", "month": ""}
    for col in numeric_cols:
        summary[col] = sums[col]
    patch = Patch()
    patch["pinnedBottomRowData"] = [summary]
    return patch
