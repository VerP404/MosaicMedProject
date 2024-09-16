import os

# Получение значения переменной окружения DJANGO_ENV
ENVIRONMENT = os.getenv('DJANGO_ENV', 'dev')  # Значение по умолчанию 'dev'
# Загрузка настроек в зависимости от значения переменной окружения
if ENVIRONMENT == 'prod':
    from .prod import *
elif ENVIRONMENT == 'dev':
    from .dev import *
else:
    raise ValueError(f"Unknown DJANGO_ENV value: {ENVIRONMENT}")
