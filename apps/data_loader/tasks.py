# tasks.py
from celery import shared_task

from .handlers.oms_data import handle_oms_data

@shared_task
def process_oms_data(file_path):
    with open(file_path, 'rb') as file:
        handle_oms_data(file, None)
