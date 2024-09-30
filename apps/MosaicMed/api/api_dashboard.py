# api_dashboard.py
from apps.MosaicMed.flaskapp.flask_app import flask_app
from flask import jsonify


@flask_app.route('/api/dashboard_chef_1', methods=['GET'])
def get_dashboard_chef_1():
    data = {
        "table": [
            {"corpus": "Корпус 1", "booked_today": 25, "free_today": 10, "free_in_14_days": 5},
            {"corpus": "Корпус 2", "booked_today": 30, "free_today": 15, "free_in_14_days": 8},
            {"corpus": "ЖК", "booked_today": 20, "free_today": 5, "free_in_14_days": 2},
            {"corpus": "Итого", "booked_today": 75, "free_today": 30, "free_in_14_days": 15}
        ]
    }
    return jsonify(data)
