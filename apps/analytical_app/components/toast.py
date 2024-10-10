import dash_bootstrap_components as dbc


def toast(type_page):
    return dbc.Toast(
        "Данные не найдены. Измените фильтры.",
        id=f"no-data-toast-{type_page}",
        header="Внимание",
        icon="danger",
        duration=4000,  # 4 секунды
        is_open=False,
        dismissable=True,  # Позволяет пользователю закрыть
        style={"position": "fixed", "top": 60, "right": 50, "width": 350},
    )
