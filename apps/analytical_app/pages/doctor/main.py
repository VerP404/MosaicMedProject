from dash import html, callback_context, no_update, Output, Input
import dash_bootstrap_components as dbc
from apps.analytical_app.app import app
from apps.analytical_app.components.cards import create_card

type_page = "doctor"
main_link = "doctor"  # начало ссылки
label = "Врач"  # для хлебных крошек

cards_row_1 = dbc.Row(
    [
        dbc.Col(create_card(1, type_page,
                            "Талоны по типу и цели",
                            "Талоны ОМС по типам и цели. Фильтрация по всем параметрам.")),
        dbc.Col(create_card(2, type_page,
                            "Отказы",
                            "Работа с отказами в оплате ОМС.")),
    ],
    className="mb-4 align-items-stretch",
)

doctor_main = html.Div([
    dbc.Breadcrumb(id=f"breadcrumb-{type_page}", items=[
        {"label": label, "active": True},
    ]),
    html.Hr(),
    html.Div(cards_row_1, style={"marginBottom": "20px", "display": "flex", "justify-content": "center"}),
])


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output(f'breadcrumb-{type_page}', 'items')],
    [Input(f'open-report-1-{type_page}', 'n_clicks'),
     Input(f'open-report-2-{type_page}', 'n_clicks'),
     ],
    prevent_initial_call=True
)
def navigate_pages(open_report_1, open_report_2):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_path = f'/{main_link}'

    breadcrumb_items = [{"label": label, "href": current_path, "active": True}]

    if button_id.startswith("open-report-"):
        new_segment = None
        if button_id == f'open-report-1-{type_page}' and open_report_1:
            new_segment = "doctor_talon"
        elif button_id == f'open-report-2-{type_page}' and open_report_2:
            new_segment = "error"

        if new_segment:
            # Добавляем новый сегмент к текущему маршруту
            new_path = f'{current_path}/{new_segment}'
            breadcrumb_items.append({"label": new_segment, "active": True})
            return new_path, breadcrumb_items

    return no_update, no_update
