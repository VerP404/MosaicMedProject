# import logging
#
# from celery import shared_task
#
# from apps.data_loader.selenium_script import run_selenium_script
#
# logger = logging.getLogger(__name__)
#
#
# @shared_task(bind=True)
# def run_selenium_task(self, username, password, start_date, end_date, start_date_treatment):
#     logger.info(f"Начало выполнения задачи {self.request.id}")
#     try:
#         success = run_selenium_script(
#             username=username,
#             password=password,
#             start_date=start_date,
#             end_date=end_date,
#             start_date_treatment=start_date_treatment
#         )
#         logger.info(f"Задача {self.request.id} завершена успешно")
#         return success
#     except Exception as e:
#         logger.error(f"Ошибка в задаче {self.request.id}: {e}")
#         raise self.retry(exc=e, countdown=60, max_retries=3)
#
