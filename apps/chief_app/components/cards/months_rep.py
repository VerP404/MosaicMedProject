import requests
import dash_bootstrap_components as dbc
from dash import dash_table

from apps.chief_app.components.cards.cards_utils import create_card
from apps.chief_app.settings import COLORS


# Функция для получения данных через API
def fetch_api_data():
    url = "http://127.0.0.1:8000/api/base_query/?year=2024&months=0"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []  # Возвращаем пустой список, если API недоступен
    except Exception as e:
        print(f"Ошибка при вызове API: {e}")
        return []


table_data = fetch_api_data()

# Создание контента для карточки с таблицей
report_months = dash_table.DataTable(
    id="table-card5",
    columns=[{"name": col, "id": col} for col in table_data[0].keys()],
    data=table_data,
    style_header={"backgroundColor": COLORS["card_background"], "color": COLORS["text"]},
    style_cell={"backgroundColor": COLORS["card_background"], "color": COLORS["text"], "textAlign": "center"},
    style_table={"overflowX": "auto"},
)
