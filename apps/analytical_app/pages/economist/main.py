from dash import html, dcc, Output, Input, dash_table, exceptions, State, callback_context
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app

# Карточки в виде группы с одинаковой высотой
cards = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Сверхподушевое финансирование", className="card-title"),
                    html.P(
                        "Описание отчета по сверхподушевому финансированию, включая анализ текущего состояния.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="success", className="mt-auto", id="open-report-1"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Экономический анализ", className="card-title"),
                    html.P(
                        "Анализ текущего экономического состояния учреждения с выводами и рекомендациями.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="warning", className="mt-auto", id="open-report-2"
                    ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Статистический отчет", className="card-title"),
                    html.P(
                        "Подробный отчет с текущими статистическими данными и прогнозами.",
                        className="card-text",
                    ),
                    dbc.Button(
                        "Открыть", color="danger", className="mt-auto", id="open-report-3"
                    ),
                ]
            )
        ),
    ]
)

# Основной макет страницы "Экономист"
economist_main = html.Div([
    dbc.Row(dbc.Col(html.H5("Экономист"),)),
    html.Hr(),
    # Вставляем CardGroup с карточками
    html.Div(cards, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),

])


# Объединённый коллбэк для открытия отчетов и возврата назад
@app.callback(
    Output('url', 'pathname'),
    [Input('open-report-1', 'n_clicks'),
     Input('open-report-2', 'n_clicks'),
     Input('open-report-3', 'n_clicks')],
    prevent_initial_call=True  # Не выполнять коллбэк при загрузке страницы
)
def navigate_pages(open_report_1, open_report_2, open_report_3):
    ctx = callback_context
    if not ctx.triggered:
        return '/economist'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'open-report-1' and open_report_1:
        return '/report-1'
    elif button_id == 'open-report-2' and open_report_2:
        return '/report-2'
    elif button_id == 'open-report-3' and open_report_3:
        return '/report-3'

    return '/economist'
