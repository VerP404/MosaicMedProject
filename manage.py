#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess

from threading import Thread
from config.settings import BASE_DIR


def run_dash_app():
    """Запуск Dash приложения."""
    dash_app_path = os.path.join(BASE_DIR, 'apps', 'analytical_app', 'index.py')
    dash_command = [sys.executable, dash_app_path]
    dash_process = subprocess.Popen(dash_command)
    try:
        dash_process.wait()
    except KeyboardInterrupt:
        dash_process.terminate()


def main():
    """Запуск Django приложения."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Создание потока для запуска Dash приложения
    dash_thread = Thread(target=run_dash_app)
    dash_thread.start()

    # Запуск Django приложения
    try:
        main()
    except KeyboardInterrupt:
        # Завершение процессов при прерывании
        dash_thread.join()
