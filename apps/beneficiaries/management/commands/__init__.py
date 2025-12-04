"""
Management команды для приложения beneficiaries

Доступные команды:

1. create_beneficiaries_testdata
   Создание тестовых данных для демонстрации системы
   Использование: python manage.py create_beneficiaries_testdata

2. sync_from_recipes
   Синхронизация данных льготников из таблицы Recipe
   Использование: python manage.py sync_from_recipes [--limit N] [--dry-run]

3. update_beneficiaries_data
   Обновление и актуализация данных (статусы, истекшие назначения)
   Использование: python manage.py update_beneficiaries_data --all [--dry-run]

Подробная документация: см. README.md в этой директории
"""
